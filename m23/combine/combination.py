import sys

if "../../" not in sys.path:
    sys.path.insert(0, "../../")

from matplotlib.pyplot import ylabel
import numpy as np
from astropy.io.fits import getdata as getfitsdata

### imports from m23
from m23.matrix import cropIntoRectangle
from m23.matrix import surroundWith
from m23.trans import createFitFileWithSameHeader
from m23.names import nameAfterCalibration
from m23.calibrate.master_calibrate import fitDataFromFitImages

### imagesToCombine
###   purpose: combine the calibrated images in a night
###
###   NOTE: The IDL code does the alignment before the
###   combination, so we will do the same
###
### paramaters
###   calibratedImageNames: file names of the calibrated images
###   imagesToCombineNumber: number of images to combine (default is 10)
###   totalImageNumber: total number of images to combine
### 
### returns
###  a tuple of two things
###    (combined image data, combined image name)

def imageCombination(imagesData, fileName, fitFileNameToCopyHeaderFrom):
    imagesData = np.array(imagesData)
    combinedImageData = np.sum(imagesData, axis=0)

    createFitFileWithSameHeader(combinedImageData, fileName, fitFileNameToCopyHeaderFrom)
    return (combinedImageData, fileName)

