class ProcessingSettings:
    def __init__(
        self,
        rows,
        columns,
        listOfPolygsToFill,
        polygonFillValue,
        noOfCombination,
        outputLocation,
        imagesFolderLocation,
        refImageLocation,
        refFilePath,
        name,
    ):
        self.rows = rows
        self.columns = columns
        self.listOfPolygonsToFill = listOfPolygsToFill
        self.polygonFillValue = polygonFillValue
        self.noOfCombination = noOfCombination
        self.outputLocation = outputLocation
        self.imagesFolderLocation = imagesFolderLocation
        self.refImageLocation = refImageLocation
        self.refFilePath = refFilePath
        self.name = name
                # self.name = name


    def __repr__(self):
        return f"Setting: {self.name}"

    def __str__(self):
        return self.__repr__()


NEW_CAMERA_CROP_REGION = [
    [(0, 2048 - 1600), (0, 0), (492, 0), (210, 2048 - 1867)],
    [(0, 1600), (0, 2048), (480, 2048), (210, 1867)],
    [(1400, 2048), (2048, 2048), (2048, 1500), (1834, 1830)],
    [(1508, 0), (1852, 241), (2048, 521), (2048, 0)],
]
NEW_CAMERA_IMAGE_HEIGHT = 2048
NEW_CAMERA_IMAGE_WIDTH = 2048

folderLocation = r"E:\Summer 2021\June 12, 2021"
outputFolderLocation = r"C:\Data Processing\xxx\June-12-Reprocessed"
noOfCombination = 10
referenceImagePath = (
    r"C:\Data Processing\RefImage\m23_3.5_071.fit" # This is the reference image 
                                                   # from 2003
)
referenceFilePath = (r"C:\Data Processing\RefImage\ref_revised_71.txt")

oldCameraSettings = ProcessingSettings(
    1024,
    1024,
    [],
    1,
    noOfCombination=noOfCombination,
    outputLocation=outputFolderLocation,
    imagesFolderLocation=folderLocation,
    refImageLocation=referenceImagePath,
    refFilePath=referenceFilePath,
    name="Old Camera Settings (< June 16 2022)",
)
newCameraSettings = ProcessingSettings(
    NEW_CAMERA_IMAGE_HEIGHT,
    NEW_CAMERA_IMAGE_WIDTH,
    NEW_CAMERA_CROP_REGION,
    1,
    noOfCombination=noOfCombination,
    outputLocation=outputFolderLocation,
    imagesFolderLocation=folderLocation,
    refImageLocation=referenceImagePath,
    refFilePath=referenceFilePath,
    name="New Camera Settings (>= June 16 2022)",
)

allSettings = [oldCameraSettings, newCameraSettings]

#### This is the setting that our data processing script uses
currentSettings = oldCameraSettings