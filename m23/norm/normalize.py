import math
import os
from datetime import date
from pathlib import Path

import numpy as np

from m23.file import getLinesWithNumbersFromFile


###
### Function: normalizeLogFiles
###
### Takes in reference file name, log files names to normalize
### and folder path to save the new files in
###
### Produces a normalization.txt file and Flux Logs combined folder
### with normalized files in the saveFolder
###
### BIG ASSUMPTION!!!!
### We assume that noOfStars in all log files is the same as no of stars in
### reference file. This is the case if the log files were produced using extraction
### module in this library. However, in case of log files produced by previous IDL code
### this was't true. This is also one of the reasons, this normalization code might be
### faster than the IDL version.
###
###
### TODO: Mask out stars with center pixel not matching + crop the outlier stars
###  using linfit
def normalizeLogFiles(
    referenceFileName,
    logFilesNamesToNormalize,
    logfile_adu_column,
    saveFolder: Path,
    date_of_night: date,
    startImageUsed="",
    endImageUsed="",
):

    ### Wrapper around the function so we don't
    ### have to keep passing the saveFolder as argument
    saveFileInFolder = lambda *args, **kwargs: saveFileInFolder(saveFolder, *args, **kwargs)

    ### COLUMN_NUMBERS (0 means first column)
    ref_adu_column = 5
    logfile_adu_column = 6
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

    ### At this point, if we want to look at 300-th star in our first image
    ### we would do logFilesData[0][299] (beware of python index starting from 0)
    noOfFiles = len(logFilesData)
    ### Normalization is done with reference to images 20%, 40%, 60% and 80% through night
    indicesToNormalizeTo = np.linspace(0, noOfFiles, 6, dtype="int")[1:-1]
    adus_in_data_to_normalize_to = np.array(logFilesData, dtype="object")[indicesToNormalizeTo]

    ### get the ADU column in the logfiles
    adus_in_data_to_normalize_to = np.array(
        [aduInLogData(data) for data in adus_in_data_to_normalize_to]
    )

    referenceFileStarPositions = [
        np.array(line.split()[ref_positions_xy[0] : ref_positions_xy[1] + 1], dtype="float")
        for line in referenceData
    ]

    ### matrix of image by star
    ### so 4th star in 100th image will be
    ### normalized_star_data[99][3]
    normalized_star_data = np.zeros((noOfFiles, len(referenceData)))

    ### find normalization factor for each file
    allNormFactors = []
    for file_index in range(noOfFiles):
        ### Normalization factor is the median of the scaleFactors of all stars for scaleFactors < 5
        ### where scaleFactor for a star for that image is the ratio of that star's adu in
        ### sum of data_to_normalize_to / 4 * adu in current image

        adu_of_current_log_file = np.array(aduInLogData(logFilesData[file_index]), dtype="float")

        starPositions = starPositionsInLogData(logFilesData[file_index])

        ### mask out stars with center more than 1 pixel away from those in the ref file
        ### also mask if the star is outside the 12px box around the image
        for star_index in range(len(adu_of_current_log_file)):
            starX, starY = starPositions[star_index]
            refX, refY = referenceFileStarPositions[star_index]
            if math.sqrt((refX - starX) ** 2 + (refY - starY) ** 2) > 1:
                adu_of_current_log_file[star_index] = 0

        ### Find normalization factor
        scale_factors_for_stars = np.sum(adus_in_data_to_normalize_to, axis=0) / (
            4 * adu_of_current_log_file
        )
        ### Only get the median value for scale factors between 0 and 5, since some values are
        ### -inf or nan
        ### We get the upper threshold 5 from the IDL code
        good_scale_factors = scale_factors_for_stars[
            np.where((scale_factors_for_stars < 5) & (scale_factors_for_stars > 0))
        ]
        normFactor = np.median(good_scale_factors) if len(good_scale_factors) else 0

        allNormFactors.append(normFactor)
        normalized_star_data[file_index] = normFactor * np.array(
            aduInLogData(logFilesData[file_index])
        )

    ### Save the norm factor dot txt

    np.savetxt(
        saveFolder
        / f"{date_of_night.strftime('%m-%d-%y')}_m23_7.0-ref_revised_71_normfactors.txt",
        np.array(allNormFactors),
        fmt="%3.5f",
    )

    ### Save the normalized data for each star
    noOfStars = len(normalized_star_data[0])
    for star_index in range(noOfStars):
        star_data = [
            normalized_star_data[file_index][star_index] for file_index in range(noOfFiles)
        ]
        ### turn all star_data that's negative to 0
        star_data = [currentData if currentData > 0 else 0 for currentData in star_data]

        # Add header information to the file
        # To make the layout consistent with output from IDL version
        with open(
            os.path.join(
                saveFolder,
                f"{date_of_night.strftime('%m-%d-%y')}_m23_7.0-ref_revised_71_{(star_index+1):04}_flux.txt",
            ),
            "w",
        ) as f:
            f.write(f"Program:\n")
            f.write(f"Started with image\t{startImageUsed}\n")
            f.write(f"Ended with image\t{endImageUsed}\n")
            f.write(f"Aligned with image {Path(referenceFileName).name}\n")
            f.write(f"X location:\t{''}\n")
            f.write(f"Y location:\t{''}\n")
            np.savetxt(
                f,
                np.array(star_data),
                fmt="%10.2f",
            )
