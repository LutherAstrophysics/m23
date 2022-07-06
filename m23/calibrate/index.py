import sys
if '../../' not in sys.path: sys.path.insert(0, '../../')

from m23.align.alignment import imageAlignment
from m23.calibrate.calibration import getCenterAverage

from m23.calibrate.master_calibrate import makeMasterDark, makeMasterFlat
from m23.calibrate.calibration import calibrateImages, getCenterAverage
from astropy.io.fits import getdata as getfitsdata
from m23.align.alignment import imageAlignment
from m23.names.alignment import nameAfterAlignment
from m23.combine.combination import imageCombination
from m23.names.calibration import nameAfterCalibration


# def getDark(n):
#     # zfill(x) pads with zeros at the beginning to make the string x-long
#     return f"dark_7.0-{str(n).zfill(4)}.fit"

# def getFlat(n):
#     return f"flat_7.0-{str(n).zfill(4)}.fit"

def getRaw(n):
    return f"m23_7.0-{str(n).zfill(4)}.fit"

# allDarks = [getDark(i) for i in range(1, 2)]
# allFlats = [getFlat(i) for i in range(1, 2)]
allRaw = [getRaw(i) for i in range(300, 400)]


# masterDark = makeMasterDark(allDarks, "masterdark.fit")
# masterFlat = makeMasterFlat(allFlats, masterDark, "masterflat.fit")


#### allAligned
###  takes a list of calibrated names for alignment
###  retuns a tuple of two things
###  (an array of image data after alignment, an arry of image names after alignment)
def allAligned(listOfCalibratedNames):
    allAlignedImagesData = []
    for calibratedImage in listOfCalibratedNames: 
        allAlignedImagesData.append(imageAlignment(calibratedImage, 'm23_7.0-0300.fit', nameAfterAlignment(calibratedImage)))
    
    return (allAlignedImagesData, [nameAfterAlignment(oldName) for oldName in listOfCalibratedNames])


calibratedImageNames = [nameAfterCalibration(img) for img in allRaw][1:]
for img in calibratedImageNames:
    try:
        imageAlignment(img, 'm23_7.0-0300-calibrated.fit', nameAfterAlignment(img))
    except:
        print(f"Error trying to align {img}")