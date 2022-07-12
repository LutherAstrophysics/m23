import sys
from turtle import register_shape

if "../../" not in sys.path:
    sys.path.insert(0, "../../")

from astropy.io.fits import getdata
import numpy as np
import astroalign as aa
from skimage.transform import SimilarityTransform


from m23.matrix.fill import fillMatrix
from m23.trans.fits import createFitFileWithSameHeader


a = r"C:\Data Processing\xxx\exp-old\combined-0-1.fit"
b = r"C:\Data Processing\xxx\exp-old-idl\m23_7.0-001.fit"
refImage = r"C:\Data Processing\RefImage\m23_3.5_071.fit"

newName = r"C:\Data Processing\xxx\exp-old\aligned-0-1.fit"


toTransform = getdata(a)
refData = getdata(refImage)

transf, (source_list, target_list) = aa.find_transform(toTransform, refData)

target_fixed = np.array(refData, dtype="<f4")
source_fixed = np.array(toTransform, dtype="<f4")

print(f"Sale was {transf.scale}")
newTransMatrix = SimilarityTransform(
    rotation=transf.rotation, translation=transf.translation, scale=transf.scale
)
registered_image, footprint = aa.apply_transform(newTransMatrix, source_fixed, target_fixed, fill_value=0)
createFitFileWithSameHeader(registered_image, newName, a)

idData = getdata(b)
pyData = getdata(newName)
def pos(x, y):
    print(f"IDL: {idData[x][y]}")
    print(f"Python: {pyData[x][y]}")