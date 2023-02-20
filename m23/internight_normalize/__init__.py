from pathlib import Path
from typing import List


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
    pass
