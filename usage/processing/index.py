###
### Boilerplate
import sys

if "../../" not in sys.path:
    sys.path.insert(0, "../../")

import os

###
from yaspin import yaspin


### m23 imports
from m23.utils import fitFilesInFolder, fitDataFromFitImages
from m23.matrix import crop, fillMatrix
from m23.calibrate import makeMasterDark, makeMasterFlat, calibrateImages
from m23.constants import NEW_CAMERA_CROP_REGION
from m23.align import imageAlignment
from m23.combine import imageCombination


### local imports
from conventions import rawCalibrationFolderName, rawImagesFolderName


def main():

    ### expected number of rows, and pixels in the image
    row, column = 2048, 2048

    # folderLocation = input("Enter folder location where data is stored for the night: ")
    # outputFolderLocation = input("Enter output folder location: ")
    # referenceImagePath = input("Path to reference image: ")
    # noOfCombination = int(input("Enter the number of images to combine: "))
    folderLocation = r"E:\xxx"
    outputFolderLocation = r"C:\Data Processing\xxx"
    noOfCombination = 10
    referenceImagePath = (
        r"C:\Data Processing\Summer 2019 M23\April 19\Aligned Combined\m23_7.0-050.fit"
    )

    ### helper function for output folder location
    def fileInOutputFolder(fileName):
        return os.path.join(outputFolderLocation, fileName)

    ###
    ### masterCalibration
    ###
    calibrationsFolder = os.path.join(folderLocation, rawCalibrationFolderName)
    darks = [
        os.path.join(calibrationsFolder, file)
        for file in fitFilesInFolder(calibrationsFolder, "dark")
    ]
    flats = [
        os.path.join(calibrationsFolder, file)
        for file in fitFilesInFolder(calibrationsFolder, "flat")
    ]
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
            saveAs=fileInOutputFolder("masterdark.fit"),
            headerToCopyFromName=darks[0],
            listOfDarkData=darksDataCropped,
        )
    with yaspin(text=f"Making master flat"):
        masterFlatData = makeMasterFlat(
            saveAs=fileInOutputFolder("masteflat.fit"),
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

    with yaspin(text=f"Cropping edges"):
        rawImagesCropedData = [
            crop(matrix, row, column)
            for matrix in (fitDataFromFitImages(allRawImagesNames))
        ]

    with yaspin(text=f"calibrating"):
        calibratedImagesData = calibrateImages(
            masterDarkData=masterDarkData,
            masterFlatData=masterFlatData,
            listOfImagesData=rawImagesCropedData,
        )

    with yaspin(text=f"Masking regions of bad pixels"):
        calibratedImagesFilled = [
            fillMatrix(calibratedMatrix, NEW_CAMERA_CROP_REGION, 1)
            for calibratedMatrix in calibratedImagesData
        ]

    ###
    ### Alignment
    ###
    with yaspin(text=f"Aligning"):
        try:
            alignedImagesData = [
                imageAlignment(image, referenceImagePath)
                for image in calibratedImagesFilled
            ]
        except:
            print("Could not align, combining without alignment")
            alignedImagesData = calibratedImagesFilled

    ###
    ### Combination
    ###
    noOfCombinedImages = len(alignedImagesData) // noOfCombination
    for index in range(noOfCombinedImages):
        with yaspin(
            text=f"Combining {index * noOfCombination} - {(index + 1) * noOfCombination}"
        ):
            imageCombination(
                alignedImagesData[
                    index * noOfCombination : (index + 1) * noOfCombination
                ],
                fileInOutputFolder(f"combined-{index}.fit"),
                allRawImagesNames[index * noOfCombination],
            )

    ###
    ### Extraction
    ###


if __name__ == "__main__":
    main()
