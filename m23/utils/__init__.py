import os
import re
from datetime import date, datetime
from pathlib import Path, PosixPath
from typing import Iterable, List

import numpy as np
from astropy.io.fits import getdata as getfitsdata
from numpy.typing import DTypeLike

from m23.constants import (
    INPUT_NIGHT_FOLDER_NAME_DATE_FORMAT,
    OUTPUT_NIGHT_FOLDER_NAME_DATE_FORMAT,
)
from m23.file.raw_image_file import RawImageFile

# local imports
from .rename import rename


def get_image_number_in_log_file_combined_file(file: Path) -> int:
    """
    Returns the image number log file combined file, or raises error if image number not found
    Examples:
        In the filename, 07-07-18_m23_7.0-112.txt, the image number is 112
    """
    results = re.findall(r"^.*-(\d+)\.txt", file.name)
    if len(results) == 0:
        raise ValueError(f"{file.name} is not in something-xxx.txt format")
    else:
        return int(results[0])


def get_image_number_in_fit_file(file: Path) -> int:
    """
    Returns the image number of the fit file, or raises error if image number not found
    Examples:
        In the filename, m23_7.0-010.fit, image number is 10
        More generally, In something-xxx.fit, integer representing xxx defines the image number
    """
    results = re.findall(r"^.*-(\d+)\.fit", file.name)
    if len(results) == 0:
        raise ValueError(f"{file.name} is not in something-xxx.fit format")
    else:
        return int(results[0])


def get_flats(folder: Path) -> Iterable[PosixPath]:
    """
    Return a list of flat files in `folder` provided
    """
    return folder.glob("*flat*.fit")


def get_darks(folder: Path) -> Iterable[PosixPath]:
    """
    Return a list of dark files in `folder` provided
    """
    return folder.glob("*dark*.fit")


def get_all_fit_files(folder: Path) -> Iterable[PosixPath]:
    """
    Return a list of all fit files in `folder` provided
    """
    return folder.glob("*.fit")


def get_raw_images(folder: Path) -> Iterable[RawImageFile]:
    """
    Return a list `RawImageFile` files in `folder` provided sorted asc. by image number 
    Note that only filenames matching the naming convention of RawImageFile are returned
    """
    all_files = [RawImageFile(file.absolute()) for file in folder.glob("*.fit")]
    # Filter files whose filename don't match naming convention
    all_files = filter(lambda raw_image_file : raw_image_file.is_valid_file_name(), all_files)
    # Sort files by image number
    return sorted(all_files, key=lambda raw_image_file: raw_image_file.image_number())



def get_radius_folder_name(radius: int) -> str:
    """
    Returns the folder name to use for a given radius pixel of extraction
    """
    radii = {
        1: "One",
        2: "Two",
        3: "Three",
        4: "Four",
        5: "Five",
        6: "Six",
        7: "Seven",
        8: "Eight",
        9: "Nine",
    }
    if result := radii.get(radius):
        return f"{result} Pixel Radius"
    else:
        return f"{radius} Pixel Radius"


def get_date_from_input_night_folder_name(name: str | Path) -> date:
    if issubclass(type(name), Path):
        name = name.name
    return datetime.strptime(name, INPUT_NIGHT_FOLDER_NAME_DATE_FORMAT).date()


def get_output_folder_name_from_night_date(night_date: date) -> str:
    return night_date.strftime(OUTPUT_NIGHT_FOLDER_NAME_DATE_FORMAT)


def fitFilesInFolder(folder, fileType="All"):
    allFiles = os.listdir(folder)
    fileType = fileType.lower()

    allFiles = list(filter(lambda x: x.endswith(".fit"), allFiles))
    if fileType == "all":
        return allFiles
    else:
        return list(filter(lambda x: x.__contains__(fileType), allFiles))


def fitDataFromFitImages(images):
    return [getfitsdata(item) for item in images]


def fit_data_from_fit_images(images: Iterable[str | Path]) -> List[DTypeLike]:
    return [getfitsdata(item) for item in images]


def get_log_file_name(night_date: date):
    return f"Night-{night_date}-Processing-log.txt"


### Similar to the default version of IDL Median
### https://github.com/LutherAstrophysics/python-helpers/issues/8
def customMedian(arr, *args, **kwargs):
    arr = np.array(arr)
    if len(arr) % 2 == 0:
        newArray = np.append(arr, [np.multiply(np.ones(arr[0].shape), np.max(arr))], axis=0)
        return np.median(newArray, *args, **kwargs)
    else:
        return np.median(arr, *args, **kwargs)


__all__ = [
    "customMedian",
    "fitFilesInFolder",
    "rename",
    "get_closet_date",
    "raw_data_name_format",
]
