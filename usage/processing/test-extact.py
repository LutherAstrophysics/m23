import sys

from numpy import extract

if "../../" not in sys.path:
    sys.path.insert(0, "../../")

import os 
from astropy.io.fits import getdata
from m23.extract import extractStars

refFile = r"C:\Data Processing\RefImage\ref_test.txt"
imageFolder = r"C:\Data Processing\xxx\exp-test-idl"

imageFiles = [os.path.join(imageFolder, rf"m23_7.0-0{number:02}.fit") for number in range(1, 2)]

def makeLogFileName(index):
    return os.path.join(r"C:\Data Processing\xxx\Outputs", f"{index + 1}.txt")

for index in range(len(imageFiles)):
    extractStars(getdata(imageFiles[index]), refFile, makeLogFileName(index))