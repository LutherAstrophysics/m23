from dataclasses import dataclass, replace

@dataclass
class ProcessingSettings:
    rows: int
    columns: int
    listOfPolygonsToFill: list
    polygonFillValue: int
    noOfCombination: int
    outputLocation: str
    imagesFolderLocation: str
    refImageLocation: str
    refFilePath: str
    name: str
    alternateMasterFlat: str
    radius: int

    def __repr__(self):
        return f"Setting: {self.name}"

    def __str__(self):
        return self.__repr__()


### These are the settings you need to 
### change, they include: 
###  input and output folders, number of images per combination,
###  reference image and file paths, and the radius of extraction
folderLocation = r"F:\Summer 2021\March 19, 2021"
outputFolderLocation = r"C:\Data Processing\March 19, 2021"
noOfCombination = 10
referenceImagePath = (r"F:\RefImage\m23_3.5_071.fit")
referenceFilePath = (r"F:\RefImage\ref_revised_71.txt")
radiusOfExtraction = 5

### path to the master flat to use if the night 
### does not have flat frames
alternateMasterFlat = r"C:\Data Processing\June 12, 2021\Calibration Frames\masterflat.fit"

oldCameraSettings = ProcessingSettings(
    rows=1024, 
    columns=1024, 
    listOfPolygonsToFill=[], 
    polygonFillValue=1,
    noOfCombination=noOfCombination, 
    outputLocation=outputFolderLocation,
    imagesFolderLocation=folderLocation,
    refImageLocation = referenceImagePath,
    refFilePath=referenceFilePath,
    name= "Old Camera Settings  (< June 16 2022)",
    alternateMasterFlat=alternateMasterFlat,
    radius=radiusOfExtraction)

### Settings for the new camera
NEW_CAMERA_CROP_REGION = [
    [(0, 2048 - 1600), (0, 0), (492, 0), (210, 2048 - 1867)],
    [(0, 1600), (0, 2048), (480, 2048), (210, 1867)],
    [(1400, 2048), (2048, 2048), (2048, 1500), (1834, 1830)],
    [(1508, 0), (1852, 241), (2048, 521), (2048, 0)],
]

newCameraSettings = replace(oldCameraSettings)
newCameraSettings.rows = 2048
newCameraSettings.columns = 2048
newCameraSettings.listOfPolygonsToFill = NEW_CAMERA_CROP_REGION
newCameraSettings.name = "New Camera Settings (>= June 16 2022)"


###
### list of all processing settings
###
allSettings = [oldCameraSettings, newCameraSettings]


###
### This is the setting that our data processing script uses
###
currentSettings = oldCameraSettings