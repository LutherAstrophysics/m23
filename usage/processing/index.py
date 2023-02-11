###
### Boilerplate
import sys
from pathlib import Path

if "../../" not in sys.path:
    sys.path.insert(0, "../../")

import os
import re
from datetime import date, datetime

from astropy.io.fits import getdata

### local imports
from conventions import rawCalibrationFolderName, rawImagesFolderName

### setting import
from settings import currentSettings

###
from yaspin import yaspin

from m23.align import imageAlignment
from m23.calibrate import (
    calibrateImages,
    makeMasterBias,
    makeMasterDark,
    makeMasterFlat,
)
from m23.combine import imageCombination
from m23.extract import extractStars
from m23.matrix import crop, fillMatrix
from m23.norm import normalizeLogFiles

### m23 imports
from m23.utils import fitDataFromFitImages, fitFilesInFolder, raw_data_name_format


def main(settings=None):

    ### settings is provied to main function in case of automation
    ### see automate.py
    settingsToUse = settings or currentSettings
    newlinechar = "\n"

    ### expected number of rows, and pixels in the image
    row, column = settingsToUse.rows, settingsToUse.columns
    folderLocation = settingsToUse.imagesFolderLocation
    outputFolderLocation = settingsToUse.outputLocation

    # Check against the input folder name format
    input_folder_path = Path(folderLocation)
    assert input_folder_path.exists()
    try:
        proper_date = datetime.strptime(input_folder_path.name, raw_data_name_format)
    except ValueError as e:
        print("Aborting because of improper date name format for", folderLocation)
        print("Name should be in format (Month Name Day, Year): December 28, 2019")
        raise e

    print(f"Using {currentSettings}, for processing {os.path.split(folderLocation)[-1]}")

    ### Create output folder if it doesn't exist
    if not os.path.exists(outputFolderLocation):
        os.makedirs(outputFolderLocation)

    ### Set these to the same as settings.py:
    ### ref image, ref file paths, number of
    ### combined images, crop region, and master flat
    ### to use in case the night does not have flats taken
    referenceImagePath = settingsToUse.refImageLocation
    referenceFilePath = settingsToUse.refFilePath
    noOfImagesInOneCombination = settingsToUse.noOfCombination
    cropRegion = settingsToUse.listOfPolygonsToFill
    alternateMasterFlat = settingsToUse.alternateMasterFlat
    radiusOfExtraction = settingsToUse.radius

    ### Make the folders to hold the processed data
    calibrationFolderName = "Calibration Frames"
    alignedCombinedFolderName = "Aligned Combined"
    logFilesCombinedFolderName = "Log Files Combined"
    fluxLogsCombinedFolderName = "Flux Logs Combined"
    logfileName = "processlog.txt"

    ### helper function for output folder location
    def fileInOutputFolder(fileName):
        return os.path.join(outputFolderLocation, fileName)

    ### logFd is a file handle that writes logs of the processing code
    ### as it moves forward
    logfd = open(fileInOutputFolder(logfileName), "w")

    logfd.write(f"Created logfile to process {folderLocation} at {datetime.now()} {newlinechar}")

    ### write pre process logs
    logfd.write(f"Using {settingsToUse} {newlinechar}")
    logfd.write(f"Using reffile {referenceFilePath} {newlinechar}")
    logfd.write(f"Using ref image {referenceImagePath} {newlinechar}")
    logfd.write(f"Using radius of extraction: {radiusOfExtraction}{newlinechar}")

    ### Create folders if they don't already exist
    for folder in [
        calibrationFolderName,
        alignedCombinedFolderName,
        logFilesCombinedFolderName,
        fluxLogsCombinedFolderName,
    ]:
        if not os.path.exists(fileInOutputFolder(folder)):
            os.makedirs(fileInOutputFolder(folder))

    def fileInMasterCalibrate(fileName):
        return os.path.join(fileInOutputFolder(calibrationFolderName), fileName)

    def fileInAlignedCombined(fileName):
        return os.path.join(fileInOutputFolder(alignedCombinedFolderName), fileName)

    def fileInLogFilesCombined(fileName):
        return os.path.join(fileInOutputFolder(logFilesCombinedFolderName), fileName)

    ###
    ### masterCalibration
    ###
    calibrationsFolder = os.path.join(folderLocation, rawCalibrationFolderName)
    # biases = [
    #     os.path.join(calibrationsFolder, file)
    #     for file in fitFilesInFolder(calibrationsFolder, "bias")
    # ]
    ### Ignore biases
    biases = []
    darks = [
        os.path.join(calibrationsFolder, file)
        for file in fitFilesInFolder(calibrationsFolder, "dark")
    ]
    flats = [
        os.path.join(calibrationsFolder, file)
        for file in fitFilesInFolder(calibrationsFolder, "flat")
    ]

    ### Ignore the maaster bias since we don't use biases
    masterBiasData = None
    # if biases and len(biases):
    #     with yaspin(text=f"Cropping biases"):
    #         biasesDataCropped = [
    #             crop(matrix, row, column) for matrix in (fitDataFromFitImages(biases))
    #         ]

    #     with yaspin(text=f"Making master bias"):
    #         masterBiasData = makeMasterBias(
    #             saveAs=fileInMasterCalibrate("masterbias.fit"),
    #             headerToCopyFromName=biases[0],
    #             listOfBiasData=biasesDataCropped,
    #         )

    with yaspin(text=f"Cropping darks"):
        darksDataCropped = [crop(matrix, row, column) for matrix in (fitDataFromFitImages(darks))]

    ### if there are flats for the night
    if len(flats):
        with yaspin(text=f"Cropping flats"):
            flatsDataCropped = [
                crop(matrix, row, column) for matrix in (fitDataFromFitImages(flats))
            ]

    with yaspin(text=f"Making master dark"):
        masterDarkData = makeMasterDark(
            saveAs=fileInMasterCalibrate("masterdark.fit"),
            headerToCopyFromName=darks[0],
            listOfDarkData=darksDataCropped,
        )
        logfd.write(f"{datetime.now()} Made masterdark from{newlinechar}")
        logfd.write(f"{newlinechar.join(darks)}")
        logfd.write(f"{newlinechar}")

    ### Generate masterflat if flats are provided in calibrations folder
    ### else expects master flat filepath to be provided in settings
    if len(flats):
        with yaspin(text=f"Making master flat"):
            masterFlatData = makeMasterFlat(
                saveAs=fileInMasterCalibrate("masterflat.fit"),
                headerToCopyFromName=flats[0],
                listOfFlatData=flatsDataCropped,
                masterDarkData=masterDarkData,
            )
            logfd.write(f"{datetime.now()} Made masterflat from{newlinechar}")
            logfd.write(f"{newlinechar.join(flats)}")
            logfd.write(f"{newlinechar}")
    else:
        try:
            masterFlatData = getdata(alternateMasterFlat)
            logfd.write(
                f"{datetime.now()} using alternate masterflat {alternateMasterFlat}{newlinechar}"
            )
        except Exception as e:
            print("Did you provide path to master flat in settings???")
            raise e
    ###
    ###  Calibration step
    ###
    rawImagesFolder = os.path.join(folderLocation, rawImagesFolderName)
    allRawImagesNames = [
        os.path.join(rawImagesFolder, file) for file in fitFilesInFolder(rawImagesFolder)
    ]

    ###
    ### Sort raw images names to avoid indexing issue
    ###
    try:
        rawImagesNumbers = [re.search("-.*.fit", img)[0][1:-4] for img in allRawImagesNames]
        rawImageIndices = [int(img) for img in rawImagesNumbers]
        allRawImagesNames = [
            imageName for _, imageName in sorted(zip(rawImageIndices, allRawImagesNames))
        ]
        logfd.write(f"Raw Images {datetime.now()}{newlinechar}")
        if len(allRawImagesNames) == 0:
            print("No raw images found, returning")
            logfd.write(f"No raw images found to process")
            return
        logfd.write(f"{newlinechar.join(allRawImagesNames)}")
        logfd.write(f"{newlinechar}")
    except Exception as e:
        print("Raw image doesn't match the pattern: xxx-imagenumber.fit")
        print("Example: m23_7.0-010.fit")
        raise e
    ### processs given sets of images,
    ###  which includes
    ###  Cropping, Filling, Calibrating, Aligning, Combining, Extracting
    def process(imageStartIndex, imageEndIndex):

        ### Cropping the edges of the images
        rawImagesCropedData = [
            crop(matrix, row, column)
            for matrix in (fitDataFromFitImages(allRawImagesNames[imageStartIndex:imageEndIndex]))
        ]

        ### Image calibration
        calibratedImagesData = calibrateImages(
            masterDarkData=masterDarkData,
            masterFlatData=masterFlatData,
            masterBiasData=masterBiasData,
            listOfImagesData=rawImagesCropedData,
        )

        ### Filling out the four dark corners of the images
        calibratedImagesFilled = calibratedImagesData
        if len(cropRegion):
            calibratedImagesFilled = [
                fillMatrix(calibratedMatrix, cropRegion, 1)
                for calibratedMatrix in calibratedImagesData
            ]

        ### Image alignment
        alignedImagesData = []
        for imageIndex in range(len(calibratedImagesFilled)):
            try:
                alignedImagesData.append(
                    imageAlignment(calibratedImagesFilled[imageIndex], referenceImagePath)
                )
            except Exception as e:
                print(f"Could not align image {imageStartIndex + imageIndex}")
                logfd.write(
                    f"{newlinechar}Could not align image no {imageStartIndex + imageIndex} - {allRawImagesNames[imageStartIndex + imageIndex]}{newlinechar}"
                )

                ###
                ### We're throwing an exception here means that we don't
                ### want the code to proceed further in this function call
                ### process if an image could not be aligned.
                ###
                ### What this means is that if we were trying to do data
                ### processing of 205 images with 10 as number of images per
                ### combination, then the image no. 25 could not be aligned, then
                ### the images in the range 20-30 shall be ignored...

                ### This is better than just using images 20-24, 26-30 because we
                ### would then be combining only 9 images... one might think that the idea solution would
                ### use images 20-31 (ignoring 25) but it would be problematic since we might end up combining imaged from vastly different periods of night that way
                ###
                raise e

        ### Guard to check that we're always using the same number of
        ### images in any combination for that night of data.
        if len(alignedImagesData) == noOfImagesInOneCombination:
            combinedImageData = imageCombination(
                alignedImagesData,
                fileInAlignedCombined(
                    f"m23_7.0-{(imageEndIndex // noOfImagesInOneCombination):03}.fit"
                ),
                ### fileName we are copying header info from
                allRawImagesNames[imageStartIndex],
            )

            ### Extraction
            extractStars(
                combinedImageData,
                referenceFilePath,
                ### similar format to IDL code output
                saveAs=fileInLogFilesCombined(
                    f"{proper_date.strftime('%m-%d-%y')}_m23_7.0-{(imageEndIndex // 10):03}.txt"
                ),
                radiusOfExtraction=radiusOfExtraction,
            )
        else:
            print(
                f"No image could be aligned for the combination, not combining or extracting images {imageStartIndex}-{imageEndIndex}"
            )

    noOfCombinedImages = len(allRawImagesNames) // noOfImagesInOneCombination

    ###
    ### This code is for printing the process on the terminal
    ###
    for i in range(noOfCombinedImages):
        fromIndex = i * noOfImagesInOneCombination
        toIndex = (i + 1) * noOfImagesInOneCombination
        ### If there are 16 raw images, and the
        ###   #noOfImagesInOneCombination is 10
        ###   then only one combined image is formed, the last 6 are ignored
        with yaspin(text=f"Processing images {fromIndex}-{toIndex}"):
            try:
                logfd.write(
                    f"Processing images {fromIndex}-{toIndex} {datetime.now()}{newlinechar}"
                )
                process(fromIndex, toIndex)
            except Exception as e:
                print(f"Failed processing {fromIndex} - {toIndex}")
                print(f"{e}")
                print(f"Continuing with next set...")

    ### After extraction, we want to save the flux log files
    ### for each star and their normalization factor
    allLogFiles = sorted(
        [
            os.path.join(fileInOutputFolder(logFilesCombinedFolderName), file)
            for file in os.listdir(fileInOutputFolder(logFilesCombinedFolderName))
        ]
    )

    logfd.write(
        f"{newlinechar}Doing normalization {datetime.now()} of {len(allLogFiles)} logfiles"
    )
    logfd.write(f"{newlinechar.join(allLogFiles)}")
    logfd.write(f"{newlinechar}")

    ###
    ### Create a folder inside flux logs combined for corresponding raidus of extraction
    ###
    fluxLogsFolder = fileInOutputFolder(fluxLogsCombinedFolderName)
    # Check guard to tell that we currently only support 5px radius of extraction.
    assert radiusOfExtraction == 5
    starRadiusFolder = os.path.join(fluxLogsFolder, "Five Pixel Radius")
    if not os.path.exists(starRadiusFolder):
        os.makedirs(starRadiusFolder)

    ###
    ### Normalize the log files and save the stars and norm factors
    ### in output folder
    normalizeLogFiles(referenceFilePath, allLogFiles, starRadiusFolder, proper_date)

    ### To keep track of how long the code takes to run
    logfd.write(f"{newlinechar}Done normalization {datetime.now()}")

    ### close processing log file handle
    logfd.close()


if __name__ == "__main__":
    print(f"Starting {datetime.now()}")
    main()
    print(f"Done {datetime.now()}")
