def surroundWith(npArray, size, value=0):
    """
    @param npArray: numpy array
    @param size: integer specifying the length of the edge
    @param value: (optional) value to surround with, 0 default

    Mutates the original array provided, npArray
    """
    # columns
    npArray[:, :size] = value
    npArray[:, -size:] = value

    # rows
    npArray[:size, :] = value
    npArray[-size:, :] = value
