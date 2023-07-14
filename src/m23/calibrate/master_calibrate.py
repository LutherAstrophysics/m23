import numpy as np

from m23.trans import createFitFileWithSameHeader
from m23.utils import customMedian, fitDataFromFitImages, sorted_by_number

# This code is a direct implementation of steps
# mentioned in Handbook of Astronomical Image `Processing by
# Richard Berry and James Burnell version 2.0 section 6.3 Standard Calibration


#  makeMasterBias
#
#  purpose: creates masterBias, saves to fileName + returns masterBiasData
#
def makeMasterBias(saveAs, headerToCopyFromName=None, listOfBiasNames=None, listOfBiasData=None):
    if listOfBiasNames:
        listOfBiasData = fitDataFromFitImages(listOfBiasNames)

    if not listOfBiasNames and not listOfBiasData:
        raise Exception("Neither Bias data nor names were provided")

    if not headerToCopyFromName and listOfBiasNames:
        headerToCopyFromName = listOfBiasNames[0]
    elif not headerToCopyFromName and not listOfBiasNames:
        raise Exception("Filename to copy header from not provided")

    masterBiasData = getMedianOfMatrices(listOfBiasData)
    # headerToCopyFromName is the file whose header we're copying to
    #  save in masterBias
    createFitFileWithSameHeader(masterBiasData, saveAs, headerToCopyFromName)

    return masterBiasData


#  makeMasterDark
#
#  purpose: creates masterDark, saves to fileName + returns masterDarkData
#
# we generate the masterDark by "taking median of the dark frames"
#   --Richard Berry, James Burnell
def makeMasterDark(
    saveAs=None,
    headerToCopyFromName=None,
    listOfDarkNames=None,
    listOfDarkData=None,
):
    if listOfDarkNames:
        listOfDarkData = fitDataFromFitImages(listOfDarkNames)

    if not listOfDarkNames and not listOfDarkData:
        raise Exception("Neither Dark data nor names were provided")

    masterDarkData = getMedianOfMatrices(listOfDarkData)
    # listOfDarks[0] is the file whose header we're copying to
    #  save in masterDark

    # Create the file only if filename to save as is provided
    if saveAs is not None:
        if not headerToCopyFromName and listOfDarkNames:
            headerToCopyFromName = listOfDarkNames[0]
        elif not headerToCopyFromName and not listOfDarkNames:
            raise Exception("Filename to copy header from not provided")

        createFitFileWithSameHeader(masterDarkData, saveAs, headerToCopyFromName)

    return masterDarkData


#  makeMasterFlat
#
#  purpose: creates masterFlat, saves to fileName + returns masterFlatData
#
# we generate the masterFlat by
#   taking the median of flats and subtracting the masterDarkData
#
def makeMasterFlat(
    saveAs,
    masterDarkData,
    headerToCopyFromName=None,
    listOfFlatNames=None,
    listOfFlatData=None,
):
    # We're supposed to use flat dark for the master flat
    # but we did not take any for the new camera, so we're
    # using dark frames instead
    # In other words: If we don't have flat dark, use dark frames
    #

    if listOfFlatNames:
        listOfFlatNames = sorted_by_number(listOfFlatNames)
        listOfFlatData = fitDataFromFitImages(listOfFlatNames)

    if not listOfFlatNames and not listOfFlatData:
        raise Exception("Neither Flat data nor names were provided")

    if not headerToCopyFromName and listOfFlatNames:
        headerToCopyFromName = listOfFlatNames[0]
    elif not headerToCopyFromName and not listOfFlatNames:
        raise Exception("Filename to copy header from not provied")

    firstFlatMedian = customMedian(listOfFlatData[0])
    # We scale all flats w.r.t. first flat image
    #   like the current IDL code does
    #   https://github.com/LutherAstrophysics/idl-files/blob/f3d10e770d4d268908438deb4cda2076f21f1b14/master_calibration_frame_makerNEWEST.pro#L199
    listOfFlatData = [
        flatData * firstFlatMedian / customMedian(flatData) for flatData in listOfFlatData
    ]
    # the we take the median of the scaled flats
    combinedFlats = getMedianOfMatrices(listOfFlatData)
    masterFlatData = combinedFlats - masterDarkData

    # convert flat data to matrix of ints
    masterFlatData = np.array(masterFlatData, dtype="int")
    # listOfFlats[0] is the file whose header we're copying to
    #  save in masterDark
    createFitFileWithSameHeader(masterFlatData, saveAs, headerToCopyFromName)
    return masterFlatData


def getMedianOfMatrices(listOfMatrices):
    # https://stackoverflow.com/questions/18461623/average-values-in-two-numpy-arrays
    return customMedian(np.array(listOfMatrices), axis=0, out=np.empty_like(listOfMatrices[0]))
