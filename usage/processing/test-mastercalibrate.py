import sys

from numpy import extract

if "../../" not in sys.path:
    sys.path.insert(0, "../../")

import os 
from astropy.io.fits import getdata
from m23.calibrate import makeMasterDark, makeMasterFlat

# TODO