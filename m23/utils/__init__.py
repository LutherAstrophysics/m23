import os

import numpy as np
from astropy.io.fits import getdata as getfitsdata

from .date import get_closet_date

### local imports
from .rename import rename


def fitFilesInFolder(folder, fileType="All"):
    allFiles = os.listdir(folder)
    fileType = fileType.lower()

    allFiles = list(filter(lambda x: x.endswith(".fit"), allFiles))
    if fileType == "all":
        return allFiles
    else:
        return list(filter(lambda x: x.__contains__(fileType), allFiles))


def fitDataFromFitImages(images):
    return [getfitsdata(item) for item in images]


### Similar to the default version of IDL Median
### https://github.com/LutherAstrophysics/python-helpers/issues/8
def customMedian(arr, *args, **kwargs):
    arr = np.array(arr)
    if len(arr) % 2 == 0:
        newArray = np.append(arr, [np.multiply(np.ones(arr[0].shape), np.max(arr))], axis=0)
        return np.median(newArray, *args, **kwargs)
    else:
        return np.median(arr, *args, **kwargs)


__all__ = ["customeMedian", "fitFilesInFolder", "rename", "get_closet_date"]
