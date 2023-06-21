import numpy as np

from m23.matrix import blockRegions, fillMatrix


def test_block_regions():
    # We test splitting a matrix vertically into horizontally
    # ----------------------------
    # | 0   1   2   3   4  5  6  7 |
    # | 8   9  10  11  12 13 14 15 |
    # | 16 17  18  19  20 21 22 23 |
    # | 24 25  26  27  28 29 30 31 |
    # -----------------------------
    # If we were to split the matrix above into 2, 2 boxes,
    # we would expect to see
    # ------  -------
    # | 0 1 | 2   3 |....
    # | 8 9 | 10 11 |....
    # ------  ---------
    # | 16 17 | 18 19 |
    # | 24 25 | 26 27 |
    # ------  ---------
    rows, cols = 4, 8
    matrix = np.arange(rows * cols).reshape(rows, cols)
    box_rows, box_cols = 2, 2
    boxes = blockRegions(matrix, (box_rows, box_cols))
    assert len(boxes) == rows // box_rows * cols // box_cols
    # Boxes is a flat array holding each box
    # we make it multi-dimensional now
    boxes_multidim = boxes.reshape(rows // box_rows, cols // box_cols, box_rows, box_cols)
    assert (boxes_multidim[1][0] == np.array([[16, 17], [24, 25]])).all()


def test_fill_matrix():
    rows, cols = 10, 10
    matrix = np.arange(rows * cols).reshape(rows, cols)
    # We test splitting a matrix vertically into horizontally
    # ----------------------------
    # | 0   1   2   3   4  5  6  7 |
    # | 8   9  10  11  12 13 14 15 |
    # | 16 17  18  19  20 21 22 23 |
    # | 24 25  26  27  28 29 30 31 |
    # -----------------------------
    # Let's test cropping a section of the matrix to turn it into
    # ----------------------------
    # | 0   1   2   3   4  5  6  7 |
    # | 8          11  12 13 14 15 |
    # | 16         19  20 21 22 23 |
    # | 24 25  26  27  28 29 30 31 |
    # -----------------------------
    polygon = [
        (0, 1),
        (5, 1),
        (3, 3),
        (0, 1),
    ]
    # Fill with 0
    polygons = [polygon]
    fillMatrix(matrix, polygons, 1000)
    assert matrix[1,1] == 1000

