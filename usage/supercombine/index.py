###
### Boilerplate for local testing
import sys

if "../../" not in sys.path:
    sys.path.insert(0, "../../")

import os
import re

from m23.combine import imageCombination
from yaspin import yaspin


def nameAfterCombination(date, year, numberOfCombinations):
    return f"{year}-{date}-sc-{numberOfCombinations}.fit"


def allFilesList(folderPath):
    allFiles = os.listdir(folderPath)
    return list(
        filter(
            lambda x: x.endswith(".fit"),
            [os.path.join(folderPath, file) for file in os.listdir(folderPath)],
        )
    )


def processYear(yearLocation, year):
    allDates = list(filter(lambda x: re.search("\d", x), os.listdir(yearLocation)))
    for date in allDates:
        processDay(
            folderPath=os.path.join(yearLocation, date, "Aligned Combined"),
            saveAs=nameAfterCombination(
                date,
                year,
                len(os.listdir(os.path.join(yearLocation, date, "Aligned Combined"))),
            ),
            day=f"{date}-{year}",
        )


def processDay(folderPath, saveAs, day):
    try:
        names = allFilesList(folderPath)
        newFolderName = "C:\Data Processing\Supercombined Images"
        newNameExact = os.path.join(newFolderName, saveAs)
        with yaspin(text=f"processing data for {day}"):
            imageCombination(names, newNameExact)
    except Exception as e:
        print(f"Error proceesing {day} in {folderPath}")
        # raise e


def main():
    years = [
        ("C:\Data Processing\Summer 2021 M23", 2021),
        ("C:\Data Processing\Summer 2020 M23", 2020),
        ("C:\Data Processing\Summer 2019 M23", 2019),
        ("C:\Data Processing\Summer 2018 M23", 2018),
    ]
    for year in years:
        processYear(*year)


if __name__ == "__main__":
    main()
