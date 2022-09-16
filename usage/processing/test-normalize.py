import sys

from numpy import extract

if "../../" not in sys.path:
    sys.path.insert(0, "../../")

import os

from m23.norm import normalizeLogFiles

refFile = r"C:\Data Processing\RefImage\ref_revised_71.txt"

logFilesFolder = r"C:\Data Processing\xxx\June-12-Reprocessed_2\Log Files Combined"
allLogFiles = os.listdir(logFilesFolder)
logFilesFullName = [os.path.join(logFilesFolder, file) for file in allLogFiles]
normalizeLogFiles(
    refFile,
    logFilesFullName,
    r"C:\Data Processing\xxx\June-12-Reprocessed\PY Normalized RERUN",
)
