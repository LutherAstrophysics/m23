import numpy as np


def crop(matrix, row, column):
    return matrix[:row, :column]


### cropIntoRectangle
###
### parameters:
###   matrix: a numpy array
###   x: xCordinate to start crop
###   xLength: length across first axis
###   y: yCordiate to start crop
###   yLength: length across second (y) axis
###
### returns
###   cropped rectangle
def cropIntoRectangle(matrix, x, xLength, y, yLength):
    return matrix[x : x + xLength, y : y + yLength]
