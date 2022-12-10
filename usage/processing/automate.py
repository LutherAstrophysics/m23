import os
from datetime import datetime

from index import main
from settings import newCameraSettings, oldCameraSettings

### allNights is a tuple of length 2 or 3 of:
###     - input folder locations
###     - output folder locations
###     - (optional) path to masteflat to use (in case the night doesn't have masterflat shot!)

# Please don't modify this file
# Copy the contents of this to my_automate.py in the same folder
# that this is in. Then run the script.
# This way this file can stay as a reference and don't need to be re-committed
# to git everytime someone call this for different night.

allNights = [
    (r"F:\Summer 2022\June 19, 2022", r"C:\Data Processing\June 19, 2022"),
    (
        r"F:\Summer 2022\June 16, 2022",
        r"C:\Data Processing\June 16, 2022",
        r"C:\Data Processing\June 19, 2022\Calibration Frames\masterflat.fit",
    ),
    (
        r"F:\Summer 2022\June 17, 2022",
        r"C:\Data Processing\June 17, 2022",
        r"C:\Data Processing\June 19, 2022\Calibration Frames\masterflat.fit",
    ),
    (
        r"F:\Summer 2022\June 20, 2022",
        r"C:\Data Processing\June 20, 2022",
        r"C:\Data Processing\June 19, 2022\Calibration Frames\masterflat.fit",
    ),
    (
        r"F:\Summer 2022\June 23, 2022",
        r"C:\Data Processing\June 23, 2022",
        r"C:\Data Processing\June 19, 2022\Calibration Frames\masterflat.fit",
    ),
    (
        r"F:\Summer 2022\June 26, 2022",
        r"C:\Data Processing\June 26, 2022",
        r"C:\Data Processing\June 19, 2022\Calibration Frames\masterflat.fit",
    ),
    (
        r"F:\Summer 2022\June 29, 2022",
        r"C:\Data Processing\June 29, 2022",
        r"C:\Data Processing\June 19, 2022\Calibration Frames\masterflat.fit",
    ),
    (
        r"F:\Summer 2022\July 1, 2022",
        r"C:\Data Processing\July 1, 2022",
        r"C:\Data Processing\June 19, 2022\Calibration Frames\masterflat.fit",
    ),
    (
        r"F:\Summer 2022\July 9, 2022",
        r"C:\Data Processing\July 9, 2022",
        r"C:\Data Processing\June 19, 2022\Calibration Frames\masterflat.fit",
    ),
    (
        r"F:\Summer 2022\July 17, 2022",
        r"C:\Data Processing\July 17, 2022",
        r"C:\Data Processing\June 19, 2022\Calibration Frames\masterflat.fit",
    ),
]

### set the camera settings to old or new
### depending on the data
mySetting = newCameraSettings

print(f"Starting automation script: {datetime.now()}")

### Start the automation process
###
for night in allNights:

    ### create output folder if it doesn't exist
    if not os.path.exists(night[1]):
        os.makedirs(night[1])

    mySetting.imagesFolderLocation = night[0]
    mySetting.outputLocation = night[1]

    ### set the alternatemasterflat if provided
    if len(night) > 2:
        mySetting.alternateMasterFlat = night[2]

    try:
        main(mySetting)
    except Exception as e:
        print("Error in night", night)
        print(f"{e}")
        print("Continuing to other nights")
        pass

print(f"Finished {datetime.now()}")
