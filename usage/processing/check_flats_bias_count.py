# Checks which nights have flats/biases for a particular year
# For each particular day folder, inside the year folder
# traverses to the Calibration Frames folder and prints
# the number of flats and biases
import argparse
from pathlib import Path

# Note that this is a command line utility, so you would run this as
# Running from the folder where this file is situated at
#
# python .\check_flats_bias_count.py 'F:/Summer 2022/'
# Also note the use of forward slash for foler location. If backward slash
# doesn't work in windows, use forward slash.

# The code below is supposed to be static
def handleDay(dayPath: Path) -> tuple[int]:
    flats = list(dayPath.glob("Calibration Frames/*flat*.fit"))
    biases = list(dayPath.glob("Calibration Frames/*bias*.fit"))
    print(f"{dayPath.name:20s}{len(flats):^6}{len(biases):^6}")
    return len(flats), len(biases)


def main(yearFolderLocation: str):
    root = Path(yearFolderLocation)
    print(f"{'Day':20s}{'Flats':^6s}{'Bias':^6s}")
    f_total, b_total = 0, 0
    for day in root.iterdir():
        f, b = handleDay(day)
        f_total += f
        b_total += b
    print(f"{'Total':20s}{f_total:^6}{b_total:^6}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="Check Flats Bias Count",
        description="Generates a list of count for no of flats, bias images for a year",
    )
    parser.add_argument("folder_location")  # positional argument, folder_locationmain()
    args = parser.parse_args()
    main(args.folder_location)
