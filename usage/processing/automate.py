from index import main
from settings import oldCameraSettings, newCameraSettings

import os
import datetime

### allNights is a tuple of input folder locations and output folder locations 
allNights = [
    (r"E:\Summer 2021\June 4, 2021", r"C:\Data Processing\xxx\Outputs\June 4, 2021"), 
    (r"E:\Summer 2021\June 5, 2021", r"C:\Data Processing\xxx\Outputs\June 5, 2021"), 
    (r"E:\Summer 2021\June 8, 2021", r"C:\Data Processing\xxx\Outputs\June 8, 2021"),
    (r"E:\Summer 2021\June 12, 2021", r"C:\Data Processing\xxx\Outputs\June 12, 2021"),
]

mySetting = oldCameraSettings

print(f"Starting {datetime.now}")
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

print(f"Finished {datetime.now}")