import sys
if '../../' not in sys.path: sys.path.insert(0, '../../')

from m23.calibrate.calibration import getCenterAverage

from m23.calibrate.master_calibrate import makeMasterDark, makeMasterFlat
from m23.calibrate.calibration import calibrateImages, getCenterAverage
from astropy.io.fits import getdata as getfitsdata

def getDark(n):
    return f"dark_7.0-00{n}.fit"

def getFlat(n):
    return f"flat_7.0-00{n}.fit"

allDarks = [getDark(i) for i in range(15, 21)]
allFlats = [getFlat(i) for i in range(15, 21)]

masterDark = makeMasterDark(allDarks, "masterdark.fit")
masterFlat = makeMasterFlat(allFlats, masterDark, "masterflat.fit")

calibrated = calibrateImages(["m23_7.0-0607.fit"], masterDark, masterFlat)
