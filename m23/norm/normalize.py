import sys

if "../../" not in sys.path:
    sys.path.insert(0, "../../")

import os

### external libraries
import numpy as np

### m23 imports
from m23.file import getLinesWithNumbersFromFile

###
### Function: normalizeLogFiles
###
### Takes in reference file name, log files names to normalize
### and folder path to save the new files in
### 
### Produces a normalization.txt file and Flux Logs combined folder
### with nomralized files in the saveFolder
###
### BIG ASSUMPTION!!!!
### We assume that noOfStars in all log files is the same as no of stars in
### reference file. This is the case if the log files were produced using extraction 
### module in this library. However, in case of log files produced by previous IDL code
### this was't true. This is also one of the reasons, this normalizaion code might be
### faster than the IDL version.
### 
###
def normalizeLogFiles(referenceFileName, logFilesNamesToNormalize, saveFolder):

    ### Wrapper around the function so we don't 
    ### have to keep passing the saveFolder as argument
    saveFileInFolder = lambda *args, **kwargs : saveFileInFolder(saveFolder, *args, **kwargs)
    
    ### COLUMN_NUMBERS (0 means first column)
    ref_adu_column = 5
    logfile_adu_column = 4
    ref_positions_xy = (0, 1)
    logfile_positions_xy = (0, 1)

    def aduInLogData(logData):
        return [line.split()[logfile_adu_column] for line in logData]

    referenceData = getLinesWithNumbersFromFile(referenceFileName)
    logFilesData = [getLinesWithNumbersFromFile(logFileName) for logFileName in logFilesNamesToNormalize]

    ### At this point, if we want to look at 300-th star in our first image 
    ### we would do logFilesData[0][299] (beware of python index starting from 0)
    noOfFiles = len(logFilesData)
    ### Normalization is done with reference to images 20%, 40%, 60% and 80% through night
    indicesToNormalizeTo = np.floor(np.array([noOfFiles * sample for sample in [0.2, 0.4, 0.6, 0.8]]))
    data_to_normalize_to = np.array(logFilesData)[indicesToNormalizeTo]
    adus_in_data_to_normalize_to = aduInLogData(data_to_normalize_to)

    ### matrix of image by star
    ### so 4th star in 100th image will be 
    ### normalized_star_data[99][3]
    normalized_star_data = np.zeros((noOfFiles, len(referenceData)))

    ### find normalization factor for each file
    allNormFactors = []
    for file_index in range(len(noOfFiles)):
        ### Normalization factor is the median of the scaleFactors of all stars for scaleFactors < 5
        ### where scaleFactor for a star for that image is the ratio of that star's adu in 
        ### sum of data_to_normalize_to / 4 * adu in current image

        adu_of_current_log_file = aduInLogData(logFilesData[file_index])
        
        ### Find normalization factor
        scale_factors_for_stars = np.sum(adus_in_data_to_normalize_to, axis=0)/4*adu_of_current_log_file
        normFactor = np.median(np.where(scale_factors_for_stars < 5))

        allNormFactors.append(normFactor)
        
        normalized_star_data[file_index] = normFactor * np.array(logFilesData[file_index])

    ### Save the norm factor dot txt

    ### Save the normalized data for each star


