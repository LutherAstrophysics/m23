import numpy as np

from m23.constants import ASSUMED_MAX_BRIGHTNESS
from m23.matrix import cropIntoRectangle
from m23.utils import customMedian

# This file is for code related to applying master calibrations (dark, flats)
#   onto raw images

# Steps:
# 1. Compute average pixel value of the master flat using a square matrix
# 2. Using CALIBRATION = (AVERAGE_FLAT/MASTER_FLAT)*(RAW_IMAGE-MASTER_DARK)
#    Note: AVERAGE_FLAT is a value, MASTER_FLAT, RAW_IMAGE and MASTER_DARK are matrices.
# TODO:
#  Remove the hot pixels
#  Something to do with saving pixel values > 2 sigma in the IDL code ???

# getCenterAverage
#
# make a square center for the master flat-field frame (size is up to the user)
# and compute the average value of that square matrix
#
# 1024 x 1024 is cropped into 175x175 square box
# so 2048 x 2048 is cropped into 350 x 350 square box
# this is a square starting from (850, 850) to (1200, 1200)


def getCenterAverage(matrix):
    squareSize = 350 if matrix.shape[0] == 2048 else 175
    xPosition = 850 if matrix.shape[0] == 2048 else 425
    yPosition = 850 if matrix.shape[0] == 2048 else 425
    center = cropIntoRectangle(matrix, xPosition, squareSize, yPosition, squareSize)
    return np.mean(center)


# applyCalibration
#
# Please note that this code is a direct implementation of steps
# mentioned in Handbook of Astronomical Image Processing by
# Richard Berry and James Burnell section 6.3 Standard Calibration
#
# parameters:
#   rawImage: image name to calibrate
#   masterDarkData: masterDark data
#   masterFlatData: masterFlat data
#   averageFlatData: average value of center square of master flat
#   fileName: file Name to save the calibrated image to (needed if saving image)
#   hotPixelsInMasterDark: array of positions of hot pixels in master dark
#   save: whether or not to save image after calibration (optional, default : False)
#
# returns
#   calibrated image


def applyCalibration(
    imageData,
    masterDarkData,
    masterFlatData,
    averageFlatData,
    hotPixelsInMasterDark,
):
    # Calibration Step:

    # Completely Ignore bias
    # if len(masterBiasData):
    # imageData = imageData - masterBiasData
    # masterDarkData = masterDarkData - masterBiasData

    subtractedRaw = imageData - masterDarkData
    flatRatio = np.array(averageFlatData / masterFlatData)
    # dtype is set to float32 for our image viewing software Astromagic, since
    # it does not support float64 We think we are not losing any significant
    # precision with this down casting

    calibratedImage = np.multiply(flatRatio, subtractedRaw, dtype="float32")

    # Unlike current IDL Code we're doing this step to calibrated
    #   image instead of the raw
    # Calculate the median and standard deviation of the raw image

    medianInRaw = customMedian(imageData)
    stdInRaw = np.std(imageData)

    # NOTE We don't know why it's 2 sigma???
    highValue = medianInRaw + 2 * stdInRaw
    lowValue = medianInRaw - 2 * stdInRaw

    # recalibrate the pixels in hot positions (which are defined by
    #   hot pixels in masterDark)
    for pixelLocation in hotPixelsInMasterDark:
        recalibrateAtHotLocation(pixelLocation, calibratedImage, highValue, lowValue)

    # This calibration formula converts low background values to very high values,
    # sometimes up to millions, whereas the maximum signal of stars is less than
    # one hundred thousand
    # This will affect our alignment star-finding algorithm,
    # so we want to set these values to 0

    calibratedImage[calibratedImage > ASSUMED_MAX_BRIGHTNESS] = 0

    # Only create file if fileName is provided
    return calibratedImage


def recalibrateAtHotLocation(location, calibratedImageData, highValue, lowValue):
    # For all hot pixel positions that aren't at edges (in the master dark)
    # Check if the pixel value in calibrated( or RAW ??? TO FIX) img is abnormally
    #   high + one of the surrounding pixels is abnormally high too,
    #   then we fit a gaussian of surrounding 10X10 pixel box
    #   and assign the gaussian's value at position [5,5] (because that's the center
    #   pixel we started with) to that pixel value.
    #  ELSE: In other words:
    #  If the pixel value is not abnormally high, or if it's abnormally high but none of
    #    its surrounding pixels is abnormally high:
    #    create a 3X3 box with our pixel at center, and take the average of 8 pixels around it

    row, col = location

    # This is the smallest surrounding
    # We use 11*11 surrounding for Gaussian
    # and 3*3 for average
    def surroundingValues():
        return [
            calibratedImageData[row - 1, col],
            calibratedImageData[row + 1, col],
            calibratedImageData[row, col - 1],
            calibratedImageData[row, col + 1],
        ]

    def needsGaussian():
        # isHigh
        isHigh = calibratedImageData[row][col].all() > highValue and any(
            [value > highValue for value in surroundingValues()]
        )
        # isLow
        isLow = calibratedImageData[row][col].all() < lowValue and any(
            [value < lowValue for value in surroundingValues()]
        )
        return isHigh or isLow

    def doGaussian():
        # Create a gaussian matrix for the surrounding matrix
        # Let the hot pixel value equal to the middle position value of the gaussian box
        # Gaussian needs to be done, for now though we're just taking average.
        # TODO
        takeAverage()

    def takeAverage():
        surroundingMatrix = calibratedImageData[row - 1 : row + 2, col - 1 : col + 2]
        surroundingSum = np.sum(surroundingMatrix)
        surroundingMatrixAverageWithoutCenter = (
            surroundingSum - calibratedImageData[row][col]
        ) / 8
        calibratedImageData[row][col] = surroundingMatrixAverageWithoutCenter

    doGaussian() if needsGaussian() else takeAverage()


# A word of caution:
#   When we need the fileName, we'll call it xxxFileName
#   and when we just need the fits data in that file, we will call
#   it xxxData
#
#   For example: masterDarkFileName if fileName for masterDark image is required
#   and masterDarkData if the data of that fit file is required!


# HEADER COMMENTS: TODO

# purpose:
#   takes a list of image data to calibrate
#   returns array of calibrated image data,


def calibrateImages(masterDarkData, masterFlatData, listOfImagesData, masterBiasData=np.array([])):
    # We save the hot pixels, which are 3 standard deviation higher than the median
    # We will save their positions (x,y)
    stdInMasterDark = np.std(masterDarkData)
    medianInMasterDark = customMedian(masterDarkData)

    # Find hot pixel positions
    hotPixelPositions = np.column_stack(
        np.where(masterDarkData > medianInMasterDark + 3 * stdInMasterDark)
    )

    # We define the edges as the outermost 5 (or 10???) pixels????
    edgeSize = 5

    # noOfRows and columns in masterdarkData
    totalRows, totalColumns = masterDarkData.shape[0], masterDarkData.shape[1]

    # Filter out the edges
    # Filter top/left
    topLeftFiltered = filter(
        lambda row_column: not (row_column[0] < edgeSize or row_column[1] < edgeSize),
        hotPixelPositions,
    )
    # Filter bottom/right & convert to tuple
    filteredHotPixelPositions = tuple(
        filter(
            lambda row_column: not (
                row_column[0] > totalRows - edgeSize or row_column[1] > totalColumns - edgeSize
            ),
            topLeftFiltered,
        )
    )

    averageFlat = (getCenterAverage(masterFlatData),)

    # print("NO OF HOT PIXEL", len(filteredHotPixelPositions))
    # We need to find the flux values of (x,y) in the calibrated images

    return [
        applyCalibration(
            imageData,
            masterDarkData,
            masterFlatData,
            averageFlat,
            hotPixelsInMasterDark=filteredHotPixelPositions,
        )
        for imageData in listOfImagesData
    ]
