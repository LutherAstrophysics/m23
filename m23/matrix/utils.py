### surroundWithZeros
###
### parameters:
###   npArray: numpy array
###   size: integer specifying the length of the edge
###   value: (optional) value to surround with, 0 default
###
###
### returns: None
###
### it mutates the original array provided, npArray
def surroundWith(npArray, size, value=0):

    # columns
    npArray[:, :size] = value
    npArray[:, -size:] = value

    # rows
    npArray[:size, :] = value
    npArray[-size:, :] = value
