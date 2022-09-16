import re


def nameAfterCalibration(nameToCalibrate):
    return re.sub(".fit$", "-calibrated.fit", nameToCalibrate)
