from astropy.io import fits


def createFitFile(fitsHeader, fitsData, fileName):
    fits.writeto(fileName, fitsData, header=fitsHeader, overwrite=True)


def createFitFileWithSameHeader(fitsData, fileName, fileNameToCopyHeaderFrom):
    with fits.open(fileNameToCopyHeaderFrom) as fd:
        headerToCopy = fd[0].header
        createFitFile(headerToCopy, fitsData, fileName)
