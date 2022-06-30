import sys

if "../../" not in sys.path:
    sys.path.insert(0, "../../")

from astropy.io.fits import getdata as getfitsdata
from m23.trans.fits import createFitFileWithSameHeader
from m23.matrix.crop import crop
import numpy as np

### please note that code is a direct implementation of steps
### mentioned in Handbook of Astronomical Image `Processing by
### Richard Berry and James Burnell section 6.3 Standard Calibration

###
### calibrate function specifications:
###
### input:
###   list of darks - for a night
###   list of flats - for a night
###
### process
###   raw image to calibrate (fit file) - for the same night
###   generate master dark
###   generate master flat
###   we are ignoring biases and using dark frames as flatdarks
###
### output
###   list of calibrated images


def calibrate(listOfDarks, listOfFlats, rawImages):

    masterDark = makeMasterDark(listOfDarks)
    masterFlat = makeMasterFlat(listOfFlats)

    return listOfCalibratedImages

###  makeMasterDark
###
###  purpose: creates masterDark, saves to fileName + returns masterDarkData
###
### we generate the masterDark by "taking median of the dark frames"
###   --Richar Berry, James Burnell
def makeMasterDark(listOfDarks, fileName, row=2048, column=2048):

    dataOfDarks = [
        crop(matrix, row, column) for matrix in (fitDataFromFitImages(listOfDarks))
    ]
    masterDarkData = getMedianOfMatrices(dataOfDarks)
    # listOfDarks[0] is the file whose header we're copying to
    #  save in masterDark
    createFitFileWithSameHeader(masterDarkData, fileName, listOfDarks[0])

    return masterDarkData


###  makeMasterFlat
###
###  purpose: creates masterFlat, saves to fileName + returns masterFlatData
###
### we generate the masterFlat by 
###   taking the median of flats and subtracting the masterDarkData
###  
def makeMasterFlat(listOfFlatNames, masterDarkData, fileName, row=2048, columns=2048):

    ### We're supposed to use flat dark for the master flat
    ### but we did not take any for the new camera, so we're
    ### using dark frames instead
    ### In other words: If we don't have flat dark, use dark frames
    ###

    combinedFlats = getMedianOfMatrices(fitDataFromFitImages(listOfFlatNames))
    masterFlatData = combinedFlats - masterDarkData
    # listOfFlats[0] is the file whose header we're copying to
    #  save in masterDark
    createFitFileWithSameHeader(masterFlatData, fileName, listOfFlatNames[0])

    return masterFlatData


def fitDataFromFitImages(images):
    return [getfitsdata(item) for item in images]


def getMedianOfMatrices(listOfMatrices):

    ## https://stackoverflow.com/questions/18461623/average-values-in-two-numpy-arrays
    return np.median(
        np.array(listOfMatrices), axis=0, out=np.empty_like(listOfMatrices[0])
    )
