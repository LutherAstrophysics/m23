import logging
import math
from datetime import date
from pathlib import Path
from typing import Iterable, List, Tuple, TypedDict

import numpy as np
from typing_extensions import NotRequired

from m23.constants import INTRA_NIGHT_IMPACT_THRESHOLD_PIXELS
from m23.file.flux_log_combined_file import FluxLogCombinedFile
from m23.file.log_file_combined_file import LogFileCombinedFile
from m23.file.normfactor_file import NormfactorFile
from m23.file.reference_log_file import ReferenceLogFile
from m23.utils import half_round_up_to_int

from .get_line import get_star_to_ignore_bit_vector


class NormalizationTechniques:
    # Normalization linear means that we normalize with respect to 20% 40% 60%
    # and 80% image of the night
    LINEAR = "LINEAR"
    # Elevation means that we normalize to some images (1-4) from within a night
    # that have the same cluster angle (within 1 degree)
    ELEVATION = "ELEVATION"


class IntranightNormalizationResult(TypedDict):
    normfactors: Iterable[float]
    normalized_cluster_angle: NotRequired[float]


def normalize_log_files(  # noqa
    reference_log_file: ReferenceLogFile,
    log_files_to_normalize: List[LogFileCombinedFile],
    output_folder: Path,
    radius: int,
    img_duration: float,
    night_date: date,
) -> IntranightNormalizationResult:
    """
    This function normalizes (intra night *not* inter night) the
    LogFilesCombined files provided.  Note that the normalization **isn't** done
    with respect to the data in the reference image but with respect to some
    sample images take throughout the night.

    Note that this code assumes that the all stars in the log files are
    available in reference log file and no more or less.

    @return: iterable of normfactors for the images
    """

    # We are sorting the log files so that we know what's the first logfile
    # we are using and what's the last. This data is needed written in header
    # of all flux log combined files that we create
    logger = logging.getLogger("LOGGER_" + str(night_date))

    log_files_to_normalize.sort(key=lambda log_file: log_file.img_number())
    no_of_files = len(log_files_to_normalize)

    indices_to_normalize_to = get_indices_to_normalize_to(
        log_files_to_normalize, NormalizationTechniques.ELEVATION, night_date
    )
    log_file_names = list(map(lambda x: x.path().name, log_files_to_normalize))
    log_files_to_normalize_to_str = np.array(log_file_names).take(indices_to_normalize_to)
    logger.info(f"Logfiles to normalize wit respect to {log_files_to_normalize_to_str}")

    array_of_logfiles_of_array_of_adus = []  # This is an array of arrays

    # This holds the normalization factor for each log_file to use
    all_norm_factors = []

    for file_index, log_file in enumerate(log_files_to_normalize):
        adu_of_current_log_file = log_files_to_normalize[file_index].get_adu(radius)

        # Perform linear fits, cropping in 12 pixels from stars closest to the
        # four corners creating a quadrilateral region, and excluding stars
        # outside of this area
        stars_to_ignore_bit_vector = get_star_to_ignore_bit_vector(log_file, radius)

        # Mask out stars with center more than 1 pixel away from those in the
        # ref file also mask if the star is outside the 12px box around the
        # image
        for star_index in range(len(log_file)):
            # Note not to be confused between logfile and reference file here we
            # call logfile combined that's to be normalized as logfile and the
            # reference file that we use to look up the standard positions of
            # star as reference file
            star_no = star_index + 1

            # Mark the adu of the star as 0 if that's to be ignored
            if stars_to_ignore_bit_vector[star_index] == 0:
                adu_of_current_log_file[star_index] = 0
                # We go to the next star in the for loop as we already know ADU
                # for this star for this image
                continue

            star_data_in_log_file = log_file.get_star_data(star_no)
            if (
                not all([x > 0 for x in star_data_in_log_file.radii_adu.values()])
                or star_data_in_log_file.sky_adu <= 0
            ):
                adu_of_current_log_file[
                    star_index
                ] = 0  # Ignore this star for normfactor calc of this logfile
                continue

            star_x_reffile, star_y_reffile = reference_log_file.get_star_xy(star_no)
            star_x_position, star_y_position = (
                star_data_in_log_file.x,
                star_data_in_log_file.y,
            )

            if (
                math.sqrt(
                    (star_x_reffile - star_x_position) ** 2
                    + (star_y_reffile - star_y_position) ** 2
                )
                > INTRA_NIGHT_IMPACT_THRESHOLD_PIXELS
            ):
                adu_of_current_log_file[star_index] = 0

        array_of_logfiles_of_array_of_adus.append(adu_of_current_log_file)

    # Now for each log file we calculate its normfactor For each logfile, its
    # normfactor is the median of normfactors of the stars in that image.  For a
    # star, its normfactor in a logfile is sum of adus in reference log files
    # divided by 4 * its adu. Note that reference log files mean the 4 sample
    # log files taken from within the night.
    reference_log_files = []
    for index, log_file in enumerate(array_of_logfiles_of_array_of_adus):
        if index in indices_to_normalize_to:
            reference_log_files.append(log_file)

    array_of_logfiles_of_array_of_adus = np.array(
        array_of_logfiles_of_array_of_adus
    )  # Convert to numpy array
    reference_log_files = np.array(reference_log_files)  # Convert to numpy array
    for file_index, log_file in enumerate(array_of_logfiles_of_array_of_adus):
        no_of_stars = len(log_file)
        norm_factor_for_stars = []
        for star_index in range(no_of_stars):
            star_adu_in_reference_log_files = []
            for ref_log_file in reference_log_files:
                star_adu_in_reference_log_files.append(ref_log_file[star_index])
            star_adu = log_file[star_index]
            if all([value > 0 for value in star_adu_in_reference_log_files]) and star_adu > 0:
                normfactor = sum(star_adu_in_reference_log_files) / (
                    len(indices_to_normalize_to) * star_adu
                )
            else:
                normfactor = 0
            norm_factor_for_stars.append(normfactor)
        good_scale_factors = [x for x in norm_factor_for_stars if 0 < x <= 5]
        norm_factor_for_logfile = np.median(good_scale_factors)
        all_norm_factors.append(norm_factor_for_logfile)
        array_of_logfiles_of_array_of_adus[file_index] = (
            norm_factor_for_logfile * array_of_logfiles_of_array_of_adus[file_index]
        )

    # Save normfactors
    normfactors_file_name = NormfactorFile.generate_file_name(night_date, img_duration)
    normfactor_file = NormfactorFile(output_folder / normfactors_file_name)
    normfactor_file.create_file(all_norm_factors)

    # Save the normalized data for each star
    noOfStars = len(array_of_logfiles_of_array_of_adus[0])
    for star_index in range(noOfStars):
        star_no = star_index + 1
        star_adu_data = [
            array_of_logfiles_of_array_of_adus[file_index][star_index]
            for file_index in range(no_of_files)
        ]
        # Turn all star_adu_data that's negative to 0
        star_adu_data = [current_data if current_data > 0 else 0 for current_data in star_adu_data]

        # We now create flux log combined file
        flux_log_combined_file_name = FluxLogCombinedFile.generate_file_name(
            night_date, star_no, img_duration
        )
        flux_log_combined_file = FluxLogCombinedFile(output_folder / flux_log_combined_file_name)

        fist_log_file_number = log_files_to_normalize[0].img_number()
        last_log_file_number = log_files_to_normalize[-1].img_number()

        x_positions = []
        y_positions = []
        date_times = []

        for lf in log_files_to_normalize:
            star_data = lf.get_star_data(star_no)
            x_positions.append(star_data.x)
            y_positions.append(star_data.y)
            date_times.append(lf.datetime())

        flux_log_combined_file.create_file(
            star_adu_data,
            fist_log_file_number,
            last_log_file_number,
            x_positions,
            y_positions,
            all_norm_factors,
            date_times,
            reference_log_file,
        )

    return {
        "normfactors": all_norm_factors,
        "normalized_cluster_angle": get_cluster_angle_to_normalize_by_log_files(
            log_files_to_normalize
        ),
    }


def get_cluster_angle_to_normalize_by_log_files(log_files) -> float:
    angles_and_file_numbers = []
    for logfile in log_files:
        angles_and_file_numbers.append((logfile.get_cluster_angle(), logfile.img_number()))
    angle = get_cluster_angle_to_normalize_to(angles_and_file_numbers)
    return angle


def get_indices_to_normalize_to(log_files, technique, night_date):
    logger = logging.getLogger("LOGGER_" + str(night_date))
    if technique == NormalizationTechniques.LINEAR:
        # Normalization is done with reference to images 20%, 40%, 60% and 80%
        # throughout night The indices here are the index of the images from the
        # night to which to normalize.
        return np.linspace(0, len(log_files), 6, dtype="int")[1:-1]
    elif technique == NormalizationTechniques.ELEVATION:
        angle = get_cluster_angle_to_normalize_by_log_files(log_files)
        logger.info(f"Cluster angle to normalized to {angle}")
        indices = []
        for index, logfile in enumerate(log_files):
            if half_round_up_to_int(logfile.get_cluster_angle()) == angle:
                indices.append(index)
        if len(indices) < 4:
            return indices
        else:
            indices_of_indices = np.linspace(0, len(indices), 6, dtype="int")[1:-1]
            return np.array(indices).take(indices_of_indices)
    else:
        raise Exception(f"Intranight {technique} not recognized")


def get_cluster_angle_to_normalize_to(
    angles_and_file_number_exact: Iterable[Tuple[float, int]]
) -> int:
    """
    @param: angles_and_file_number: An iterable of tuple of angle and image number
    @returns: cluster angle to normalize to

    Note that we want to choose a cluster angle that's present the most in the
    night.  If there are more than one angles, we choose the one that spread out
    as far as possible into the night. If there's are more than one contenders
    present, we choose the one that's closest to the middle of the night.
    """

    # Rounded version
    angles_and_file_number = list(
        map(lambda x: (half_round_up_to_int(x[0]), x[1]), angles_and_file_number_exact)
    )

    angles, file_numbers = zip(*angles_and_file_number)

    file_numbers = sorted(file_numbers)
    first_file_number = file_numbers[0]
    last_file_number = file_numbers[-1]

    # Create a dictionary that holds count of each angle
    angles_count_dict = {angle: 0 for angle in set(angles)}
    for angle in angles:
        angles_count_dict[angle] += 1

    angles_count_sorted = sorted(angles_count_dict.items(), key=lambda x: x[1], reverse=True)
    max_count = angles_count_sorted[0][1]

    # Angles have have max count (there could be multiple) are stored as candidates
    candidates_angles = list(
        map(lambda x: x[0], (filter(lambda x: x[1] == max_count, angles_count_sorted)))
    )

    if len(candidates_angles) == 1:
        return candidates_angles[0]

    # Find a candidate that has the most spread
    candidates_spread = {}
    candidates_first_file_number = {}
    for candidate in candidates_angles:
        by_candidate = sorted(
            filter(lambda x: x[0] == candidate, angles_and_file_number), key=lambda x: x[1]
        )
        first_file_by_candidate = by_candidate[0][1]
        candidates_first_file_number[candidate] = first_file_by_candidate
        last_file_by_candidate = by_candidate[-1][1]
        candidates_spread[candidate] = last_file_by_candidate - first_file_by_candidate

    # Find the candidate with most spread
    candidates_spread_sorted = sorted(candidates_spread.items(), key=lambda x: x[1], reverse=True)
    max_spread = candidates_spread_sorted[0][1]

    candidates_with_max_spread = list(
        map(lambda x: x[0], filter(lambda x: x[1] == max_spread, candidates_spread_sorted))
    )

    if len(candidates_with_max_spread) == 1:
        return candidates_with_max_spread[0]

    # Return the candidate whose first image is the closest to the middle of the night
    return sorted(
        candidates_with_max_spread,
        key=lambda x: abs(
            0.5 - (candidates_first_file_number[x] / (last_file_number - first_file_number))
        ),
    )[0]
