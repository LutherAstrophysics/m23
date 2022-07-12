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


### local imports
from conventions import rawCalibrationFolderName, rawImagesFolderName


### setting import
from settings import currentSettings


def main():

    print(f"Using {currentSettings}, for processing")

    ### expected number of rows, and pixels in the image
    row, column = currentSettings.rows, currentSettings.columns
    folderLocation = currentSettings.imagesFolderLocation

    outputFolderLocation = currentSettings.outputLocation
    referenceImagePath = currentSettings.refImageLocation
    referenceFilePath = currentSettings.refFilePath
    noOfImagesInOneCombination = currentSettings.noOfCombination
    cropRegion = currentSettings.listOfPolygonsToFill

    calibrationFolderName = "Calibration Frames"
    alignedCombinedFolderName = "Aligned Combined"
    logFilesCombinedFolderName = "Log Files Combined"

    ### helper function for output folder location
    def fileInOutputFolder(fileName):
        return os.path.join(outputFolderLocation, fileName)

    ### Create folders if they don't already exist
    for folder in [calibrationFolderName, alignedCombinedFolderName,  logFilesCombinedFolderName]:
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
    biases = [
        os.path.join(calibrationsFolder, file)
        for file in fitFilesInFolder(calibrationsFolder, "bias")
    ]
    darks = [
        os.path.join(calibrationsFolder, file)
        for file in fitFilesInFolder(calibrationsFolder, "dark")
    ]
    flats = [
        os.path.join(calibrationsFolder, file)
        for file in fitFilesInFolder(calibrationsFolder, "flat")
    ]

    masterBiasData = None  # In case there isn't a bias
    if biases and len(biases):
        with yaspin(text=f"Cropping biases"):
            biasesDataCropped = [
                crop(matrix, row, column) for matrix in (fitDataFromFitImages(biases))
            ]

        with yaspin(text=f"Making master bias"):
            masterBiasData = makeMasterBias(
                saveAs=fileInMasterCalibrate("masterBias.fit"),
                headerToCopyFromName=biases[0],
                listOfBiasData=biasesDataCropped,
            )

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
            saveAs=fileInMasterCalibrate("masteflat.fit"),
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

        alignedImagesData = [
            imageAlignment(image, referenceImagePath)
            for image in calibratedImagesFilled
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
                fileInAlignedCombined(f"combined-{imageStartIndex}-{imageEndIndex}.fit"),
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


if __name__ == "__main__":
    print(f"Starting {datetime.now()}")
    main()
    print(f"Done {datetime.now()}")
