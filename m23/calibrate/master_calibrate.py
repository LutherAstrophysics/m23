from email import header
import sys

if "../../" not in sys.path:
    sys.path.insert(0, "../../")

import numpy as np

### m23 imports
from m23.trans import createFitFileWithSameHeader
from m23.utils import fitDataFromFitImages

### please note that code is a direct implementation of steps
### mentioned in Handbook of Astronomical Image `Processing by
### Richard Berry and James Burnell version 2.0 section 6.3 Standard Calibration


###  makeMasterDark
###
###  purpose: creates masterDark, saves to fileName + returns masterDarkData
###
### we generate the masterDark by "taking median of the dark frames"
###   --Richard Berry, James Burnell
def makeMasterDark(saveAs, headerToCopyFromName=None, listOfDarkNames=None, listOfDarkData=None):

    if listOfDarkNames:
        listOfDarkData = fitDataFromFitImages(listOfDarkNames)
    
    if not listOfDarkNames and not listOfDarkData:
        raise Exception("Neither Dark data nor names were provided")  

    if not headerToCopyFromName and listOfDarkNames:
        headerToCopyFromName = listOfDarkNames[0]
    elif not headerToCopyFromName and not listOfDarkNames:
        raise Exception("Filename to copy header from not provied")

    masterDarkData = getMedianOfMatrices(listOfDarkData)
    # listOfDarks[0] is the file whose header we're copying to
    #  save in masterDark
    createFitFileWithSameHeader(masterDarkData, saveAs, headerToCopyFromName)

    return masterDarkData


###  makeMasterFlat
###
###  purpose: creates masterFlat, saves to fileName + returns masterFlatData
###
### we generate the masterFlat by 
###   taking the median of flats and subtracting the masterDarkData
###  
def makeMasterFlat(saveAs, masterDarkData, headerToCopyFromName=None, listOfFlatNames=None, listOfFlatData=None):

    ### We're supposed to use flat dark for the master flat
    ### but we did not take any for the new camera, so we're
    ### using dark frames instead
    ### In other words: If we don't have flat dark, use dark frames
    ###

    if listOfFlatNames:
        listOfFlatData = fitDataFromFitImages(listOfFlatNames)
   
    if not listOfFlatNames and not listOfFlatData:
        raise Exception("Neither Flat data nor names were provided")  

    if not headerToCopyFromName and listOfFlatNames:
        headerToCopyFromName = listOfFlatNames[0]
    elif not headerToCopyFromName and not listOfFlatNames:
        raise Exception("Filename to copy header from not provied")


    ### We subtract the masterdark from the combined flats to get the master flat (p.189)
    combinedFlats = getMedianOfMatrices(listOfFlatData)
    masterFlatData = combinedFlats - masterDarkData
    # listOfFlats[0] is the file whose header we're copying to
    #  save in masterDark
    createFitFileWithSameHeader(masterFlatData, saveAs, headerToCopyFromName)

    return masterFlatData



def getMedianOfMatrices(listOfMatrices):

    ## https://stackoverflow.com/questions/18461623/average-values-in-two-numpy-arrays
    return np.median(
        np.array(listOfMatrices), axis=0, out=np.empty_like(listOfMatrices[0])
    )
