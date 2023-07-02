import math
import warnings
from functools import cache
from typing import Tuple

import numpy as np


class SkyBgCalculator:
    # Something that always confused me is that position (x, y) in the reference
    # can be accessed from the image_data with image_data[y][x]

    @classmethod
    def get_box_number(cls, x: float, y: float) -> Tuple[int, int, int]:
        # We find out which sky background box the given co-ordinate falls under
        box_row, box_col = y // 128, x // 128
        small_box = (y - box_row * 128) // 32
        return box_row, box_col, small_box

    @classmethod
    def star_positions_circle_matrix(cls, x, y, radius):
        size = 2 * radius + 1
        matrix = [[1 for _ in range(size)] for _ in range(size)]
        matrix = np.multiply(matrix, circleMatrix(radius))
        matrix = matrix.astype("object")
        for row in range(-radius, radius + 1):
            for col in range(-radius, radius + 1):
                if matrix[row + radius][col + radius] != 0:
                    matrix[row + radius][col + radius] = (x + col, y + row)
        return matrix

    @classmethod
    def star_positions(cls, x, y, radius):
        matrix = cls.star_positions_circle_matrix(x, y, radius)
        return matrix.ravel()[np.flatnonzero(matrix)]

    def __init__(self, image_data) -> None:
        # This storage cache has to be image specific
        self.storage = {}
        self.image_data = image_data

    def get_image_data_at_box(self, box: Tuple[int, int, int]):
        row, col, small_box_number = [int(x) for x in box]
        start_row = row * 128
        start_col = col * 128
        return self.image_data[start_row : start_row + 128, start_col : start_col + 128][
            32 * small_box_number : 32 * (small_box_number + 1)
        ]

    def calculate_bg_at_position(self, x: float, y: float) -> float:
        """
        Returns the sky background at the given pixel position
        """
        # We divide the 1024*1024 image_data into boxes of size 128, 128. We further
        # strip the 128 sized square into four thin strips along the row then
        # calculate the sky background in that 32 * 128 (longer columns) by plotting
        # a 2nd degree polyfit to the values in that rectangular strip (only 10%
        # values from 40th to 50th percentile) as a function of their column number

        # This means that there will be a total of 8 big boxes across rows, 8 across
        # columns. In each of these 8 boxes, there will be 4 smaller rectangular
        # boxes.

        bg_box_number = self.get_box_number(x, y)
        if self.storage.get(bg_box_number) is None:
            bg_box = self.get_image_data_at_box(bg_box_number)
            list_of_x_position_and_adus = []
            for row in range(32):
                for col in range(128):
                    adu = bg_box[row][col]
                    if adu != 0:
                        list_of_x_position_and_adus.append((col, adu))

            # Sort list by ADU
            list_of_x_position_and_adus.sort(key=lambda x: x[1])
            # We now only keep 40%-55% percentile to do the fitting as anything
            # higher than that would most probably be stars, and lowers might be
            # black values
            length = len(list_of_x_position_and_adus)
            centered_array = list_of_x_position_and_adus[
                int(0.4 * length) : int(0.55 * length) + 1
            ]

            if len(centered_array) == 0:
                self.storage[bg_box_number] = lambda *args: 0
            else:
                x_to_plot, y_to_plot = zip(*centered_array)
                with warnings.catch_warnings():
                    warnings.filterwarnings("error")
                    try:
                        self.storage[bg_box_number] = np.poly1d(
                            np.polyfit(x=x_to_plot, y=y_to_plot, deg=2)
                        )
                    except np.linalg.LinAlgError:
                        # Use average in case of error. Is writing nan better so
                        # that we can ignore the star altogether?
                        # self.storage[bg_box_number] = lambda *args: np.mean(y_to_plot)
                        self.storage[bg_box_number] = lambda *args: np.nan
                    except np.RankWarning:
                        self.storage[bg_box_number] = lambda *args: np.nan
                    except RuntimeWarning:
                        self.storage[bg_box_number] = lambda *args: np.nan

        x_position_within_big_box = x - bg_box_number[1] * 128
        # The background at the given pixel given by the polynomial fit at the small
        # box Since the items stored in the storage_dict are those fit functions at
        # the respective boxes, we get the bg value by applying that function
        return self.storage[bg_box_number](x_position_within_big_box)

    def get_star_average_bg_per_pixel(self, x, y, radius):
        positions = self.star_positions(x, y, radius)
        adu_bg_sum = 0
        for position in positions:
            adu_bg_sum += self.calculate_bg_at_position(*position)
        return adu_bg_sum / len(positions)


@cache
def circleMatrix(radius):
    lengthOfSquare = radius * 2 + 1
    myMatrix = np.zeros(lengthOfSquare * lengthOfSquare).reshape(lengthOfSquare, lengthOfSquare)
    for row in range(-radius, radius + 1):
        for col in range(-radius, radius + 1):
            if math.ceil(math.sqrt((row) ** 2 + (col) ** 2)) <= radius:
                myMatrix[row + radius][col + radius] = 1
    return myMatrix
