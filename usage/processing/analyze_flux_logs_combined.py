# This code is used to find which images were used
# for different nights when calculating flux logs combined.

# This can be used as a command line utlity by running as:
# python analyze_flux_logs.combined "F:/Summer 2019/"
# Or the analyze_year function can be imported to be run as a part
# of another program.
# Note that you might have to use forward slash instead of backward
# when passing folder location.

import sys
from datetime import datetime

### Boilerplate to be able to import m23
from typing import List, Tuple

if "../../" not in sys.path:
    sys.path.insert(0, "../../")

import argparse
import re
from pathlib import Path

from m23.file import formatWindowsPath


def analyze_year(
    folder_location: str, print_result=False
) -> List[Tuple[str, int | str, int | str]]:
    """
    Analyzes the flux logs for the given year at folder_location

    param folder_location: Folder location for a year
    print_result: Whether the result is to be printed

    return: The result of analysis
    """
    result = []

    # Make sure that the folder exists
    year_path = Path(folder_location)
    if not year_path.exists():
        if print_result:
            print("Folder doesn't exist")
            return
        else:
            raise FileNotFoundError("Invalid path for the year location")

    # Print header info
    if print_result:
        print(f"Year\t{year_path.name}")
        print(f"{'Night':<20s}{'Start':>10s}{'End':>10s}")
    for night in filter(lambda x: not x.is_file(), year_path.glob("*")):
        # Ignore if a not a folder
        if night.is_file():
            continue
        # Ignore if the folder name doesn't match a ceratin convention
        try:
            datetime.strptime(night.name, "%B %d")
        except ValueError:
            continue
        # Analyze the start, end image for each night
        # Read one of the star Flux Logs Combined Files for analysis
        try:
            file_to_read = list(night.glob(f"Flux Logs Combined*/Five Pixel Radius/*flux*"))[0]
        except IndexError as e:
            if print_result:
                print(
                    f"No matching Flux Logs Combined file found in",
                    formatWindowsPath(night.absolute()),
                )
                return
            else:
                raise e

        # Read the start image and end image value from file_to_read
        with file_to_read.open() as fd:
            fd.readline()  # Ignore the first line
            start = get_first_integer(fd.readline())
            end = get_first_integer(fd.readline())
            result.append((night.name, start, end))
            if print_result:
                print(f"{night.name:<20s}{str(start):>10s}{str(end):>10s}")
    return result


def get_first_integer(text_to_search: str) -> str | int:
    """
    Returns the first integer found in the search string, returns empty string otherwise
    """
    return (re.search(r"\d+", text_to_search) or "") and int(
        re.search(r"\d+", text_to_search).group()
    )


def main():
    parser = argparse.ArgumentParser(
        prog="Analyze Flux Logs Combined",
        description="Gives list of which images were used when calculating flux logs",
    )
    parser.add_argument("folder_location")  # positional argument
    parser.add_argument("-o", "--output", required=False)  # providing output location provides a verbose output
    args = parser.parse_args()
    result = analyze_year(args.folder_location, print_result=True)
    if output_folder := args.output:
        output_path = Path(output_folder)
        if not output_path.exists():
            print("output path", formatWindowsPath(output_path), "doesn't exist") 
            return
        for r in range(len(result)):
            result[r] = formatWindowsPath(output_path.joinpath("Flux Logs Combined"))


if __name__ == "__main__":
    main()
