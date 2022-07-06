import sys
if "../../" not in sys.path:
    sys.path.insert(0, "../../")

from matplotlib.pyplot import ylabel
import numpy as np
import astroalign as ast
from astropy.io.fits import getdata as getfitsdata
from m23.trans.fits import createFitFileWithSameHeader

### There are three methods of photometry
### 1. Aperture photometry: This is the method we use
###    for the old camera, we create radii of 3, 4, 5 pixels around a star,
###    and calculate its flux value
### 2. Profile photometry: TODO: This method was deemed 
###    inappropriate since the old images did not have
###    as many pixels, but the new one have a lot more, 
###    so this is a method we want to try
### 3. Annular photometry

