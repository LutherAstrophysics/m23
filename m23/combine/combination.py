import numpy as np

### imports from m23
from m23.trans import createFitFileWithSameHeader

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
###   the combined image data


def imageCombination(imagesData, fileName, fitFileNameToCopyHeaderFrom):
    imagesData = np.array(imagesData)
    combinedImageData = np.sum(imagesData, axis=0)

    createFitFileWithSameHeader(
        combinedImageData.astype("int"), fileName, fitFileNameToCopyHeaderFrom
    )
    return combinedImageData
