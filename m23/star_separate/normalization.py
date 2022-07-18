import sys

if "../../" not in sys.path:
    sys.path.insert(0, "../../")

import os
import math

### m23 imports
from m23.file import getLinesWithNumbersFromFile


###
### takes referenceLogFile and logFilesToNormalize
###   and produces normfactors.txt and normalized Flux Logs Combined
###
### approach
###   we normalize each log file, and use it to constrcut Flux Logs Combined
###   for all the stars in the referenceLogFile


def normalize(referenceLogFile, logFilesToNormalize, savePath):

    ### 
    ### finds matching stars in
    ### reference log file and logFile
    ### 
    ### Note: Matching means the centers are not 
    ### more than 1 pixel apart
    ###
    ### return an array of tuples of indices in
    ###   the reference file and the current log file in that order
    ### example:
    ###   [(300, 250), (100, 600)]

    def starMatcher(refFileData, logFileData, shiftThreshold=1):
        matches = []
        logFilePositions = [line.strip()[:2] for line in logFileData]
        refFilePositions = [line.strip()[:2] for line in refFileData]
        for logIndex in range(len(logFilePositions)):
            position = logFilePositions[logIndex]
            xLogFile, yLogFile = position
            refIndex = 0
            found = False
            while refIndex < len(refFilePositions) and not found:
                xRefFile, yRefFile = refFilePositions[refIndex]
                difference_x = abs(xLogFile - xRefFile)
                difference_y = abs(yLogFile - yRefFile)
                found = math.sqrt(difference_x ** 2 + difference_y ** 2) < shiftThreshold 
                if found:
                    matches.append(refIndex, logIndex)
                refIndex += 1
        return matches

    def normalizeLogFile(logFileToNormalize, checkLogFilesData):
        ### raises and error if there aren't four items in checkLogFiles
        assert len(checkLogFilesData) == 4
        firstCheck, secondCheck, thirdCheck, fourthCheck = checkLogFilesData
        # sumOfCheck = 
        normalizationFactor = 1
        return normalizationFactor

    ### saves file in the correct path
    def saveFile(fileName, arrayOfHeaders, arrayOfData):
        with open(os.path.join(savePath, fileName), "w") as fd:
            for header in arrayOfHeaders + arrayOfData:
                fd.write(str(header) + "\n")

    ### logFilesData
    logFilesArray = [
        getLinesWithNumbersFromFile(logFile) for logFile in logFilesToNormalize
    ]

    ### check log files used for normalization (default is every 20% of the night)
    checkLogFilesData = [
        logFilesArray[
            math.floor(len(logFilesArray) * 0.2),
            math.floor(len(logFilesArray) * 0.4),
            math.floor(len(logFilesArray) * 0.6),
            math.floor(len(logFilesArray) * 0.8),
        ]
    ]
    all_normalization_factors = [normalizeLogFile(logFile) for logFile in logFilesArray]

    ### create normalization file
    saveFile("normalization.txt", [], all_normalization_factors)

    ### get data from reference log file
    referenceLogFileData = getLinesWithNumbersFromFile(referenceLogFile)

    ### generate header info for Flux Logs combined for a particular star
    def getStarHeader(star_no):
        referenceLogForThisStar = referenceLogFileData[
            star_no - 1
        ].split()  # -1 because stars are named from 1 not 0
        xLocation, yLocation = referenceLogForThisStar[:2]
        return [
            f"X Location: {xLocation}",
            f"Y Location: {yLocation}",
        ]

    ### generates stars ADU normalized
    def getStarADUNormalized(star_index, logFilesData):
        currentStarLogFileData = logFilesData[
            star_index - 1
        ]  # -1 because stars are named from 1 not 0
        all_adu_normalized = []
        for image_index in range(len(currentStarLogFileData.images)):
            adu_in_image_index = currentStarLogFileData.images[image_index].adu
            all_adu_normalized.append(
                adu_in_image_index * all_normalization_factors[image_index]
            )
        return all_adu_normalized

    ### start with star 1 instead of 0 (beware of python range defaults)
    for star_index in len(range(1, referenceLogFileData + 1)):

        starHeaders = getStarHeader(star_index)
        starFluxNormalized = getStarADUNormalized(star_index)

        saveFile(f"{star_index}_flux.txt", starHeaders, starFluxNormalized)
