###  Taken from https://stackoverflow.com/questions/44782476/split-a-numpy-array-both-horizontally-and-vertically
###
### arr is the numpy array to turn into blocks
### blockSize is the tuple/array of sizes
def blockRegions(arr, blockSize):
    # arr is input array, blockSizeis block-size
    m, n = arr.shape
    M, N = blockSize
    return arr.reshape(m // M, M, n // N, N).swapaxes(1, 2).reshape(-1, M, N)
