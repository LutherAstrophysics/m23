### This file how to use our rename module

### First use this following boilerplater like we do in all our code

import sys
if "../../" not in sys.path:
    sys.path.insert(0, "../../")

import re

### Now import our rename module
from m23.utils import rename

### define folder where you want to rename files
folder = r"C:\Data Processing\xxx\June-12-Reprocessed_2\Log Files Combined"

### write a renaming function, that takes a current name, and returs a new name
def newNameFromOldName(oldName):
    lastNumber = int(re.search("-.?\d*.txt$", oldName)[0][1:-4])
    return f"06-12-21_m23_7.0-{lastNumber:03}.txt"

rename(folder, newNameFromOldName, dry=False)