###
### Boilerplate
import sys

if "../../" not in sys.path:
    sys.path.insert(0, "../../")

import os
from datetime import datetime

###
from yaspin import yaspin


### m23 imports
from m23.utils import fitFilesInFolder, fitDataFromFitImages
from m23.matrix import crop, fillMatrix
from m23.calibrate import (
    makeMasterBias,
    makeMasterDark,
    makeMasterFlat,
    calibrateImages,
)
from m23.align import imageAlignment
from m23.combine import imageCombination
from m23.extract import extractStars
from m23.norm import normalizeLogFiles


### local imports
from conventions import rawCalibrationFolderName, rawImagesFolderName, alternateCalibrationFolderName


### setting import
from settings import currentSettings


def main(settings = None):

    ### settings is provied to main function in case of automation
    ### see automate.py
    settingsToUse = settings or currentSettings
    
    print(f"Using {currentSettings}, for processing")

    ### expected number of rows, and pixels in the image
    row, column = settingsToUse.rows, settingsToUse.columns
    folderLocation = settingsToUse.imagesFolderLocation

    outputFolderLocation = settingsToUse.outputLocation
    referenceImagePath = settingsToUse.refImageLocation
    referenceFilePath = settingsToUse.refFilePath
    noOfImagesInOneCombination = settingsToUse.noOfCombination
    cropRegion = settingsToUse.listOfPolygonsToFill

    calibrationFolderName = "Calibration Frames"
    alignedCombinedFolderName = "Aligned Combined"
    logFilesCombinedFolderName = "Log Files Combined"
    fluxLogsCombinedFolderName = "Flux Logs Combined"

    ### helper function for output folder location
    def fileInOutputFolder(fileName):
        return os.path.join(outputFolderLocation, fileName)

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
    alternateCalibrationFolder = os.path.join(folderLocation, alternateCalibrationFolderName)
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

    ### Looks for flats in alternate calibration folder
    ### if it can't find in the main calibration folder
    if len(flats) < 1:
        flats = [os.path.join(alternateCalibrationFolder, file) for file in fitFilesInFolder(alternateCalibrationFolder, "flat")]

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
        darksDataCropped = [
            crop(matrix, row, column) for matrix in (fitDataFromFitImages(darks))
        ]

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
    with yaspin(text=f"Making master flat"):
        masterFlatData = makeMasterFlat(
            saveAs=fileInMasterCalibrate("masterflat.fit"),
            headerToCopyFromName=flats[0],
            listOfFlatData=flatsDataCropped,
            masterDarkData=masterDarkData,
        )

    ###
    ###  Calibration step
    ###
    rawImagesFolder = os.path.join(folderLocation, rawImagesFolderName)
    allRawImagesNames = [
        os.path.join(rawImagesFolder, file)
        for file in fitFilesInFolder(rawImagesFolder)
    ]

    ### processs given sets of images,
    ###  which includes
    ###  Cropping, Filling, Calibrating, Aligning, Combining, Extracting
    def process(imageStartIndex, imageEndIndex):

        rawImagesCropedData = [
            crop(matrix, row, column)
            for matrix in (
                fitDataFromFitImages(allRawImagesNames[imageStartIndex:imageEndIndex])
            )
        ]

        calibratedImagesData = calibrateImages(
            masterDarkData=masterDarkData,
            masterFlatData=masterFlatData,
            masterBiasData=masterBiasData,
            listOfImagesData=rawImagesCropedData,
        )

        calibratedImagesFilled = calibratedImagesData
        if len(cropRegion):
            calibratedImagesFilled = [
                fillMatrix(calibratedMatrix, cropRegion, 1)
                for calibratedMatrix in calibratedImagesData
            ]

        alignedImagesData = []
        for imageIndex in range(len(calibratedImagesFilled)):
            try:
                alignedImagesData.append(
                    imageAlignment(
                        calibratedImagesFilled[imageIndex], referenceImagePath
                    )
                )
            except:
                print(f"Could not align image {imageStartIndex + imageIndex}")

        if len(alignedImagesData):
            combinedImageData = imageCombination(
                alignedImagesData,
                fileInAlignedCombined(
                    f"combined-{imageStartIndex}-{imageEndIndex}.fit"
                ),
                ### fileName we are copying header info from
                allRawImagesNames[imageStartIndex],
            )

            ###
            ### Extraction
            ###
            extractStars(
                combinedImageData,
                referenceFilePath,
                saveAs=fileInLogFilesCombined(
                    f"log-file-{imageStartIndex}-{imageEndIndex}.txt"
                ),
            )
        else:
            print(
                f"No image could be aligned for the combination, not combining or extracting images {imageStartIndex}-{imageEndIndex}"
            )

    noOfCombinedImages = len(allRawImagesNames) // noOfImagesInOneCombination

    for i in range(noOfCombinedImages):
        fromIndex = i * noOfImagesInOneCombination
        toIndex = (i + 1) * noOfImagesInOneCombination
        ### If there are 16 raw images, and the
        ###   #noOfImagesInOneCombination is 10
        ###   then only one combined image is formed, the last 6 are ignored
        with yaspin(text=f"Processing images {fromIndex}-{toIndex}"):
            try:
                process(fromIndex, toIndex)
            except Exception as e:
                print(f"Failed processing {fromIndex} - {toIndex}")
                print(f"{e}")
                print(f"Continuing with next set...")
                raise e

    ### After extraction, we want to save the flux log files
    ### for each star and their normalization factor
    allLogFiles = [
        os.path.join(fileInOutputFolder(logFilesCombinedFolderName), file)
        for file in os.listdir(fileInOutputFolder(logFilesCombinedFolderName))
    ]
    normalizeLogFiles(
        referenceFilePath, allLogFiles, fileInOutputFolder(fluxLogsCombinedFolderName)
    )


if __name__ == "__main__":
    print(f"Starting {datetime.now()}")
    main()
    print(f"Done {datetime.now()}")
