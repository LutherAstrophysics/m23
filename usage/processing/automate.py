from index import main
from settings import oldCameraSettings, newCameraSettings

import os

### allNights is a tuple of input folder locations and output folder locations 
allNights = [
    (r"E:\Summer 2022\June 16, 2022", r"C:\Data Processing\xxx\Outputs\June 16, 2022"), 
    (r"E:\Summer 2022\June 17, 2022", r"C:\Data Processing\xxx\Outputs\June 17, 2022"), 
    (r"E:\Summer 2022\June 19, 2022", r"C:\Data Processing\xxx\Outputs\June 19, 2022"),
    (r"E:\Summer 2022\June 20, 2022", r"C:\Data Processing\xxx\Outputs\June 20, 2022"),
    (r"E:\Summer 2022\June 23, 2022", r"C:\Data Processing\xxx\Outputs\June 23, 2022"),
    (r"E:\Summer 2022\June 26, 2022", r"C:\Data Processing\xxx\Outputs\June 26, 2022"), 
    (r"E:\Summer 2022\June 29, 2022", r"C:\Data Processing\xxx\Outputs\June 29, 2022"),
    (r"E:\Summer 2022\July 1, 2022", r"C:\Data Processing\xxx\Outputs\July 1, 2022"),
    (r"E:\Summer 2022\July 9, 2022", r"C:\Data Processing\xxx\Outputs\July 9, 2022"),
    (r"E:\Summer 2022\July 17, 2022", r"C:\Data Processing\xxx\Outputs\July 17, 2022")
]

mySetting = newCameraSettings

for night in allNights:

    ### create output folder if it doesn't exist
    if not os.path.exists(night[1]):
        os.makedirs(night[1])
    
    mySetting.imagesFolderLocation = night[0]
    mySetting.outputLocation = night[1]
    try:
        main(mySetting)
    except Exception as e:
        print("Error in night", night)
        print("Continuing to other nights")
        pass