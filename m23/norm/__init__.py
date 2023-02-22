import math
import os
from datetime import date
from pathlib import Path
from typing import List

import numpy as np

from m23.file import getLinesWithNumbersFromFile
from m23.file.flux_log_combined_file import FluxLogCombinedFile
from m23.file.log_file_combined_file import LogFileCombinedFile
from m23.file.normfactor_file import NormfactorFile
from m23.file.reference_log_file import ReferenceLogFile


# TODO: Mask out stars with center pixel not matching + crop the outlier stars using linfit
def normalize_log_files(
    # referenceFileName,
    reference_log_file: ReferenceLogFile,
    log_files_to_normalize: List[LogFileCombinedFile],
    output_folder : Path,
    radius: int,
    img_duration: float,
    night_date: date
):
    """
    This function normalizes the images provided.
    Note that the normalization isn't done with respect to the data in the reference image
    but with respect to some sample images take throughout the night.

    Note that this code assumes that the all stars in the log files are available in
    reference log file and no more or less.
    """

    # Wrapper around the function so we don't
    # have to keep passing the saveFolder as argument
    saveFileInFolder = lambda *args, **kwargs: saveFileInFolder(saveFolder, *args, **kwargs)

    # COLUMN_NUMBERS (0 means first column)
    ref_positions_xy = (0, 1)
    logfile_positions_xy = (0, 1)

    def aduInLogData(logData):
        return [float(line.split()[logfile_adu_column]) for line in logData]

    def starPositionsInLogData(logData):
        return [
            np.array(
                (line.split()[logfile_positions_xy[0] : logfile_positions_xy[1] + 1]),
                dtype="float",
            )
            for line in logData
        ]

    referenceData = getLinesWithNumbersFromFile(referenceFileName)
    logFilesData = [
        getLinesWithNumbersFromFile(logFileName) for logFileName in logFilesNamesToNormalize
    ]

    # At this point, if we want to look at 300-th star in our first image
    # we would do logFilesData[0][299] (beware of python index starting from 0)
    noOfFiles = len(logFilesData)

    # Normalization is done with reference to images 20%, 40%, 60% and 80% through night
    # The indices here are the index of the images from the night to which to normalize.
    # Note, we aren't normalizing with reference to the ref file
    indicesToNormalizeTo = np.linspace(0, noOfFiles, 6, dtype="int")[1:-1]
    adus_in_data_to_normalize_to = np.array(logFilesData, dtype="object")[indicesToNormalizeTo]

    # Get the ADU column in the logfiles
    adus_in_data_to_normalize_to = np.array(
        [aduInLogData(data) for data in adus_in_data_to_normalize_to]
    )

    referenceFileStarPositions = [
        np.array(line.split()[ref_positions_xy[0] : ref_positions_xy[1] + 1], dtype="float")
        for line in referenceData
    ]

    # Matrix of image by star so 4th star in 100th image will be normalized_star_data[99][3]
    normalized_star_data = np.zeros((noOfFiles, len(referenceData)))

    # Find normalization factor for each file
    all_norm_factors = []
    for file_index in range(noOfFiles):
        # Normalization factor is the median of the scaleFactors of all stars for scaleFactors < 5
        # where scaleFactor for a star for that image is the ratio of that star's adu in
        # sum of data_to_normalize_to / 4 * adu in current image

        adu_of_current_log_file = np.array(aduInLogData(logFilesData[file_index]), dtype="float")

        starPositions = starPositionsInLogData(logFilesData[file_index])

        # Mask out stars with center more than 1 pixel away from those in the ref file
        # also mask if the star is outside the 12px box around the image
        for star_index in range(len(adu_of_current_log_file)):
            starX, starY = starPositions[star_index]
            refX, refY = referenceFileStarPositions[star_index]
            if math.sqrt((refX - starX) ** 2 + (refY - starY) ** 2) > 1:
                adu_of_current_log_file[star_index] = 0

        # Find normalization factor
        scale_factors_for_stars = np.sum(adus_in_data_to_normalize_to, axis=0) / (
            4 * adu_of_current_log_file
        )
        # Only get the median value for scale factors between 0 and 5, since some values are -inf or nan
        # We get the upper threshold 5 from the IDL code
        good_scale_factors = scale_factors_for_stars[
            np.where((scale_factors_for_stars < 5) & (scale_factors_for_stars > 0))
        ]
        norm_factor = np.median(good_scale_factors) if len(good_scale_factors) else 0

        all_norm_factors.append(norm_factor)
        normalized_star_data[file_index] = norm_factor * np.array(
            aduInLogData(logFilesData[file_index])
        )

    # Save normfactors
    normfactors_file_name = NormfactorFile.generate_file_name(night_date, img_duration)
    normfactor_file = NormfactorFile(output_folder / normfactors_file_name)
    normfactor_file.create_file(all_norm_factors)

    # Save the normalized data for each star
    noOfStars = len(normalized_star_data[0])
    for star_index in range(noOfStars):

        star_data = [
            normalized_star_data[file_index][star_index] for file_index in range(noOfFiles)
        ]
        # Turn all star_data that's negative to 0
        star_data = [currentData if currentData > 0 else 0 for currentData in star_data]

        # Create flux log combined file
        flux_log_combined_file_name = FluxLogCombinedFile.generate_file_name(night_date, star_index + 1, img_duration)
        flux_log_combined_file = output_folder / flux_log_combined_file_name
        flux_log_combined_file.create_file(star_data, "", "", ("", ""), reference_log_file)