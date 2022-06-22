from astropy.io import fits
import numpy as np
from m23.funcs.hof import noOfArgs

###
### readFit
###
### Purpose: 
###     takes in a fileName, and a function workWithFit
###     and call the procedure workWithFit passing the 
###
###  
@noOfArgs(2)
def readFits(*args):
    fileName, workWithFit = args
    with fits.open(fileName) as fd:
        workWithFit(fd[0])


###
### fitsToCSV
###
### Purpose: 
###     takes in name of fitsFile and csvLocation
###     then stores the fitsFile data as CSV file
###     in CSV locatation
###
###  
@noOfArgs(2)
def fitsToCSV(fileName, csvLocation):
    def toCSV(fileHandle):
        data =  fileHandle.data
        np.savetxt(csvLocation, data, delimiter=",")
    readFits(fileName, toCSV)


def createFitFile(fitsHeader, fitsData, fileName):
    # hdu = fits.PrimaryHDU(data=fitsData, header=fitsHeader)
    # hdu.writeto(fileName)
    fits.writeto(fileName, fitsData, header=fitsHeader)


def createFitFileWithSameHeader(fitsData, fileName, fileToCopyHeaderFrom):
    with fits.open(fileToCopyHeaderFrom) as fd:
        headerToCopy = fd[0].header
        createFitFile(headerToCopy, fitsData, fileName)
