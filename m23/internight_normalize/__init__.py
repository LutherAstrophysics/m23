import logging
from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import norm

from m23.constants import COLOR_NORMALIZED_FOLDER_NAME, FLUX_LOGS_COMBINED_FOLDER_NAME
from m23.file.color_normalized_file import ColorNormalizedFile
from m23.file.flux_log_combined_file import FluxLogCombinedFile
from m23.file.reference_log_file import ReferenceLogFile
from m23.file.ri_color_file import RIColorFile
from m23.utils import (
    get_date_from_input_night_folder_name,
    get_log_file_name,
    get_radius_folder_name,
)


def internight_normalize(
    night: Path, reference_file: Path, color_file: Path, radii_of_extraction: List[int]
) -> None:
    """
    This function normalizes the Flux Logs Combined for a night with respect to
    the data in the reference night. It also saves the result of inter-night normalization.
    We typically the image 71 on Aug 4 2003 night as the reference.

    Note that since the a night can have Flux Logs Combined for multiple radii of extraction,
    this functions creates a color normalized output folder for as many radii of extraction
    as specified. Note that for each specified radius of extraction specified, respective
    Flux Logs Combined folder has to exist in `night` Path provided.

    param: night: Night folder that contains Flux Logs Combined folder
    param: reference_file: The path to the reference file to use.
    param: color_file: The path to the the mean R-I file to use.

    return: None

    Side effects:

    This function creates a 'Color Normalized' folder inside `night` Path and
    folders for each radius specified in radii_of_extraction inside 'Color Normalized' folder
    that contains a txt file of the inter-night normalized data for each star for that night.

    This function also logs to the default log file in `night`. See `process_nights` inside `processor`
    module for the details of the log file.


    Preconditions:
    `night` is a valid path containing Flux Logs Combined for all radius specified in `radii_of_extraction`
    `reference_file` is a valid file path in conventional reference file format
    `color_file` is a valid file path in conventional R-I color file format
    """

    for radius in radii_of_extraction:
        internight_normalize_auxiliary(night, reference_file, color_file, radius)


def internight_normalize_auxiliary(
    night: Path, reference_file: Path, color_file: Path, radius_of_extraction: List[int]
):
    """
    This is an auxiliary function for internight_normalize that's different from the
    `internight_normalize` because this function takes `radius_of_extraction` unlike
    `internight_normalize` that takes `radii_of_extraction`.

    See https://drive.google.com/file/d/1R1Xc9RhPEYXgF5jlmHvtmDqvrVWs6xfK/view?usp=sharing
    for explanation of this algorithm by Prof. Wilkerson.
    """
    # Setup logging
    night_date = get_date_from_input_night_folder_name(night)
    log_file_path = night / get_log_file_name(night_date)
    logging.basicConfig(
        filename=log_file_path,
        format="%(asctime)s %(message)s",
        level=logging.INFO,
    )

    logging.info(f"Running internight color normalization for {radius_of_extraction}")

    # Flux logs for a particular radius for that night is our primary input to this algorithm
    # We are essentially calculating median values of the flux logs combined for a star
    # and multiplying it by a normalization factor. We do this for each star.
    # How we calculate normalization factor is described later below.
    FLUX_LOGS_COMBINED_FOLDER = (
        night / FLUX_LOGS_COMBINED_FOLDER_NAME / get_radius_folder_name(radius_of_extraction)
    )
    flux_logs_files: List[FluxLogCombinedFile] = [
        FluxLogCombinedFile(file) for file in FLUX_LOGS_COMBINED_FOLDER.glob("*")
    ]
    # Filter out the files that don't match conventional flux log combined file format
    flux_logs_files = filter(lambda x: x.is_valid_file_name(), flux_logs_files)

    # We store value for each star in a named tuple

    color_data_file = RIColorFile(color_file)
    reference_file_data = ReferenceLogFile(reference_file)

    # This dictionary holds the data for each
    # Star's median ADU, normalization factor and normalized ADU
    data_dict: ColorNormalizedFile.Data_Dict_Type = {
        log_file.star_number(): ColorNormalizedFile.StarData(
            log_file.specialized_median_for_internight_normalization(),  # Median flux value
            np.nan,  # Normalized median
            np.nan,  # Norm factor
            color_data_file.get_star_color(log_file.star_number()),  # Star color in color ref file
            np.nan,  # Actual color value used
            log_file.attendance(),  # Attendance of the star for the night
            reference_file_data.get_star_adu(log_file.star_number()) or np.nan,
        )  # We'll populate values that are nan now after calculating normalization factor
        for log_file in flux_logs_files
    }

    # We calculate the ratio of signal in reference file data and the special median
    # signal for a star for the night. We do this for each stars with >50% attendance.
    stars_signal_ratio: Dict[int, float] = {}
    for star_no in range(1, 2508 + 1):  # Note +1 because of python the way range works
        star_data = data_dict[star_no]
        # Only calculate the ratio for stars with >= 50% attendance for the night
        if star_data.attendance >= 0.5:
            # Only include this star if it has a non-zero median flux
            if star_data.median_flux > 0.001:
                ratio = star_data.reference_log_adu / star_data.median_flux
                stars_signal_ratio[star_no] = ratio

    # Now we try to find correction factors (aka. normalization factor) for stars with mean r-i
    # data. How we deal with stars without mean r-i data is described later.
    # For those that have mean r-i color data,  we sort these stars into 3
    # populations based on mean r-i,as they appear different on a histogram of
    # mean r-i and graphs of mean r-i vs.  ref/night.  Potentially, they could
    # be disk stars in the luster, disk stars in the field, and bulge stars in
    # the field. That remains to be looked into. 
    # Next, we remove outliers using an initial polynomial curve fit. Then we
    # fit a final curve to each section. At the end of this program, we use the
    # curve fits to normalize these stars with color data.

    # The following dictionary holds the information for which one of the three
    # regions (described above) do stars that have mean r-i values as well as
    # are more than 50% attendant on the night fall into. So we look at the stars
    # from color dict and ensure that it's also in the dictionary
    # stars_signal_ratio)
    stars_population_number : Dict[int, int] = {} # Map from star number to population number (either 1 or 2 or 3)
    for star_no in stars_signal_ratio:
        star_color_value  = data_dict[star_no].measured_mean_r_i
        if star_color_value <= -0.0001 or star_color_value >= 0.0001:
            # Include the star if the its color value falls in a certain range
            if star_color_value > 0.135 and star_color_value <= 0.455:
                stars_population_number[star_no] = 1
            elif star_color_value > 0.455 and star_color_value <= 1.063:
                stars_population_number[star_no] = 2
            elif star_color_value > 1.063 and star_color_value <= 7:
                stars_population_number[star_no] = 3
            # Otherwise we don't include the star in the population number

    # We now remove outliers points from signal-ratio vs r-i graph.
    # Essentially, this program works by taking a 3rd degree polynomial curve
    # fit for each of the 3 intervals. Then, it calculates how far each point is
    # from its predicted point on the curve, the point - point on the curve.  It
    # bins and creates a histogram for these differences, and fits a Gaussian to
    # it (this is statistically useful in limiting the sway of outliers on the
    # mean and standard deviation). Then, any point more than 2.5 standard
    # deviations from the curve fit is removed as an outlier.

    # Here we loop over each section of the polynomial fit
    section_data = {} # This dict holds data for each section that we use outside the loop
    sections = [1, 2, 3]
    for section_number in sections:

        stars_to_include = [star_no for star_no in stars_population_number if stars_population_number[star_no] == section_number]
        x_values = [data_dict[star_no].measured_mean_r_i for star_no in stars_to_include] # Colors
        y_values = [stars_signal_ratio[star_no] for star_no in stars_to_include] # Signal ratios

        # These lines of code check to make sure the first or last data point in the signal value isn't an outlier. 
        # First or last data points tend to greatly affect the polynomial fit, so if the data points are
        # 2 standard deviations away from the next closest point, they are replaced with the mean of the 
        # next two closest points.
        modified_y_value = [y for y in y_values] # Note that we don't want to alter the original y_values list
        std_signals = np.std(y_values)
        if abs(y_values[0] - y_values[1])/std_signals > 2:
            modified_y_value[0] = np.mean(modified_y_value[1:3])
        if abs(y_values[-1] - y_values[-2])/std_signals > 2:
            modified_y_value[-1] = np.mean(modified_y_value[-4:-2])

        coeffs = np.polyfit(x_values, y_values, 3) # Third degree fit
        polynomial_fit_fn = lambda x : coeffs[0] * x ** 3 + coeffs[1] * x ** 2 + coeffs[2] * x + coeffs[3] # ax^3 + bx^2 + cx + d

        # This list stores the difference between actual signal value and the value given by fitted curve 
        y_differences = [y_values[index] - polynomial_fit_fn[x] for index, x in enumerate(x_values)]

        # We store the data of each section to later in a dictionary indexed by the section number
        section_data[section_number] = {
            'stars_to_include': stars_to_include,
            'x_values': x_values,
            'y_values': y_values,
            'y_differences': y_differences # This is the difference of actual y to fitted y
        }


    y_differences = [ ]  # This holds the y_differences for three sections calculated in the loop above
    for section_number in sections:
        y_differences += section_data[section_number]['y_differences']

    y_diff_std = np.std(y_differences)
    y_diff_min = np.min(y_differences) - 5 * y_diff_std
    y_diff_max = np.max(y_differences) - 5 * y_diff_std
    y_no_of_bins = 11 # We want to use 11 bins
    bin_frequencies, bins = np.histogram(y_differences, range=[y_diff_min, y_diff_max], bins=y_no_of_bins)
    mean, sigma = norm.fit(np.repeat(bins, bin_frequencies))

    # Now we find stars for which y_difference is more than 2std away from mean
    top_threshold = mean + 2 * sigma
    bottom_threshold = mean - 2 * sigma

    # We now create a list of stars that are outside the specified threshold
    stars_outside_threshold = []
    for section_number in sections:
        section_y_differences = section_data[section_number]['y_differences']
        section_stars = section_data[section_number]['stars_to_include']
        for index, y_diff in enumerate(section_y_differences):
            if y_diff < bottom_threshold or y_diff > top_threshold:
                star_no = section_stars[index]
                stars_outside_threshold.append(star_no)

    stars_fitted_signal_ratios = {} # This dictionary holds the fitted signal ratios for the stars
    # Now we do a second degree polynomial fit for the stars in sections that aren't in `stars_outside_threshold`
    # Note that we have to fit individual curves for each section like we did above
    for section_number in sections:

        # Note that we're excluding stars in `stars_outside_threshold` list
        stars_to_include = [star_no for star_no in stars_population_number if stars_population_number[star_no] == section_number and star_no not in stars_outside_threshold]
        x_values = [data_dict[star_no].measured_mean_r_i for star_no in stars_to_include] # Colors
        y_values = [stars_signal_ratio[star_no] for star_no in stars_to_include] # Signal ratios

        # These lines of code check to make sure the first or last data point in the signal value isn't an outlier. 
        # First or last data points tend to greatly affect the polynomial fit, so if the data points are
        # 2 standard deviations away from the next closest point, they are replaced with the mean of the 
        # next two closest points.
        modified_y_value = [y for y in y_values] # Note that we don't want to alter the original y_values list
        std_signals = np.std(y_values)
        if abs(y_values[0] - y_values[1])/std_signals > 2:
            modified_y_value[0] = np.mean(modified_y_value[1:3])
        if abs(y_values[-1] - y_values[-2])/std_signals > 2:
            modified_y_value[-1] = np.mean(modified_y_value[-4:-2])

        coeffs = np.polyfit(x_values, y_values, 2) # Second degree fit
        polynomial_fit_fn = lambda x : coeffs[0] * x ** 2 + coeffs[1] * x  + coeffs[2] # ax^2 + bx + c

        for index, star in enumerate(stars_to_include):
            x_value = x_values[index]
            fitted_y_value = polynomial_fit_fn[x_value] # This is the normfactor for the star
            stars_fitted_signal_ratios[star] = fitted_y_value
            data_dict[star].norm_factor = fitted_y_value # Set the normfactor 
            data_dict[star].normalized_median_flux = data_dict[star].median_flux * fitted_y_value 

    # At this point we've completed calculating normfactors for stars with good color data (i.e. R-I data)
    # For other stars we do the following:


    # # We now make a plot of the ratio (calculated) vs R-I for the particular star
    # values_to_plot = [
    #     (
    #         color_data_file.get_star_color(star_no),  # X value is the R-I value for a star
    #         stars_signal_ratio[star_no],  # Y Value is the star signal ratio calculated above
    #     )
    #     for star_no in stars_signal_ratio
    # ]
    # x, y = zip(*values_to_plot)  # Unpack a list of pairs into two tuples
    # plt.plot(x, y, "b+")
    # plt.xlabel("R-I")
    # plt.ylabel("Signal ratio")
    # plt.show()

    # Now we calculate normalization factor for the star for the night

    # Save data
    OUTPUT_FOLDER = (
        night / COLOR_NORMALIZED_FOLDER_NAME / get_radius_folder_name(radius_of_extraction)
    )
    output_file = OUTPUT_FOLDER / ColorNormalizedFile.get_file_name(
        night_date, radius_of_extraction
    )
    ColorNormalizedFile(output_file.absolute()).save_data(data_dict, night_date)

    # output_file = OUTPUT_FOLDER
    logging.info(f"Completed internight color normalization for {radius_of_extraction}")
