import math
from functools import cache

import numpy as np

from m23.file import getLinesWithNumbersFromFile
from m23.matrix import blockRegions

# There are three methods of photometry
# 1. Aperture photometry: This is the method we use
# for the old camera, we create radii of 3, 4, 5 pixels around a star,
# and calculate its flux value
# 2. Profile photometry: TODO: This method was deemed
# inappropriate since the old images did not have
# as many pixels, but the new one have a lot more,
# so this is a method we want to try
# 3. Annular photometry


def newStarCenters(imageData, oldStarCenters):
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

    return [centerFinder(position) for position in oldStarCenters]


def extract_stars(
    image_data, reference_log_file_name, save_as, radii_of_extraction, image_name=None
):
    stars_positions_in_ref_file = starsPositionsInLogFile(reference_log_file_name)
    stars_centers_in_new_image = newStarCenters(image_data, stars_positions_in_ref_file)

    star_fluxes = {
        radius: flux_log_for_radius(radius, stars_centers_in_new_image, image_data)
        for radius in radii_of_extraction
    }
    no_of_stars = len(star_fluxes[radii_of_extraction[0]])

    # Create file
    with open(save_as, "w") as fd:
        # These 9 lines are to make sure it's the same format
        # as the old log files generated by IDL code
        fd.write("\n")
        fd.write(f"Star Data Extractor Tool: (Note: This program mocks format of AIP_4_WIN) \n")
        fd.write(f"\tImage {image_name or ''}:\n")
        fd.write(f"\tTotal no of stars: {no_of_stars}\n")
        fd.write(f"\tRadius of star diaphragm: {', '.join(map(str, radii_of_extraction))}\n")
        fd.write(f"\tSky annulus inner radius: \n")
        fd.write(f"\tSky annulus outer radius: \n")
        fd.write(f"\tThreshold factor: \n")

        headers = [
            "X",
            "Y",
            "XFWHM",
            "YFWHM",
            "Avg FWHM",
            "Sky ADU",
        ] + [f"Star ADU {radius}" for radius in radii_of_extraction]
        fd.write(
            f"{headers[0]:>16s}{headers[1]:>16s}{headers[2]:>16s}{headers[3]:>16s}{headers[4]:>16s}{headers[5]:>16s}{headers[6]:>16s}{headers[7]:>16s}{headers[8]:>16s}"
        )
        fd.write("\n")
        for star_index in range(no_of_stars):
            # We keep all stars in this step, filtering bad ones only in the normalization step
            data = (
                stars_centers_in_new_image[star_index][::-1]
                + (0, 0, 0)
                + (
                    star_fluxes[radii_of_extraction[0]][star_index][1],  # Sky ADU
                    star_fluxes[radii_of_extraction[0]][star_index][
                        2
                    ],  # Star ADU for first radius of extraction
                )
                + tuple(
                    [star_fluxes[i][star_index][2] for i in radii_of_extraction[1:]]
                )  # Star ADU for rest of the radii of extractions
            )
            fd.write(
                f"{data[0]:>16.2f}{data[1]:>16.2f}{data[2]:>16.4f}{data[3]:>16.4f}{data[4]:>16.4f}{data[5]:>16.2f}"
            )
            for star_adu in data[6:]:
                fd.write(f"{star_adu:>16.2f}")
            fd.write("\n")


def flux_log_for_radius(radius: int, stars_center_in_new_image, image_data):
    """
    TODO
    We need to optimize this code to work more efficiently with the caller function i.e extract_stars
    """

    regionSize = 64
    pixelsPerStar = np.count_nonzero(circleMatrix(radius))

    ###
    # return
    # an array of arrays of 64x64 matrices
    @cache
    def backgroundRegion():
        row, col = image_data.shape
        # block in third row first column can be accessed by [2, 0]
        return blockRegions(image_data, (regionSize, regionSize)).reshape(
            row // regionSize, col // regionSize, regionSize, regionSize
        )

    ###
    # backgroundRegionTuple is (2, 0) if referring to region in
    # third row, first column
    @cache
    def backgroundAverage(backgroundRegionTuple):
        row, column = backgroundRegionTuple
        region = backgroundRegion()[row][column]
        # throw out the background of zeroes, since
        # they might be at the edge
        sortedData = np.sort(region, axis=None)
        nonZeroIndices = np.nonzero(sortedData)
        # ignore the zeros
        sortedData = sortedData[nonZeroIndices]

        centeredArray = sortedData[
            int(len(sortedData) // 2 - 0.05 * len(sortedData)) : int(
                len(sortedData) // 2 + 0.05 * len(sortedData)
            )
        ]
        return np.mean(centeredArray)

    # starFlux
    #
    # return a three tuple
    # Total star flux + star pixels
    #   average background value for the star region
    #   star flux value after background subtraction
    def fluxSumForStar(position, radius):
        x, y = position
        starBox = image_data[x - radius : x + radius + 1, y - radius : y + radius + 1]
        starBox = np.multiply(starBox, circleMatrix(radius))
        backgroundAverageInStarRegion = backgroundAverage((x // regionSize, y // regionSize))
        subtractedStarFlux = np.sum(starBox) - backgroundAverageInStarRegion * pixelsPerStar
        ### Convert to zero, in case there's any nan... this ensures that
        ### two log files correspond to same star number as they are
        ### or after reading with something like getLinesWithNumbersFromFile
        ###
        ### This step makes our normalization code fast!
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
def starsPositionsInLogFile(fileName):
    linesWithNumbers = getLinesWithNumbersFromFile(fileName)
    # Assumes X and Y are the first two columns for the file
    ### NP WARNING
    ### IF dtype='float16' is specified, a number like '745.54' becomes 745.5
    ### Which means it gets rounded down, which is a HUGE problem if you're trying
    ### to match the output to IDL code
    ### So, we're using dtype='float'!!!
    return [np.array(line.split()[:2], dtype="float") for line in linesWithNumbers]


@cache
def circleMatrix(radius):
    lengthOfSquare = radius * 2 + 1
    myMatrix = np.zeros(lengthOfSquare * lengthOfSquare).reshape(lengthOfSquare, lengthOfSquare)
    for row in range(-radius, radius + 1):
        for col in range(-radius, radius + 1):
            if math.ceil(math.sqrt((row) ** 2 + (col) ** 2)) <= radius:
                myMatrix[row + radius][col + radius] = 1
    return myMatrix
