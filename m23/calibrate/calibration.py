from statistics import median
import sys

if "../../" not in sys.path:
    sys.path.insert(0, "../../")

from matplotlib.pyplot import ylabel
import numpy as np
from astropy.io.fits import getdata as getfitsdata

### imports from m23
from m23.matrix.crop import cropIntoRectangle
from m23.matrix.utils import surroundWith
from m23.trans.fits import createFitFileWithSameHeader
from m23.names.calibration import nameAfterCalibration


### This file is for code related to applying master calibrations (dark, flats)
###   onto raw images

### Steps:
### 1. Compute average pixel value of the master flat using a square matrix
### 2. Using CALIBRATION = (AVERAGE_FLAT/MASTER_FLAT)*(RAW_IMAGE-MASTER_DARK)
###    Note: AVERAGE_FLAT is a value, MASTER_FLAT, RAW_IMAGE and MASTER_DARK are matrices.
### TODO:
###  Remove the hot pixels
###  Something to do with saving pixel values > 2 sigma in the IDL code ???

### getCenterAverage
###
### make a square center for the master flat-field frame (size is up to the user)
### and compute the average value of that square matrix
###
### 1024 x 1024 is cropped into 175x175 square box
### so 2048 x 2048 is cropped into 350 x 350 square box
### this is a square starting from (850, 850) to (1200, 1200)


def getCenterAverage(matrix):
    squareSize = 350 if matrix.shape[0] == 2048 else 175
    xPosition = 850 if matrix.shape[0] == 2048 else 425
    yPosition = 850 if matrix.shape[0] == 2048 else 425
    center = cropIntoRectangle(matrix, xPosition, squareSize, yPosition, squareSize)
    return np.mean(center)


### applyCalibration
###
### Please note that this code is a direct implementation of steps
### mentioned in Handbook of Astronomical Image Processing by
### Richard Berry and James Burnell section 6.3 Standard Calibration
###
### parameters:
###   rawImage: image name to calibrate
###   masterDarkData: masterDark data
###   masterFlatData: masterFlat data
###   averageFlatData: average value of center square of master flat
###   fileName: file Name to save the calibrated image to
###   hotPixelsInMasterDark: TODO
###
### returns
###   calibrated image


def applyCalibration(
    rawImageName,
    masterDarkData,
    masterFlatData,
    averageFlatData,
    fileName,
    hotPixelsInMasterDark,
):

    rawImage = getfitsdata(rawImageName)

    ### THIS SHOULD BE DONE AFTER CALIBRATION STEP
    ###   But we are doing it this way because the IDL code currently
    ###   does it that way
    ### THIS IS A MYSTERY!!!! MUST BE FIXED

    ### Calculate the median and standard deviation of the raw image
    medianInRaw = np.median(rawImage)
    stdInRaw = np.std(rawImage)

    ### NOTE We don't know why it's 2 sigma???
    highValue = medianInRaw + 2 * stdInRaw

    ### Calibration Step:
    subtractedRaw = rawImage - masterDarkData
    flatRatio = np.array(averageFlatData / masterFlatData)
    ### dtype is set to float32 for our image viewing software Astromagic, since it does not support float64
    ### We think we are not losing any significant precision with this downcasting
    calibratedImage = np.multiply(flatRatio, subtractedRaw, dtype="float32")

    ### For all hot pixel positions that aren't at edges (in the master dark)
    ### Check if the pixel value in calibrated( or RAW ??? TOFIX) img is abnormally
    ###   high + one of the surrounding pixels is abnormally high too,
    ###   then we fit a gaussian of surrounding 10X10 pixel box
    ###   and assign the gaussian's value at postion [5,5] (because that's the center
    ###   pixel we started with) to that pixel value.
    ###  ELSE: In other words:
    ###  If the pixel value is not abnormally high, or if it's abnomrally high but none of
    ###    its surrounding pixels is abnormally high:
    ###    create a 3X3 box with our pixel at center, and take the average of 8 pixels around it

    ### needs optimization
    # for pixelLocation in hotPixelsInMasterDark:
    #     recalibrateAtHotLocation(pixelLocation, calibratedImage, highValue)

    # Only create file if fileName is provided
    if fileName:
        createFitFileWithSameHeader(calibratedImage, fileName, rawImageName)
    return calibratedImage


def recalibrateAtHotLocation(location, calibratedImageData, highValue):

    row, col = location

    ### This is the smallest surrounding
    ### We use 11*11 surrounding for Gaussian
    ### and 3*3 for average
    def surroundingValues():
        return [
            calibratedImageData[row - 1, col],
            calibratedImageData[row + 1, col],
            calibratedImageData[row, col - 1],
            calibratedImageData[row, col + 1],
        ]

    def needsGausian():
        return calibratedImageData[location] > highValue and any(
            [value > highValue for value in surroundingValues()]
        )

    def doGaussain():
        surroundingMatrixGaussBox = calibratedImageData[
            row - 5 : row + 5, col - 5 : col + 5
        ]

        ### Create a gaussian matrix for the surrounding matrix
        ### Let the hot pixel value equal to the middle position value of the gaussian box

        # TODO
        takeAverage()
        # calibratedImageData[location] = gaussianMatrix[5, 5]

    def takeAverage():
        surroundingMatrix = calibratedImageData[row - 1 : row + 1, col - 1 : col + 1]
        surroudingSum = np.sum(surroundingMatrix)
        surroundingMatrixAverageWithoutCenter = (
            surroudingSum - calibratedImageData[location]
        ) / 8
        calibratedImageData[location] = surroundingMatrixAverageWithoutCenter

    doGaussian() if needsGausian() else takeAverage()


### A word of caution:
###   When we need the fileName, we'll call it xxxFileName
###   and when we just need the fits data in that file, we will call
###   it xxxData
###
###   For example: masterDarkFileName if fileName for masterDark image is required
###   and masterDarkData if the data of that fit file is required!


### HEADER COMMENTS: TODO

### purpose:
###   takes a list of image names to calibrate
###   returns calibrated images, saves them
def calibrateImages(listOfImageNames, masterDarkData, masterFlatData):

    ### We save the hot pixels, which are 3 standard deviation higher than the median
    ### We will save their positions (x,y)
    stdInMasterDark = np.std(masterDarkData)
    medianInMasterDark = np.median(masterDarkData)

    ### Find hot pixel positions
    hotPixelPositions = np.where(
        masterDarkData > medianInMasterDark + 3 * stdInMasterDark
    )
    ### covert to easily indexable tuple
    hotPixelPositions = zip(hotPixelPositions[0], hotPixelPositions[1])

    ### We define the edges as the outermost 5 (or 10???) pixels????
    edgeSize = 5

    ### noOfRows and colums in masterdarkData
    totalRows, totalColumns = masterDarkData.shape[0], masterDarkData.shape[1]

    ### Filter out the edges
    ### Filter top/left
    topLeftFiltered = filter(
        lambda position: position[0] < edgeSize or position[1] < edgeSize,
        hotPixelPositions,
    )
    ### Filter bottom/right & convert to tuple
    filteredHotPixelPositions = tuple(
        filter(
            lambda position: position[0] > totalRows - edgeSize
            or position[1] > totalColumns - edgeSize,
            topLeftFiltered,
        )
    )
    averageFlat = (getCenterAverage(masterFlatData),)

    ### We need to find the flux values of (x,y) in the calibrated images

    for image in listOfImageNames:
        applyCalibration(
            rawImageName=image,
            masterDarkData=masterDarkData,
            masterFlatData=masterFlatData,
            averageFlatData=averageFlat,
            fileName=nameAfterCalibration(image),
            hotPixelsInMasterDark=hotPixelPositions,
        )

    # print("Hot pixels were", filteredHotPixelPositions)
