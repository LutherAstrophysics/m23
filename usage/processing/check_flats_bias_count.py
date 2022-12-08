# Checks which nights have flats/biases for a particular year
# For each particular day folder, inside the year folder
# traverses to the Calibration Frames folder and prints
# the number of flats and biases
from pathlib import Path

# Change this
yearFolderLocations = r"F:\Summer 2019"

# The code below is supposed to be static
def handleDay(dayPath: Path):
    flats = list(dayPath.glob("Calibration Frames/flat*.fit"))
    biases = list(dayPath.glob("Calibration Frames/bias*.fit"))
    print(f"{dayPath.name:20s}{len(flats):<6}{len(biases):<6}")


def main():
    root = Path(yearFolderLocations)
    print(f"{'Day':20s}{'Flats':6s}{'Bias':6s}")
    for day in root.iterdir():
        handleDay(day)
    pass


if __name__ == "__main__":
    main()
