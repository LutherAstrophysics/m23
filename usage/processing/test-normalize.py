import sys

from numpy import extract

if "../../" not in sys.path:
    sys.path.insert(0, "../../")

import os 
from m23.norm import normalizeLogFiles

refFile = r"C:\Data Processing\RefImage\ref_test.txt"

logFilesFolder = r"C:\Data Processing\xxx\Outputs\logs"
allLogFiles = sorted(os.listdir(logFilesFolder))
logFilesFullName = [os.path.join(logFilesFolder, file) for file in allLogFiles]
normalizeLogFiles(refFile, logFilesFullName, r"C:\Data Processing\xxx\Outputs\stars")