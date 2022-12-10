# Renormalization is the step where we look at our Flux Logs Combined
# files to see which continious section of images for the night
# has good data, then we generate Flux Logs Combined using only those images
# for the night.

# This is a command line script that takes as input:
# 1. The folder location for the night.
#    Assumes the Log Files Combined are stored in folder: 'Log Files Combined'
#    Removes 'Flux Logs Combined' folder if already present, creates new set of
#    flux logs combined there.
# 2. Start image index
# 3. End image index
# Note that if start index is 5 and end is 15, images between 5-15 including 5, and 15
# will be used. This isn't going to actually use images but files from Log Files Combined.

# Usage

# The following tells to perfom normalization in the folder provided using images 15-40  (inclusive)
# It uses the default reference file, if not provied
#
# python .\re_normalize.py  'C:\Data Processing\2019 Python Processed\July 23, 2019' 15 40
#
# The reference file can be provided as:
#
# python .\re_normalize.py  'C:\Data Processing\2019 Python Processed\July 23, 2019' 1 2 -r 'F:\RefImage\ref_revised_71.txt'
#


### Boilerplate to be able to import m23
import sys

if "../../" not in sys.path:
    sys.path.insert(0, "../../")

import argparse
import logging
from operator import le
from pathlib import Path

from m23.file import formatWindowsPath
from m23.norm import normalizeLogFiles

default_reference_file = "C:/Data Processing/RefImage/ref_revised_71.txt"

# Helper function to clean up a directory
def remove_pathlib_folder(folder: Path):
    for f in folder.glob("*"):
        if f.is_file():
            f.unlink()
        else:
            # Call the function recursively
            remove_pathlib_folder(f)


def main():
    # Command line argument parsing
    parser = argparse.ArgumentParser(
        prog="Normalize",
        description="Generates normalized star flux using selected log files",
    )
    parser.add_argument("folder_location")  # positional argument, folder_location
    parser.add_argument("start", type=int)  # positional argument, image start index
    parser.add_argument("end", type=int)  # positional argument, image start index
    # Optional path to reference file, uses default if not provided
    parser.add_argument(
        "-r", "--reference", default=default_reference_file, required=False
    )  # option that takes a value

    args = parser.parse_args()

    # Error checking

    # Check if the main folder exists
    folder_path = Path(args.folder_location)
    if not folder_path.exists():
        print(
            f"Can't find folder, {folder_path.absolute()}",
        )
        return

    # Check for the Log Files Combined folder
    log_files_combined_path = folder_path.joinpath("Log Files Combined")
    if not log_files_combined_path.exists():
        print(
            f"Can't find log files combined in, {folder_path.absolute()}",
        )
        return

    # Check for bad start/end file index
    all_log_files = list(log_files_combined_path.glob("*m23*"))
    no_of_log_files = len(all_log_files)
    start_index = args.start
    end_index = args.end
    if not (start_index <= end_index <= no_of_log_files and start_index > 0):
        print(f"Bad image start, end index")
        print(
            f"Start provided : {start_index} End Provided : {end_index} No of logs found: {no_of_log_files}"
        )
        return

    # Check if reference file exists
    reference_file_path = Path(args.reference)
    if not reference_file_path.exists():
        print(f"Can't find the reference file, {args.reference}")
        return

    # If the Flux Logs Combined folder doesn't exist create
    radius_folder_path = folder_path.joinpath("Flux Logs Combined/5 Pixel Radius")
    if radius_folder_path.exists():
        # Clear the folder contents
        remove_pathlib_folder(radius_folder_path)
    else:
        radius_folder_path.mkdir(parents=True)

    # Assumming:
    # Ref file is good
    # Log files, start, end index good
    # Call normalization function

    # Get lsit of log files paths and convert to absolute file path
    list_of_log_files_to_use = list(
        map(formatWindowsPath, all_log_files[start_index - 1 : end_index])
    )
    ref_file = formatWindowsPath(reference_file_path)
    normalized_output_location = formatWindowsPath(radius_folder_path)

    # Setup logging
    logging.basicConfig(
        filename=f"{normalized_output_location}-log.txt",
        format="%(asctime)s %(message)s",
        level=logging.INFO,
    )

    logging.info(f"Using ref file {ref_file}")
    logging.info(f"Using log files: {start_index} - {end_index}")
    for x in list_of_log_files_to_use:
        logging.info(f"\t:{x}")
    logging.info(f"Performing normalization")
    try:
        normalizeLogFiles(
            ref_file, list_of_log_files_to_use, normalized_output_location, start_index, end_index
        )
    except Exception as e:
        logging.error(f"There was an error during nomralization \n{e}")
        print(e)
    logging.info(f"Normalization completed")


if __name__ == "__main__":
    main()
