import os

from astropy.io.fits import getdata as getfitsdata


def fitFilesInFolder(folder, fileType="All"):
    allFiles = os.listdir(folder)
    fileType = fileType.lower()
    
    allFiles = list(filter(lambda x : x.endswith('.fit'), allFiles))
    if fileType == "all":
        return allFiles
    else:
        return list(filter(lambda x: x.__contains__(fileType), allFiles))



def fitDataFromFitImages(images):
    return [getfitsdata(item) for item in images]
