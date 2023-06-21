import math
from functools import cache
from typing import Tuple

import numpy as np
import numpy.typing as npt

from m23.constants import SKY_BG_BOX_REGION_SIZE
from m23.file.aligned_combined_file import AlignedCombinedFile
from m23.file.log_file_combined_file import LogFileCombinedFile
from m23.file.reference_log_file import ReferenceLogFile
from m23.matrix import blockRegions
from m23.utils import half_round_up_to_int


def sky_bg_average_for_all_regions(image_data, region_size):
    """
    Returns a dictionary of background average for all `region_size` sized
    square boxes in `image_data`
    """
    rows, cols = image_data.shape
    no_of_blocks_across_rows = rows // region_size
    no_of_blocks_across_cols = cols // region_size

    # Block in third row first column can be accessed by [2, 0]
    blocks = blockRegions(image_data, (region_size, region_size)).reshape(
        no_of_blocks_across_rows, no_of_blocks_across_cols, region_size, region_size
    )

    # This is a dictionary of background data in all regions The key to this
    # dictionary is the block region number represented as a tuple. For example
    # (1, 2) means second row, third column
    bg_data = {}

    for i in range(no_of_blocks_across_rows):
        for j in range(no_of_blocks_across_cols):
            region = blocks[i][j]
            # Throw out the background of zeroes, since they might be at the edge
            sorted_data = np.sort(region, axis=None)
            non_zero_indices = np.nonzero(sorted_data)
            # Ignore the zeros
            sorted_data = sorted_data[non_zero_indices]

            centered_array = sorted_data[
                int(0.45 * len(sorted_data)) : int(0.55 * len(sorted_data)) + 1
            ]
            bg_data[(i, j)] = np.mean(centered_array)

    return bg_data


def extract_stars(
    image_data: npt.NDArray,
    reference_log_file: ReferenceLogFile,
    radii_of_extraction,
    log_file_combined_file: LogFileCombinedFile,
    aligned_combined_file: AlignedCombinedFile,
    date_time_to_use: str = "",
):
    # We save the sky background in each `region_sized`(d)
    # square box of the image in the following
    sky_backgrounds = sky_bg_average_for_all_regions(image_data, SKY_BG_BOX_REGION_SIZE)

    stars_centers_in_new_image = newStarCenters(image_data, reference_log_file)

    star_fluxes = {
        radius: flux_log_for_radius(
            radius, stars_centers_in_new_image, image_data, sky_backgrounds, reference_log_file
        )
        for radius in radii_of_extraction
    }
    no_of_stars = len(star_fluxes[radii_of_extraction[0]])

    log_file_combined_data: LogFileCombinedFile.LogFileCombinedDataType = {}

    for star_no in range(1, no_of_stars + 1):
        weighted_x = stars_centers_in_new_image[star_no - 1][0]
        weighted_y = stars_centers_in_new_image[star_no - 1][1]

        #
        bg_adu_per_pixel = star_fluxes[radii_of_extraction[0]][star_no - 1][1]

        star_FWHM = fwhm(image_data, weighted_x, weighted_y, bg_adu_per_pixel)
        log_file_combined_data[star_no] = LogFileCombinedFile.StarLogfileCombinedData(
            x=weighted_y,  # IDL and Python have Axes reversed
            y=weighted_x,  # Note the axes are reversed by convention
            xFWHM=star_FWHM[1],  # Again, note the axes are reversed by IDL convention
            yFWHM=star_FWHM[0],
            avgFWHM=star_FWHM[2],
            # Note that star_fluxes[radius] is a list of 3 tuples
            # where the elements of the tuple are (total star flux, background
            # flux, subtracted star flux)
            # Also note that we only write sky ADU for one of the radius of extraction
            # This is the usually just the first radius of extraction
            sky_adu=bg_adu_per_pixel,  # Sky ADU from first of extraction
            radii_adu=(
                {radius: star_fluxes[radius][star_no - 1][2] for radius in radii_of_extraction}
            ),
        )
    log_file_combined_file.create_file(
        log_file_combined_data, aligned_combined_file, date_time_to_use
    )


def newStarCenters(imageData, reference_log_file: ReferenceLogFile):
    no_of_stars = len(reference_log_file)

    def centerFinder(star_no):
        x, y = reference_log_file.get_star_xy(star_no)

        colWghtSum = 0
        rowWghtSum = 0
        WghtSum = 0
        for col in range(-5, 6):
            for row in range(-5, 6):
                if math.ceil(math.sqrt((col**2) + (row**2))) <= 5:
                    WghtSum += imageData[half_round_up_to_int(y) + row][
                        half_round_up_to_int(x) + col
                    ]
                    colWghtSum += imageData[half_round_up_to_int(y) + row][
                        half_round_up_to_int(x) + col
                    ] * (x + col)
                    rowWghtSum += imageData[half_round_up_to_int(y) + row][
                        half_round_up_to_int(x) + col
                    ] * (y + row)

        if WghtSum > 0:
            xWght = colWghtSum / WghtSum
            yWght = rowWghtSum / WghtSum
        else:
            xWght = x
            yWght = y

        return yWght, xWght

    return [centerFinder(star_no) for star_no in range(1, no_of_stars + 1)]


def flux_log_for_radius(
    radius: int, stars_center_in_new_image, image_data, sky_backgrounds, ref: ReferenceLogFile
):
    """
    We need to optimize this code to work more efficiently with the caller
    function i.e extract_stars
    """
    regionSize = 64
    pixelsPerStar = np.count_nonzero(circleMatrix(radius))

    def fluxSumForStar(position, radius, star_no) -> Tuple[int]:
        """
        This function returns the flux of of a star at specified `position` using
        `radius` as radius of extraction. Note that this tuple a three-tuple where
        the first, second, and third element correspond to total star flux, background flux
        and star flux after background subtraction respectively
        """
        # x_exact, y_exact = position
        y_exact, x_exact = ref.get_star_xy(star_no)

        # Mimic IDL floor
        x, y = np.round(position).astype("int")
        starBox = image_data[x - radius : x + radius + 1, y - radius : y + radius + 1]
        starBox = np.multiply(starBox, circleMatrix(radius))
        backgroundAverageInStarRegion = sky_backgrounds[
            (x_exact // regionSize, y_exact // regionSize)
        ]
        subtractedStarFlux = np.sum(starBox) - backgroundAverageInStarRegion * pixelsPerStar

        # Convert to zero, in case there's any nan.
        # This ensures that two log files correspond to same star number as they are
        # or after reading with something like getLinesWithNumbersFromFile
        # This step makes our normalization code faster than the reslife code written in IDL!
        return (
            np.nan_to_num(np.sum(starBox)),
            np.nan_to_num(backgroundAverageInStarRegion),
            np.nan_to_num(subtractedStarFlux),
        )

    stars_fluxes = [
        fluxSumForStar(position, radius, index + 1)
        for index, position in enumerate(stars_center_in_new_image)
    ]
    return stars_fluxes


@cache
def circleMatrix(radius):
    lengthOfSquare = radius * 2 + 1
    myMatrix = np.zeros(lengthOfSquare * lengthOfSquare).reshape(lengthOfSquare, lengthOfSquare)
    for row in range(-radius, radius + 1):
        for col in range(-radius, radius + 1):
            if math.ceil(math.sqrt((row) ** 2 + (col) ** 2)) <= radius:
                myMatrix[row + radius][col + radius] = 1
    return myMatrix


def fwhm(data, xweight, yweight, aduPerPixel):
    col_sum = 0
    row_sum = 0
    weighted_col_sum = 0
    weighted_row_sum = 0
    for axis in range(-5, 6):
        col_sum += data[half_round_up_to_int(xweight) + axis, half_round_up_to_int(yweight)]
        row_sum += data[half_round_up_to_int(xweight), half_round_up_to_int(yweight) + axis]
        weighted_col_sum += (
            data[half_round_up_to_int(xweight) + axis, half_round_up_to_int(yweight)] - aduPerPixel
        ) * ((half_round_up_to_int(xweight) + axis) - xweight) ** 2
        weighted_row_sum += (
            data[half_round_up_to_int(xweight), half_round_up_to_int(yweight) + axis] - aduPerPixel
        ) * ((half_round_up_to_int(yweight) + axis) - yweight) ** 2
    col_sum = col_sum - (aduPerPixel * 11)
    row_sum = row_sum - (aduPerPixel * 11)
    xFWHM = 2.355 * np.sqrt(weighted_col_sum / (col_sum - 1))
    yFWHM = 2.355 * np.sqrt(weighted_row_sum / (row_sum - 1))
    average_FWHM = np.mean([xFWHM, yFWHM])
    return xFWHM, yFWHM, average_FWHM