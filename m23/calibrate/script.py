import sys
if '../../' not in sys.path: sys.path.insert(0, '../../')

from astropy.io.fits import getdata
import numpy as np

from m23.matrix.fill import fillMatrix
from m23.trans.fits import createFitFileWithSameHeader


orgFileName = "m23_7.0-0916.fit"

data = getdata(orgFileName)

polygons = [
    [(0,2048-1600), (0,0), (492,0), (210, 2048-1867)],
    [(0, 1600), (0, 2048), (480, 2048), (210, 1867)],
    [(1400, 2048), (2048, 2048), (2048, 1500), (1834, 1830)],
    [(1508, 0), (1852, 241), (2048, 521), (2048, 0)]
]

fillMatrix(data, polygons, (100000))
createFitFileWithSameHeader(data, "cropped.fit", orgFileName)