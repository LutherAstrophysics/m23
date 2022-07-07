### 
### Boilerplate for local testing
import sys
if '../../' not in sys.path: sys.path.insert(0, '../../')

### Begin
from m23.matrix import surroundWith 

import numpy as np


testMatrix = np.arange(500).reshape(5, 10, 10)[2]
print(testMatrix)
surroundWith(testMatrix, 3, 0)
print("\n"*5)
print(testMatrix)
