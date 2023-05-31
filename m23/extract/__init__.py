import math
from functools import cache
from typing import Tuple

import numpy as np
import numpy.typing as npt
from m23.file.aligned_combined_file import AlignedCombinedFile
from m23.file.log_file_combined_file import LogFileCombinedFile
from m23.file.reference_log_file import ReferenceLogFile
from m23.matrix import blockRegions


def extract_stars(
    image_data: npt.NDArray,
    reference_log_file: ReferenceLogFile,
    radii_of_extraction,
    log_file_combined_file: LogFileCombinedFile,
    aligned_combined_file=AlignedCombinedFile,
):
    stars_centers_in_new_image = newStarCenters(image_data, reference_log_file)
    star_fluxes = {
        radius: flux_log_for_radius(radius, stars_centers_in_new_image, image_data)
        for radius in radii_of_extraction
    }
    no_of_stars = len(star_fluxes[radii_of_extraction[0]])

    log_file_combined_data: LogFileCombinedFile.LogFileCombinedDataType = {}
    for star_no in range(1, no_of_stars + 1):
        weighted_x = stars_centers_in_new_image[star_no - 1][0]
        weighted_y = stars_centers_in_new_image[star_no - 1][1]
        adu_per_pixel = star_fluxes[radii_of_extraction[0]][star_no - 1][1]

        star_FWHM = fwhm(image_data, weighted_x, weighted_y, adu_per_pixel)
        log_file_combined_data[star_no] = LogFileCombinedFile.StarLogfileCombinedData(
            x=weighted_y,  # IDL and Python have Axes reversed
            y=weighted_x,  # Note the axes are reversed by convention
            xFWHM=star_FWHM[1],  # Again, note the axes are reversed by IDL convention
            yFWHM=star_FWHM[0],
            avgFWHM=star_FWHM[2],
            # Note that star_fluxes[radius] is a list of 3 tuples
            # where the elements of the tuple are (total star flux, background flux, subtracted star flux)
            # Also note that we only write sky ADU for one of the radius of extraction
            # This is the usually just the first radius of extraction
            sky_adu=adu_per_pixel,  # Sky ADU from first of extraction
            radii_adu=(
                {radius: star_fluxes[radius][star_no - 1][2] for radius in radii_of_extraction}
            ),
        )
    log_file_combined_file.create_file(log_file_combined_data, aligned_combined_file)


def newStarCenters(imageData, reference_log_file: ReferenceLogFile):

    stars_x_positions_in_ref_file = reference_log_file.get_x_position_column()
    stars_y_positions_in_ref_file = reference_log_file.get_y_position_column()

    def centerFinder(position):
        x, y = position

        colWghtSum = 0
        rowWghtSum = 0
        WghtSum = 0
        for col in range(-5, 6):
            for row in range(-5, 6):
                if math.ceil(math.sqrt((col**2) + (row**2))) <= 5:
                    WghtSum += imageData[round(y) + row][round(x) + col]
                    colWghtSum += imageData[round(y) + row][round(x) + col] * (x + col)
                    rowWghtSum += imageData[round(y) + row][round(x) + col] * (y + row)

        if WghtSum > 0:
            xWght = colWghtSum / WghtSum
            yWght = rowWghtSum / WghtSum
        else:
            xWght = x
            yWght = y

        return yWght, xWght

    return [
        centerFinder([stars_x_positions_in_ref_file[i], stars_y_positions_in_ref_file[i]])
        for i in range(len(stars_x_positions_in_ref_file))
    ]


def flux_log_for_radius(radius: int, stars_center_in_new_image, image_data):
    """
    We need to optimize this code to work more efficiently with the caller function i.e extract_stars
    """
    regionSize = 64
    pixelsPerStar = np.count_nonzero(circleMatrix(radius))

    @cache
    def backgroundRegion():
        """
        Returns an array of arrays of 64x64 matrices
        """
        row, col = image_data.shape
        # Block in third row first column can be accessed by [2, 0]
        return blockRegions(image_data, (regionSize, regionSize)).reshape(
            row // regionSize, col // regionSize, regionSize, regionSize
        )

    @cache
    def backgroundAverage(backgroundRegionTuple: Tuple[int]):
        """
        Returns the average background in a region.
        Example, `backgroundRegionTuple` (2, 0) means the third row first column region.
        """
        row, column = backgroundRegionTuple
        region = backgroundRegion()[row][column]
        # Throw out the background of zeroes, since they might be at the edge
        sortedData = np.sort(region, axis=None)
        nonZeroIndices = np.nonzero(sortedData)
        # Ignore the zeros
        sortedData = sortedData[nonZeroIndices]

        centeredArray = sortedData[
            int(len(sortedData) // 2 - 0.05 * len(sortedData)) : int(
                len(sortedData) // 2 + 0.05 * len(sortedData)
            )
        ]
        return np.mean(centeredArray)

    def fluxSumForStar(position, radius) -> Tuple[int]:
        """
        This function returns the flux of of a star at specified `position` using
        `radius` as radius of extraction. Note that this tuple a three-tuple where
        the first, second, and third element correspond to total star flux, background flux
        and star flux after background subtraction respectively
        """
        x, y = position
        starBox = image_data[x - radius : x + radius + 1, y - radius : y + radius + 1]
        starBox = np.multiply(starBox, circleMatrix(radius))
        backgroundAverageInStarRegion = backgroundAverage((x // regionSize, y // regionSize))
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
        fluxSumForStar(np.round(position).astype("int"), radius)
        for position in stars_center_in_new_image
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
        col_sum += data[round(xweight) + axis, round(yweight)]
        row_sum += data[round(xweight), round(yweight) + axis]
        weighted_col_sum += (data[round(xweight) + axis, round(yweight)] - aduPerPixel) * (
            (round(xweight) + axis) - xweight
        ) ** 2
        weighted_row_sum += (data[round(xweight), round(yweight) + axis] - aduPerPixel) * (
            (round(yweight) + axis) - yweight
        ) ** 2
    col_sum = col_sum - (aduPerPixel * 11)
    row_sum = row_sum - (aduPerPixel * 11)
    xFWHM = 2.355 * np.sqrt(weighted_col_sum / (col_sum - 1))
    yFWHM = 2.355 * np.sqrt(weighted_row_sum / (row_sum - 1))
    average_FWHM = np.mean([xFWHM, yFWHM])
    return xFWHM, yFWHM, average_FWHM
