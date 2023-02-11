import cv2 as cv
import numpy as np

### fillMatrix
###
### this is a wrapper our open cv's fillPoly function
###
### params:
###   matrix: (2d) matrix to work with
###   polygons: array of array of tuples (x, y) defining a polygon fill region
###   fillValue: value to fill
###
### example:
###   matrix:  np.arange(50).reshape(2, 5, 5)[1]
###   pol1: [(0,0), (1,1), (0,4)]
###   pol2: [(4, 0), (3, 1), (4,4)]
###   polygons: [pol1, pol2]
###   fillValue: 0
###
### returns:
###    Mutated original matrix


def fillMatrix(matrix, polygons, fillValue) -> None:
    return cv.fillPoly(matrix, np.array(polygons), fillValue)
