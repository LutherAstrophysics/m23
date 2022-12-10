# Constructs the allNights list used by automate.py
# Does the following

# Finds which nights don't have flats and thus would need
#   to use master flat from the processing of other nights.
#   Picks the closes night if there there are more than 1 neighbor
#   nights to choose the master flat from.

# Orders the allNights list such that the nights that have flats
#   are processed first so that nights that need master flat from other
#   night can use the master flat generated from its processing.

# Needs
# Input folder root location (the year folder)
# The root outer folder location where all the days folders are to be created

### Boilerplate to be able to import from m23
import pprint
import sys

if "../../" not in sys.path:
    sys.path.insert(0, "../../")

# Note that this script might only work in windows
from pathlib import Path, WindowsPath
from re import I
from typing import List

from m23.file import formatWindowsPath
from m23.utils import get_closet_date

# Change this
yearFolderLocation = r"F:\Summer 2019"
outputFolderLocation = r"C:\Data Processing\2019 Python Processed"

DayLikeName = str

# The code below is supposed to be static
def getAllNightsList(yearFolderLocation, outputFolderLocation):
    root = Path(yearFolderLocation)
    allNights = []
    for day in root.iterdir():
        night = formatWindowsPath(day.absolute()), formatWindowsPath(
            Path(outputFolderLocation).joinpath(day.name)
        )
        allNights.append(night)
    # Order the nights by the number of flats they have, desc
    # This ensures that the nights with flats will be processed first
    # so that nights that need flats will be able to use the flats generated from them
    def get_number_of_flats(dayPathString: str):
        dayPath = Path(dayPathString)
        return len(list(dayPath.glob("Calibration Frames/*flat*.fit")))

    # Create a map from day to noOfFlats in that night
    flats_map = {x[0]: get_number_of_flats(x[0]) for x in allNights}

    # Order by number of flats
    allNights.sort(key=lambda x: get_number_of_flats(x[0]), reverse=True)

    # Add flats to nights that don't have flats
    # Add the master flat from the closest night that has flats data

    # Create a list of nights with flats
    nightsWithFlats = []
    index = 0
    while index < len(allNights) and flats_map[allNights[index][0]] > 0:
        nightsWithFlats.append(Path(allNights[index][0]).name)
        index += 1

    # Raise exception if no nights in the range have flats data
    if index == 0 and len(allNights) != 0:
        raise Exception("Looks like no nights have flats data")

    # Add alternate masterflat for the remaining nights
    def get_closest_night(nightsWithFlats: List[DayLikeName], day: DayLikeName):
        return get_closet_date(base_date=day, list_of_dates=nightsWithFlats, format="%B %d, %Y")

    def make_flat_path_from_night(day: DayLikeName):
        # Returns the filepath where the master flat file will be stored
        return formatWindowsPath(
            Path(outputFolderLocation).joinpath(f"{day}/Calibration Frames/masterflat.fit")
        )

    for night in allNights[index:]:
        closest_night_with_flat = get_closest_night(nightsWithFlats, Path(night[0]).name)
        # Add new tuple
        allNights[index] = *allNights[index], make_flat_path_from_night(closest_night_with_flat)
        index += 1
    return allNights


def main():
    pp = pprint.PrettyPrinter(width=100, compact=True)
    pp.pprint(getAllNightsList(yearFolderLocation, outputFolderLocation))


if __name__ == "__main__":
    main()
