def crop(matrix, row, column):
    return matrix[:row, :column]


def cropIntoRectangle(matrix, x, xLength, y, yLength):
    """
    Returns a cropped rectangle from the `matrix`
    @param matrix: matrix to crop
    @param x: xCoordinate to start crop
    @param xLength: length across first(x) axis
    @param y: yCoordinate to start crop
    @param yLength: length across second (y)axis

    @return a portion of the `matrix`
    """
    return matrix[x : x + xLength, y : y + yLength]
