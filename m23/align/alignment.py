import astroalign as ast
import numpy as np
from astropy.io.fits import getdata as getfitsdata

### imageAlignment
###   purpose: align a particular image to a reference image
###
###   parameters:
###   imageToAlign: the image you want to align
###   refImage: the reference image (default is ref_revised_71)
###
###   returns
###   aligned Image data as fit file


def imageAlignment(imageToAlignData, refImageName):
    refImageData = getfitsdata(refImageName)

    ### workaround for endian type mismatch error in astroalign
    ### f4 means we're converting data to float 32
    target_fixed = np.array(refImageData, dtype="float")
    source_fixed = np.array(imageToAlignData, dtype="float")

    # alignedImageData, footprint = ast.register(imageToAlignData, refImageData, fill_value=50000)
    alignedImageData, footprint = ast.register(source_fixed, target_fixed, fill_value=0)

    return alignedImageData
