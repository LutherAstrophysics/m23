###
### Boilerplate
import sys

if "../../" not in sys.path:
    sys.path.insert(0, "../../")


from astropy.io.fits import getdata
import random

# new = r"C:\Data Processing\xxx\exp-old\Calibration Frames"
newcc = r"C:\Data Processing\xxx\Outputs\June 4, 2021\Aligned Combined"

# old = r"C:\Data Processing\xxx\exp-old-idl\Calibration frames"
oldcc = r"C:\Data Processing\xxx\exp-test-idl"


# ourflat = getdata(f"{new}\masterflat.fit")
# theirflat = getdata(f"{old}\masterflat_06-12-21.fit")

# ourdark = getdata(f"{new}\masterdark.fit")
# theirdark = getdata(f"{old}\masterdark.fit")

# ourbias = getdata(f"{new}\masterbias.fit")
# theirbias = getdata(f"{old}\masterbias.fit")


ourcc = getdata(f"{newcc}\combined-0-10.fit")
theircc = getdata(f"{oldcc}\m23_7.0-001.fit")

def examineMatrix(matrixA, matrixB, *positions):
    if len(positions) == 2:
        x, y = positions
    else:
        x, y = random.randrange(1024), random.randrange(1024)
    
    print(f"At position x, y {x} {y}")
    print(f"First: {matrixA[x][y]}")
    print(f"Second: {matrixB[x][y]}")


# def flat(*positions):
#     return examineMatrix(ourflat, theirflat, *positions)


# def dark(*positions):
#     return examineMatrix(ourdark, theirdark, *positions)


# def bias(*positions):
#     return examineMatrix(ourbias, theirbias, *positions)


def cc(*positions):
    return examineMatrix(ourcc, theircc, *positions)

