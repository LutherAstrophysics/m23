from index import main
from settings import oldCameraSettings, newCameraSettings

import os
from datetime import datetime

### allNights is a tuple of length 2 or 3 of:
###     - input folder locations 
###     - output folder locations
###     - (optional) path to masteflat to use (in case the night doesn't have masterflat shot!) 
allNights = [
    (r"E:\Summer 2021\June 4, 2021", r"C:\Data Processing\xxx\Outputs\June 4, 2021", r"C:\Data Processing\Summer 2021 M23\June 12\Calibration Frames\masterflat_06-12-21.fit"), 
    (r"E:\Summer 2021\June 5, 2021", r"C:\Data Processing\xxx\Outputs\June 5, 2021", r"C:\Data Processing\Summer 2021 M23\June 12\Calibration Frames\masterflat_06-12-21.fit"), 
    (r"E:\Summer 2021\June 8, 2021", r"C:\Data Processing\xxx\Outputs\June 8, 2021", r"C:\Data Processing\Summer 2021 M23\June 12\Calibration Frames\masterflat_06-12-21.fit"),
    # (r"E:\Summer 2021\June 12, 2021", r"C:\Data Processing\xxx\Outputs\June 12, 2021"),
]

mySetting = oldCameraSettings

print(f"Starting automation script: {datetime.now()}")


for night in allNights:

    ### create output folder if it doesn't exist
    if not os.path.exists(night[1]):
        os.makedirs(night[1])
    
    mySetting.imagesFolderLocation = night[0]
    mySetting.outputLocation = night[1]

    ### set the alternatemasterflat if provided
    if len(night) > 2 :
        mySetting.alternateMasterFlat = night[2]

    try:
        main(mySetting)
    except Exception as e:
        print("Error in night", night)
        print(f"{e}")
        print("Continuing to other nights")
        pass

print(f"Finished {datetime.now()}")