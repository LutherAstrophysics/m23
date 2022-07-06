import sys
if '../../' not in sys.path: sys.path.insert(0, '../../')

from m23.calibrate.master_calibrate import makeMasterDark
from astropy.io.fits import getdata
import numpy as np
from m23.names.alignment import nameAfterAlignment
from m23.align.alignment import imageAlignment
from m23.combine.combination import imageCombination


a = getdata("m23_7.0-0300-calibrated.fit")
b = getdata("m23_7.0-0301-calibrated.fit")