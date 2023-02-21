import logging
from collections import namedtuple
from pathlib import Path
from typing import Dict, List

import numpy as np

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
    reference_file = ReferenceLogFile(reference_file)

    # This dictionary holds the data for each
    # Star's median ADU, normalization factor and normalized ADU
    data_dict: ColorNormalizedFile.Data_Dict_Type = {
        log_file.star_number(): ColorNormalizedFile.StarData(
            log_file.median(),  # Median flux value
            np.nan,  # Normalized median
            np.nan,  # Norm factor
            color_data_file.get_star_color(log_file.star_number()),  # Star color in color ref file
            np.nan,  # Actual color value used
        )  # We'll populate values that are nan now after calculating normalization factor
        for log_file in flux_logs_files
    }

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
