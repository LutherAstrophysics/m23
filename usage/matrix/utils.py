###
### Boilerplate for local testing
import sys

if "../../" not in sys.path:
    sys.path.insert(0, "../../")

import numpy as np
### Begin
from m23.matrix import surroundWith

testMatrix = np.arange(500).reshape(5, 10, 10)[2]
print(testMatrix)
surroundWith(testMatrix, 3, 0)
print("\n" * 5)
print(testMatrix)
