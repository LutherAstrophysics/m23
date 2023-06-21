def blockRegions(arr, blockSize):
    """
    Taken from
    https://stackoverflow.com/questions/44782476/split-a-numpy-array-both-horizontally-and-vertically

    @param arr: numpy array to turn into blocks
    @param blockSize: tuple/array of rows/cols in a block
    """
    m, n = arr.shape
    M, N = blockSize
    return arr.reshape(m // M, M, n // N, N).swapaxes(1, 2).reshape(-1, M, N)
