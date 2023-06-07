import logging
from typing import Iterable

import numpy as np

from m23.file.log_file_combined_file import LogFileCombinedFile


def get_star_to_ignore_bit_vector(  # noqa
    log_file_combined_file: LogFileCombinedFile, radius: int
) -> Iterable[int]:
    """
    Looks at the log_file_combined file and returns a bit vector representing
    whether that star should be ignored when calculating the norm factor for the
    night. We create this so that we can ignore stars at the edges which had a
    bright line at the edge after alignment step in old camera images. Note that
    in the bit vector, 0 means that star is to be avoided, 1 means the star is
    to be included.
    """
    y_coordinates = log_file_combined_file.get_x_position_column()
    x_coordinates = log_file_combined_file.get_y_position_column()

    night_date = log_file_combined_file.night_date()
    logger = logging.getLogger("LOGGER_" + str(night_date))

    # We now alter the x and the y values of the stars that don't have
    # any ADU value because we don't want to consider them as the stars in
    # the corners. Note that we reset this value after calculating stars to ignore
    stars_with_bogus_set = {}

    for index in range(len(log_file_combined_file.data())):
        star_no = index + 1
        star_data = log_file_combined_file.get_star_data(star_no)
        if not (
            star_data.sky_adu > 0 and all([adu > 0 for adu in star_data.radii_adu.values()])
        ):  # Note that some may be nan values
            # Set a bogus value on the star's x and y coordinate
            # so that it won't affect corner star calculation
            bogus = 512
            stars_with_bogus_set[star_no] = [x_coordinates[index], y_coordinates[index]]
            logger.debug(
                f"Intranight Linfit. Setting bogus x, y as {bogus} to star {star_no}. "
                + f"Found star data {star_data}. Logfile {log_file_combined_file}"
            )
            x_coordinates[index] = bogus
            y_coordinates[index] = bogus

    bit_vector = []

    # IDL and Python has axes reversed
    dist_from_top_left = np.sqrt(x_coordinates**2 + y_coordinates**2)
    dist_from_top_right = np.sqrt(x_coordinates**2 + (y_coordinates - 1023) ** 2)
    dist_from_bottom_left = np.sqrt((x_coordinates - 1023) ** 2 + y_coordinates**2)
    dist_from_bottom_right = np.sqrt((x_coordinates - 1023) ** 2 + (y_coordinates - 1023) ** 2)

    # indices of stars with least distances from four corners
    min_top_left = np.argmin(dist_from_top_left)
    min_top_right = np.argmin(dist_from_top_right)
    min_bottom_left = np.argmin(dist_from_bottom_left)
    min_bottom_right = np.argmin(dist_from_bottom_right)

    # star coordinates nearest to the four corners
    top_left_star = [x_coordinates[min_top_left], y_coordinates[min_top_left]]
    top_right_star = [x_coordinates[min_top_right], y_coordinates[min_top_right]]
    bottom_left_star = [x_coordinates[min_bottom_left], y_coordinates[min_bottom_left]]
    bottom_right_star = [
        x_coordinates[min_bottom_right],
        y_coordinates[min_bottom_right],
    ]

    # Fit linear lines to the four stars in the four corners, making a quadrilateral
    left_line = np.polyfit(
        [top_left_star[1], bottom_left_star[1]],
        [top_left_star[0], bottom_left_star[0]],
        1,
    )
    right_line = np.polyfit(
        [top_right_star[1], bottom_right_star[1]],
        [top_right_star[0], bottom_right_star[0]],
        1,
    )
    top_line = np.polyfit(
        [top_left_star[1], top_right_star[1]], [top_left_star[0], top_right_star[0]], 1
    )
    bottom_line = np.polyfit(
        [bottom_left_star[1], bottom_right_star[1]],
        [bottom_left_star[0], bottom_right_star[0]],
        1,
    )

    left_line_a, left_line_b = left_line

    def left_line_get_x(y):
        return (y - left_line_b) / left_line_a

    right_line_a, right_line_b = right_line

    def right_line_get_x(y):
        return (y - right_line_b) / right_line_a

    top_line_a, top_line_b = top_line

    def top_line_get_y(x):
        return top_line_a * x + top_line_b

    bottom_line_a, bottom_line_b = bottom_line

    def bottom_line_get_y(x):
        return bottom_line_a * x + bottom_line_b

    def should_include(point):
        y, x = point
        is_between_left_and_right_lines = (
            left_line_get_x(y) + 12 < x and right_line_get_x(y) - 12 > x
        )
        is_between_top_and_bottom = top_line_get_y(x) + 12 < y and bottom_line_get_y(x) - 12 > y
        return is_between_left_and_right_lines and is_between_top_and_bottom

    # We crop in 12 pixels from those four lines, and exclude stars that are
    # outside of this region
    x_and_y_coordinates = np.stack((x_coordinates, y_coordinates), axis=1)
    for star_position in x_and_y_coordinates:
        if should_include(star_position):
            bit_vector.append(1)
        else:
            bit_vector.append(0)

    # Cleanup
    # Reverse the x, y co-ordinates of the stars with where we set bogus co-ordinates
    for star, actual_coordinates in stars_with_bogus_set.items():
        actual_x, actual_y = actual_coordinates
        x_coordinates[star - 1] = actual_x
        y_coordinates[star - 1] = actual_y

    return bit_vector


def is_point_to_left_of_line(a, b, point):
    def eqn_y(x):
        return a * x + b

    def eqn_x(y):
        return (y - b) / a

    x, y = point
    x_prime = eqn_x(y)
    return x_prime > x
