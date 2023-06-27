import logging
import traceback
from pathlib import Path
from typing import Callable, Dict, List, TypedDict

import numpy as np
from scipy.optimize import curve_fit

from m23.charts import draw_internight_brightness_chart, draw_internight_color_chart
from m23.constants import COLOR_NORMALIZED_FOLDER_NAME, FLUX_LOGS_COMBINED_FOLDER_NAME
from m23.exceptions import InternightException
from m23.file.color_normalized_file import ColorNormalizedFile
from m23.file.flux_log_combined_file import FluxLogCombinedFile
from m23.file.log_file_combined_file import LogFileCombinedFile
from m23.file.ri_color_file import RIColorFile
from m23.utils import (
    customMedian,
    get_date_from_input_night_folder_name,
    get_radius_folder_name,
)
from m23.utils.flux_to_magnitude import flux_to_magnitude

# Note that this code is implemented based on the internight normalization in IDL
# https://github.com/LutherAstrophysics/idl-files/blob/39dfa1c0c6d03d64020c42583bbcaa94655d69cc/inter_night_normalization_345.pro


class ConfigImage(TypedDict):
    rows: int


def internight_normalize(
    night: Path,
    logfile_combined_reference_file: LogFileCombinedFile,
    color_file: Path,
    radii_of_extraction: List[int],
) -> Dict[int, Dict[str, Dict[int, float]]]:
    """
    This function normalizes the Flux Logs Combined for a night with respect to
    the data in the reference night. It also saves the result of inter-night
    normalization.  We typically the image 71 on Aug 4 2003 night as the
    reference.

    Note that since the a night can have Flux Logs Combined for multiple radii
    of extraction, this functions creates a color normalized output folder for
    as many radii of extraction as specified. Note that for each specified
    radius of extraction specified, respective Flux Logs Combined folder has to
    exist in `night` Path provided.

    param: night: Night folder that contains Flux Logs Combined folder param:
    reference_file: The path to the reference file to use.  param: color_file:
    The path to the the mean R-I file to use.

    return: None

    Side effects:

    This function creates a 'Color Normalized' folder inside `night` Path and
    folders for each radius specified in radii_of_extraction inside 'Color
    Normalized' folder that contains a txt file of the inter-night normalized
    data for each star for that night.

    This function also logs to the default log file in `night`. See
    `process_nights` inside `processor` module for the details of the log file.


    Preconditions:
    `night` is a valid path containing Flux Logs Combined for all radius
    specified in `radii_of_extraction`

    `reference_file` is a valid file path in conventional reference file format

    `color_file` is a valid file path in conventional R-I color file format
    """
    normfactors = {}
    for radius in radii_of_extraction:
        normfactors[radius] = internight_normalize_auxiliary(
            night, logfile_combined_reference_file, color_file, radius
        )
    return normfactors


def internight_normalize_auxiliary(  # noqa
    night: Path,
    logfile_combined_reference_file: LogFileCombinedFile,
    color_file: Path,
    radius_of_extraction: int,
) -> Dict[str, Dict[int, float]]:
    """
    This is an auxiliary function for internight_normalize that's different from
    the `internight_normalize` because this function takes
    `radius_of_extraction` unlike `internight_normalize` that takes
    `radii_of_extraction`.

    See https://drive.google.com/file/d/1R1Xc9RhPEYXgF5jlmHvtmDqvrVWs6xfK/view?usp=sharing
    for explanation of this algorithm by Prof. Wilkerson.
    """
    # Setup logging
    night_date = get_date_from_input_night_folder_name(night)
    logger = logging.getLogger("LOGGER_" + str(night_date))
    logger.info(f"Running internight color normalization for {radius_of_extraction}px")

    # Flux logs for a particular radius for that night is our primary input to
    # this algorithm We are essentially calculating median values of the flux
    # logs combined for a star and multiplying it by a normalization factor. We
    # do this for each star.  How we calculate normalization factor is described
    # later below.
    FLUX_LOGS_COMBINED_FOLDER = (
        night / FLUX_LOGS_COMBINED_FOLDER_NAME / get_radius_folder_name(radius_of_extraction)
    )
    flux_logs_files: List[FluxLogCombinedFile] = [
        FluxLogCombinedFile(file) for file in FLUX_LOGS_COMBINED_FOLDER.glob("*")
    ]
    # Filter out the files that don't match conventional flux log combined file format
    flux_logs_files = list(filter(lambda x: x.is_valid_file_name(), flux_logs_files))

    color_data_file = RIColorFile(color_file)

    # Messy hackery used instead of just reading the attendance float value
    # to mimick IDL
    is_star_attendance_over_half: Dict[int, bool] = {}

    data_dict: ColorNormalizedFile.Data_Dict_Type = {}

    for log_file in flux_logs_files:
        # This dictionary holds the data for each
        # Star's median ADU, normalization factor and normalized ADU
        star_number = log_file.star_number()
        data_dict[star_number] = ColorNormalizedFile.StarData(
            # Median flux value
            log_file.specialized_median_for_internight_normalization(),
            np.nan,  # Normalized median
            np.nan,  # Norm factor
            # Star color in color ref file
            color_data_file.get_star_color(star_number),
            np.nan,  # Actual color value used
            log_file.attendance(),  # Attendance of the star for the night
            logfile_combined_reference_file.get_star_data(star_number).radii_adu[
                radius_of_extraction
            ]
            or np.nan,
        )
        is_star_attendance_over_half[star_number] = log_file.is_attendance_over_half()

    last_star_no = 2510

    # We calculate the ratio of signal in reference file data and the special
    # median signal for a star for the night. We do this for each stars with
    # >50% attendance.
    stars_signal_ratio: Dict[int, float] = {}
    # Note +1 because of python the way range works
    for star_no in range(1, last_star_no + 1):
        star_data = data_dict[star_no]
        # Only calculate the ratio for stars with >= 50% attendance for the night
        if is_star_attendance_over_half[star_no] and not np.isnan(star_data.median_flux):
            # if star_data.attendance >= 0.5:
            # Only include this star if it has a non-zero median flux
            ratio = star_data.reference_log_adu / star_data.median_flux
            stars_signal_ratio[star_no] = ratio

    all_ref_night = []
    for star in range(1, last_star_no + 1):
        all_ref_night.append(stars_signal_ratio.get(star, 0))

    # Now we try to find correction factors (aka. normalization factor) for
    # stars with mean r-i data. How we deal with stars without mean r-i data is
    # described later.  For those that have mean r-i color data,  we sort these
    # stars into 3 populations based on mean r-i,as they appear different on a
    # histogram of mean r-i and graphs of mean r-i vs.  ref/night.  Potentially,
    # they could be disk stars in the luster, disk stars in the field, and bulge
    # stars in the field. That remains to be looked into.  Next, we remove
    # outliers using an initial polynomial curve fit. Then we fit a final curve
    # to each section. At the end of this program, we use the curve fits to
    # normalize these stars with color data.

    # The following dictionary holds the information for which one of the three
    # regions (described above) do stars that have mean r-i values as well as
    # are more than 50% attendant on the night fall into. So we look at the
    # stars from color dict and ensure that it's also in the dictionary
    # stars_signal_ratio)

    # Map from star number to color_section number (either 1 or 2 or 3)
    stars_color_section_number: Dict[int, int] = {}
    for star_no in range(1, last_star_no + 1):
        star_color_value = data_dict[star_no].measured_mean_r_i
        if star_color_value > 0.135 and star_color_value <= 0.455:
            stars_color_section_number[star_no] = 1
        elif star_color_value > 0.455 and star_color_value <= 1.063:
            stars_color_section_number[star_no] = 2
        elif star_color_value > 1.063 and star_color_value <= 7:
            stars_color_section_number[star_no] = 3

    # Otherwise we don't include the star in the color_section number
    # We now remove outliers points from signal-ratio vs r-i graph.
    # Essentially, this program works by taking a 3rd degree polynomial curve
    # fit for each of the 3 intervals. Then, it calculates how far each point is
    # from its predicted point on the curve, the point - point on the curve.  It
    # bins and creates a histogram for these differences, and fits a Gaussian to
    # it (this is statistically useful in limiting the sway of outliers on the
    # mean and standard deviation). Then, any point more than 2.5 standard
    # deviations from the curve fit is removed as an outlier.

    # Here we loop over each section of the polynomial fit
    # This dict holds data for each section that we use outside the loop
    section_data = {}
    sections = [1, 2, 3]
    for section_number in sections:
        stars_to_include = []
        for star_no in stars_color_section_number:
            if (
                stars_color_section_number[star_no] == section_number
                and star_no in stars_signal_ratio
            ):
                stars_to_include.append(star_no)

        # Colors
        x_values = [data_dict[star_no].measured_mean_r_i for star_no in stars_to_include]
        # Signal ratios
        y_values = [stars_signal_ratio[star_no] for star_no in stars_to_include]

        # Sort by x
        x_sort_indices = np.argsort(x_values)
        x_values = np.array(x_values)[x_sort_indices]
        y_values = np.array(y_values)[x_sort_indices]
        stars_to_include = np.array(stars_to_include)[x_sort_indices]

        # These lines of code check to make sure the first or last data point in
        # the signal value isn't an outlier.  First or last data points tend to
        # greatly affect the polynomial fit, so if the data points are 2
        # standard deviations away from the next closest point, they are
        # replaced with the mean of the next two closest points.
        std_signals = np.std(y_values, ddof=1)
        beginning_diff = abs(y_values[0] - y_values[1]) / std_signals
        ending_diff = abs(y_values[-1] - y_values[-2]) / std_signals
        if beginning_diff > 2 or ending_diff > 2:
            modified_y_value = y_values.copy()  # Note making copy is important
            if beginning_diff > 2:
                # Note python slicing excludes last element, IDL's includes
                modified_y_value[0] = np.mean(modified_y_value[1:4])
            if ending_diff > 2:
                # Note python slicing excludes last element, IDL's includes
                modified_y_value[-1] = np.mean(modified_y_value[-4:-1])
            a, b, c, d = np.polyfit(x_values, modified_y_value, 3)  # Degree 3

            # ax^3 + bx^2 + cx + d
            def polynomial_fit_fn(x):
                return a * x**3 + b * x**2 + c * x + d

        else:
            a, b, c, d = np.polyfit(x_values, y_values, 3)  # Degree 3

            # ax^3 + bx^2 + cx + d
            def polynomial_fit_fn(x):
                return a * x**3 + b * x**2 + c * x + d

        # This list stores the difference between actual signal value and the
        # value given by fitted curve
        y_differences = [
            polynomial_fit_fn(x) - y_values[index] for index, x in enumerate(x_values)
        ]

        # We store the data of each section to later in a dictionary indexed by
        # the section number
        section_data[section_number] = {
            "stars_to_include": stars_to_include,
            "x_values": x_values,
            "y_values": y_values,
            # This is the difference of actual y to fitted y
            "y_differences": y_differences,
        }

    # This holds the y_differences for three sections calculated in the loop above
    y_differences = []
    for section_number in sections:
        y_differences += section_data[section_number]["y_differences"]

    y_diff_std = np.std(y_differences, ddof=1)
    y_diff_mean = np.mean(y_differences)
    y_diff_min = y_diff_mean - 5 * y_diff_std
    y_diff_max = y_diff_mean + 5 * y_diff_std
    y_no_of_bins = 10  # We want to use 10 bins, like IDL code
    try:
        bin_frequencies, bins_edges = np.histogram(
            y_differences, range=[y_diff_min, y_diff_max], bins=y_no_of_bins
        )
    except ValueError:
        tb = traceback.format_exc()
        logger.error("Internight norm encountered exception in making histogram of residuals")
        logger.debug(tb)
        raise InternightException

    bins_mid_values = []
    for index, current_value in enumerate(bins_edges[:-1]):
        next_value = bins_edges[index + 1]
        bins_mid_values.append((current_value + next_value) / 2)
    fit_coefficients, _ = curve_fit(
        n_term_3_gauss_fit, bins_mid_values, bin_frequencies, maxfev=5000
    )
    mean, sigma = fit_coefficients[1], fit_coefficients[2]
    sigma = abs(sigma)  # Important since sigma given by our curve fit could be negative

    # Now we find stars for which y_difference is more than 2std away from mean
    stars_outside_threshold = []
    top_threshold = mean + 2.5 * sigma
    bottom_threshold = mean - 2.5 * sigma
    # We now create a list of stars that are outside the specified threshold
    for section_number in sections:
        section_y_differences = section_data[section_number]["y_differences"]
        section_stars = section_data[section_number]["stars_to_include"]
        for index, y_diff in enumerate(section_y_differences):
            if y_diff < bottom_threshold or y_diff > top_threshold:
                if sigma != 0:  # Guard for when fit fails and sigma is 0
                    star_no = section_stars[index]
                    stars_outside_threshold.append(star_no)

    # Now we do a second degree polynomial fit for the stars in sections that
    # aren't in `stars_outside_threshold` Note that we have to fit individual
    # curves for each section like we did above
    color_fit_functions = {}  # Stores the color fit function for each section
    # We save the x and the y so we can use this to make chart later
    section_x_values = {}
    section_y_values = {}
    for section_number in sections:
        # Note that we're excluding stars in `stars_outside_threshold` list
        stars_in_section = section_data[section_number]["stars_to_include"]
        stars_to_include = [
            star_no for star_no in stars_in_section if star_no not in stars_outside_threshold
        ]
        x_values = [data_dict[star_no].measured_mean_r_i for star_no in stars_to_include]  # Colors
        y_values = [stars_signal_ratio[star_no] for star_no in stars_to_include]  # Signal ratios
        section_x_values[section_number] = x_values
        section_y_values[section_number] = y_values

        a, b, c = np.polyfit(x_values, y_values, 2)  # Second degree fit
        # Nested lambda necessary to create a, b, c as local variables
        polynomial_fit_fn = (lambda a, b, c: lambda x: a * x**2 + b * x + c)(
            a, b, c
        )  # ax^2 + bx + c
        color_fit_functions[section_number] = polynomial_fit_fn

    normfactors_to_return = {}

    # Create and save the color chart
    normfactors_to_return["color"] = draw_internight_color_chart(
        night,
        radius_of_extraction,
        section_x_values,
        section_y_values,
        color_fit_functions,
    )

    stars_magnitudes = {
        star: flux_to_magnitude(data_dict[star].median_flux, radius_of_extraction)
        for star in range(1, last_star_no + 1)
    }
    star_magnitudes_section = {}  # Map from star no to star section no
    for star, star_magnitude in stars_magnitudes.items():
        if star_magnitude < 11:
            star_magnitudes_section[star] = 1
        elif 11 <= star_magnitude < 12.5:
            star_magnitudes_section[star] = 2
        else:
            star_magnitudes_section[star] = 3

    # These regions are divided based on stars magnitudes for
    # stars that have valid magnitude (& attendance)
    region_1_stars, region_2_stars, region_3_stars = [], [], []
    for star in stars_signal_ratio:
        star_magnitude = stars_magnitudes[star]
        if star_magnitude < 11:
            region_1_stars.append(star)
        elif 11 <= star_magnitude < 12.5:
            region_2_stars.append(star)
        else:
            region_3_stars.append(star)

    # FROM IDL version of this code "by looking at the graphs for multiple
    # nights, and fitted each regions differently...", we will use their fits
    magnitude_fit_fn = {}

    # Region 1
    # Magnitudes
    region_1_x = [stars_magnitudes[star] for star in region_1_stars]
    # Signal Ratio
    region_1_y = [stars_signal_ratio[star] for star in region_1_stars]
    coeffs_1 = np.polyfit(region_1_x, region_1_y, 1)  # Linear fit
    # ax + b
    magnitude_fit_fn[1] = lambda x: coeffs_1[0] * x + coeffs_1[1]

    # Region 2
    # Magnitudes
    region_2_x = [stars_magnitudes[star] for star in region_2_stars]
    # Signal Ratio
    region_2_y = [stars_signal_ratio[star] for star in region_2_stars]
    coeffs_2 = np.polyfit(region_2_x, region_2_y, 2)  # 2nd degree fit
    magnitude_fit_fn[2] = lambda x: (
        coeffs_2[0] * x**2 + coeffs_2[1] * x + coeffs_2[2]
    )  # ax^2 + bx + c

    # Region 3
    # Signal ratios
    region_3_x = [stars_magnitudes[star] for star in region_3_stars]
    region_3_y = [stars_signal_ratio[star] for star in region_3_stars]
    # For region 3, we just return the median of y values

    # magnitude_fit_fn[3] = lambda x: np.median(region_3_y)
    # We're using IDL like median here for getting results close to IDL's,
    # but np.median is better
    magnitude_fit_fn[3] = lambda x: customMedian(region_3_y)

    # Create and save the brightness chart
    normfactors_to_return["brightness"] = draw_internight_brightness_chart(
        night,
        radius_of_extraction,
        {1: region_1_x, 2: region_2_x, 3: region_3_x},
        {1: region_1_y, 2: region_2_y, 3: region_3_y},
        magnitude_fit_fn,
    )

    # Write normfactors for all stars
    for star_no in sorted(data_dict.keys()):
        star_data = data_dict[star_no]
        color = star_data.measured_mean_r_i
        norm_factor = None

        if 0.135 <= color < 7:
            color_section_number = stars_color_section_number[star_no]
            norm_factor = color_fit_functions[color_section_number](star_data.measured_mean_r_i)

        # Now for the stars that didn't have good R-I values which is (< 0.135
        # or >= 7) we calculate the normfactors based on the brightness fit
        else:
            # If the star is a known LPV that doesn't have a color, we calculate
            # the normfactor for it by providing a custom calculated color value
            special_star_value = get_normfactor_for_special_star(star_no, color_fit_functions[3])

            if special_star_value:
                # Note we're mutating color variable here
                norm_factor, color = special_star_value
            else:
                magnitude = stars_magnitudes[star_no]
                magnitude_section_no = star_magnitudes_section[star_no]
                norm_factor = magnitude_fit_fn[magnitude_section_no](magnitude)

        # Save the normfactor the star only if we have the normfactor for it

        if star_data.attendance < 0.5 or not star_data.median_flux > 0.001:
            normalized_median_flux = 0
        else:
            normalized_median_flux = norm_factor * star_data.median_flux
        # Replace is used because mutating a namedtuple directly isn't allowed
        data_dict[star_no] = star_data._replace(
            norm_factor=norm_factor,
            normalized_median_flux=normalized_median_flux,
            used_mean_r_i=color,
        )

    # Save data
    OUTPUT_FOLDER = (
        night / COLOR_NORMALIZED_FOLDER_NAME / get_radius_folder_name(radius_of_extraction)
    )
    output_file = OUTPUT_FOLDER / ColorNormalizedFile.get_file_name(
        night_date, radius_of_extraction
    )
    ColorNormalizedFile(output_file.absolute()).save_data(data_dict, night_date)

    # output_file = OUTPUT_FOLDER
    logger.info(f"Completed internight color normalization for {radius_of_extraction}px")
    return normfactors_to_return


def get_normfactor_for_special_star(
    star_no: int, fit_fn: Callable[[float], float]
) -> float | None:
    """
    For each of the special LPV stars that don't have a color value we calculate
    the normfactor by providing color values manually. For how we got these
    color values ask Prof. Wilkerson. Note that in the IDL code that this was
    implemented in python from the fit_fn was the polynomial fit function from
    the first region of the Signal Ratio vs Color fit. Note **not** brightness
    fit

    param: star_no : Star number
    param: fit_fn: a fit function that takes color values and returns the the
            fitted y

    return : The a tuple of normfactor for the star if the star is one of the
            special stars and the color value used Returns none if the star isn't a
            special star
    """
    stars_to_color_values = {
        814: 2.6137,
        1223: 3.6242,
        1654: 2.8866,
        1702: 2.9175,
        1716: 2.6137,
        1843: 2.7849,
        2437: 2.5545,
        2509: 2.7816,
        2510: 3.0923,
    }
    if star_no in stars_to_color_values:
        color = stars_to_color_values[star_no]
        return fit_fn(color), color


def n_term_3_gauss_fit(
    x,
    a0,
    a1,
    a2,
):
    z = (x - a1) / a2
    y = a0 * np.exp(-(z**2) / 2)
    return y
