# Checks which nights have flats/biases for a particular year
# For each particular day folder, inside the year folder
# traverses to the Calibration Frames folder and prints
# the number of flats and biases
from pathlib import Path

# Change this
yearFolderLocations = r"F:\Summer 2019"

# The code below is supposed to be static
def handleDay(dayPath: Path) -> tuple[int]:
    flats = list(dayPath.glob("Calibration Frames/flat*.fit"))
    biases = list(dayPath.glob("Calibration Frames/bias*.fit"))
    print(f"{dayPath.name:20s}{len(flats):^6}{len(biases):^6}")
    return len(flats), len(biases)


def main():
    root = Path(yearFolderLocations)
    print(f"{'Day':20s}{'Flats':^6s}{'Bias':^6s}")
    f_total, b_total = 0, 0
    for day in root.iterdir():
        f, b = handleDay(day)
        f_total += f
        b_total += b
    print(f"{'Total':20s}{f_total:^6}{b_total:^6}")


if __name__ == "__main__":
    main()
