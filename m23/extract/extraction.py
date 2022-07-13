import sys

if "../../" not in sys.path:
    sys.path.insert(0, "../../")

import numpy as np
from astropy.io.fits import getdata as getfitsdata
from functools import cache
import math

### m23 imports
from m23.trans import createFitFileWithSameHeader
from m23.matrix import blockRegions
from m23.file import getLinesWithNumbersFromFile

### There are three methods of photometry
### 1. Aperture photometry: This is the method we use
###    for the old camera, we create radii of 3, 4, 5 pixels around a star,
###    and calculate its flux value
### 2. Profile photometry: TODO: This method was deemed
###    inappropriate since the old images did not have
###    as many pixels, but the new one have a lot more,
###    so this is a method we want to try
### 3. Annular photometry

### radius the raidus used for finding star center,
###  not the raidus of extraction
def newStarCenters(imageData, oldStarCenters, radius=5):
    def centerFinder(position):
        x, y = position
        # roundedX, roundedY = np.round(position).astype("int")

        # starBox = imageData[
        #     roundedX - radius : roundedX + radius + 1,
        #     roundedY - radius : roundedY + radius + 1,
        # ]
        # starBox = np.multiply(starBox, circleMatrix(radius))
        # rowSum = np.sum(starBox, axis=0)
        # colSum = np.sum(starBox, axis=1)
        # if np.sum(rowSum) == 0 or np.sum(colSum) == 0:
        #     starXPosition, starYPosition = position
        # else:
        #     starXPosition = np.average(
        #         np.arange(len(rowSum)) + (x - radius), weights=rowSum
        #     )
        #     starYPosition = np.average(
        #         np.arange(len(colSum)) + (y - radius), weights=colSum
        #     )

        # return (starXPosition, starYPosition)

        xWghtSum = 0
        yWghtSum = 0
        WghtSum = 0
        for xAxis in range(-5, 6):
            for yAxis in range(-5, 6):
                if math.ceil(math.sqrt(xAxis ** 2 + yAxis ** 2)) <= 5:
                    WghtSum = WghtSum + imageData[round(x) + xAxis][round(y) + yAxis]
                    xWghtSum = xWghtSum + imageData[round(x) + xAxis][round(y) + yAxis] * (x + xAxis)
                    yWghtSum = yWghtSum + imageData[round(x) + xAxis][round(y) + yAxis] * (y + yAxis)
        
        if WghtSum > 0 :
            xWght = xWghtSum / WghtSum
            yWght = yWghtSum / WghtSum
        else:
            xWght = x 
            yWght = y
        
        return xWght, yWght


    return [centerFinder(position) for position in oldStarCenters]
   

def extractStars(imageData, referenceLogFileName, saveAs, radiusOfExtraction=5):
    starsPositionsInRefFile = starsPositionsInLogFile(referenceLogFileName)
    starsCentersInNewImage = newStarCenters(imageData, starsPositionsInRefFile)
    ### ???
    regionSize = 64
    pixelsPerStar = np.count_nonzero(circleMatrix(radiusOfExtraction))

    ###
    ### return
    ###  an array of arrays of 64x64 matrices
    @cache
    def backgroundRegion():
        row, col = imageData.shape
        ### block in third row first column can be accessed by [2, 0]
        return blockRegions(imageData, (regionSize, regionSize)).reshape(
            row // regionSize, col // regionSize, regionSize, regionSize
        )

    ###
    ### backgroundRegionTuple is (2, 0) if referring to region in
    ###  third row, first column
    @cache
    def backgroundAverage(backgroundRegionTuple):
        row, column = backgroundRegionTuple
        region = backgroundRegion()[row][column]
        ### throw out the background of zeroes, since
        ###   they might be at the edge
        sortedData = np.sort(region, axis=None)
        nonZeroIndices = np.nonzero(sortedData)
        ### ignore the zeros
        sortedData = sortedData[nonZeroIndices]

        centeredArray = sortedData[
            int(len(sortedData) // 2 - 0.05 * len(sortedData)) : int(
                len(sortedData) // 2 + 0.05 * len(sortedData)
            )
        ]
        return np.mean(centeredArray)

    # ### starFlux
    # ###
    # ### return a threetuple
    # ### Total star flux + star pixels
    # ###   average background value for the star region
    # ###   star flux value after background subtraction
    def fluxSumForStar(position, radius):
        x, y = position
        starBox = imageData[x - radius : x + radius + 1, y - radius : y + radius + 1]
        starBox = np.multiply(starBox, circleMatrix(radius))
        backgroundAverageInStarRegion = backgroundAverage(
            (x // regionSize, y // regionSize)
        )
        subtractedStarFlux = (
            np.sum(starBox) - backgroundAverageInStarRegion * pixelsPerStar
        )
        return np.sum(starBox), backgroundAverageInStarRegion, subtractedStarFlux

    starsFluxes = [
        fluxSumForStar(np.round(position).astype("int"), radiusOfExtraction)
        for position in starsCentersInNewImage
    ]

    ### create file
    with open(saveAs, "w") as fd:
        fd.write(
            f"Stars Found: {len(list(filter(lambda starFlux: starFlux[0] > 0, starsFluxes)))}\n"
        )
        headers = ["X", "Y", "Star Flux", "Background", "Normalized"]
        fd.write("\t".join(headers))
        fd.write("\n")
        for starIndex in range(len(starsFluxes)):
            ### write only if the star is found
            if starsFluxes[starIndex][0] > 0:
                data = starsCentersInNewImage[starIndex][::-1] + starsFluxes[starIndex]
                fd.write("\t".join(f"{item:.2f}" for item in data))
                fd.write("\n")


@cache
def starsPositionsInLogFile(fileName):
    linesWithNumbers = getLinesWithNumbersFromFile(fileName)
    #### Assumes X and Y are the first two columns for the file
    return [np.array(line.split()[:2][::-1], dtype="float16") for line in linesWithNumbers]


@cache
def circleMatrix(radius):
    lengthOfSquare = radius * 2 + 1
    myMatrix = np.zeros(lengthOfSquare * lengthOfSquare).reshape(
        lengthOfSquare, lengthOfSquare
    )
    for row in range(-radius, radius + 1):
        for col in range(-radius, radius + 1):
            if math.ceil(math.sqrt((row) ** 2 + (col) ** 2)) <= radius:
                myMatrix[row + radius][col + radius] = 1
    return myMatrix
