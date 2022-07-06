from statistics import median
import sys

if "../../" not in sys.path:
    sys.path.insert(0, "../../")

from matplotlib.pyplot import ylabel
import numpy as np
import astroalign as ast
from astropy.io.fits import getdata as getfitsdata

from m23.trans.fits import createFitFileWithSameHeader

### imageAlignment
###   purpose: align a particular image to a reference image
###
###   parameters:
###   imageToAlign: the image you want to align
###   refImage: the reference image (default is ref_revised_71)
###   
###   returns
###   aligned Image data as fit file

def imageAlignment(imageToAlign, refImage, fileName):
    imageToAlignData = getfitsdata(imageToAlign)
    refImageData = getfitsdata(refImage)

    ### workaround for endian type mismatch error in astroalign
    ### f4 means we're converting data to float 32
    target_fixed = np.array(refImageData, dtype="<f4")
    source_fixed = np.array(imageToAlignData, dtype="<f4")

    # alignedImageData, footprint = ast.register(imageToAlignData, refImageData, fill_value=50000)
    alignedImageData, footprint = ast.register(source_fixed, target_fixed, fill_value=0)


    createFitFileWithSameHeader(alignedImageData, fileName, imageToAlign)
    return alignedImageData


    