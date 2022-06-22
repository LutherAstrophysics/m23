import sys
if '../../' not in sys.path: sys.path.insert(0, '../../')

from astropy.io.fits import getdata as getfitsdata
from m23.trans.fits import createFitFileWithSameHeader
import numpy as np

### please note that code is a direct implementation of steps
### mentioned in Handbook of Astronomical Image Processing by
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



### we generate the masterDark by "taking median of the dark frames"
###   --Richar Berry, James Burnell
def makeMasterDark(listOfDarks, fileName):

    dataOfDarks = fitDataFromFitImages(listOfDarks)
    masterDarkData = getMedianOfMatrices(dataOfDarks)
    # listOfDarks[0] is the file whose header we're copying to 
    #  save in masterDark 
    createFitFileWithSameHeader(masterDarkData, fileName, listOfDarks[0]) 

    return masterDarkData


### we generate the masterFlat by ...
###
def makeMasterFlat(listOfFlats, masterDark, fileName):

    dataOfDarks = fitDataFromFitImages(listOfFlats) 
    combinedFlats = getMedianOfMatrices(dataOfDarks)
    masterFlatData = combinedFlats - masterDark
    # listOfFlats[0] is the file whose header we're copying to 
    #  save in masterDark 
    createFitFileWithSameHeader(masterFlatData, fileName, listOfFlats[0]) 

    return masterFlatData


def fitDataFromFitImages(images):
    return [getfitsdata(item) for item in images]


def getMedianOfMatrices(listOfMatrices):

    ## https://stackoverflow.com/questions/18461623/average-values-in-two-numpy-arrays
    return np.median(np.array(listOfMatrices), axis=0, out=np.empty_like(listOfMatrices[0]))
    
def getDarks(n):
    return f"dark_7.0-00{n}.fit"

def getFlats(n):
    return f"dark_7.0-00{n}.fit"

allDarks = [getDarks(i) for i in range(15, 21)]
masterDarkData = makeMasterDark(allDarks, "masterdark.fit")
makeMasterFlat(allDarks, masterDarkData, "masterFlat.fit")
