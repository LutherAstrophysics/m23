### 
### Boilerplate for local testing
import sys
if '../../' not in sys.path: sys.path.insert(0, '../../')

### Begin
from m23.trans.fits import readFits 



def workWithFit(fd):
    # readFits calls this function

    # header
    # myHeader = fd.header

    # myData is a numpy array 
    # so you can do anything you can do with numpy array
    myData = fd.data

    middleRow = myData[len(myData) // 2]
    middleItem = middleRow[len(middleRow) // 2]

    print("middleItem", middleItem)

readFits("m23_7.0-001.fit", workWithFit)
