import os
import re
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path, PosixPath
from typing import Iterable, List, Union

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


def get_flats(folder: Path, image_duration=None) -> Iterable[PosixPath]:
    """
    Return a list of flat files in `folder` provided.
    Optionally looks for the name to contain `image_duration` only if
    `image_duration` is provided
    """
    result = folder.glob("*flat*.fit")
    if image_duration:
        result = filter(lambda x: f"{image_duration}" in x.name, result)
    return result


def get_darks(folder: Path, image_duration=None) -> Iterable[PosixPath]:
    """
    Return a list of dark files in `folder` provided
    Optionally looks for the name to contain `image_duration` only if
    `image_duration` is provided
    """
    result = folder.glob("*dark*.fit")
    if image_duration:
        result = filter(lambda x: f"{image_duration}" in x.name, result)
    return result


def get_all_fit_files(folder: Path, image_duration=None) -> Iterable[PosixPath]:
    """
    Return a list of all fit files in `folder` provided
    """
    result = folder.glob("*.fit")
    if image_duration:
        result = list(filter(lambda x: f"{image_duration}" in x.name, result))
    return result


def get_raw_images(folder: Path, image_duration=None) -> Iterable[RawImageFile]:
    """
    Return a list `RawImageFile` files in `folder` provided sorted asc. by image number
    Note that only filenames matching the naming convention of RawImageFile are returned
    """
    all_files = [RawImageFile(file.absolute()) for file in folder.glob("*.fit")]
    # Filter files whose filename don't match naming convention
    all_files = filter(lambda raw_image_file: raw_image_file.is_valid_file_name(), all_files)
    # Sort files by image number
    result = sorted(all_files, key=lambda raw_image_file: raw_image_file.image_number())
    if image_duration:
        result = list(filter(lambda x: x.image_duration() == image_duration, result))
    return result


def time_taken_to_capture_and_save_a_raw_file(folder_path: Path, night_config) -> int:
    """
    Returns the average time taken to capture the raw image.  Note that this
    may be different from the `image_duration` which is the time of camera
    exposure. This because it also takes some time to save the fit image.
    This function looks at the datetime of the first and the last raw image in
    `folder_path` and calculates the average time taken for an image.

    Raises
        Exception if no raw image is present in the given folder

    """
    raw_images: Iterable[RawImageFile] = list(get_raw_images(folder_path))
    first_img = raw_images[0]
    last_image = raw_images[-1]
    no_of_images = len(raw_images)
    if night_config.get("starttime") and night_config.get("endtime"):
        duration = (night_config.get("endtime") - night_config.get("starttime")).seconds
    else:
        duration = (last_image.datetime() - first_img.datetime()).seconds
    return duration / no_of_images


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


def half_round_up_to_int(num: float):
    # Python and IDL round up half numbers differently
    # In python round(1.5) is 2 while round(2.5) is 2
    # while in IDL all half numbers are rounded up
    # This function mimics IDL behaviour
    return int(Decimal(num).to_integral_value(rounding=ROUND_HALF_UP))


def customMedian(arr, *args, **kwargs):
    """
    Median similar to the default version of IDL Median
    https://github.com/LutherAstrophysics/python-helpers/issues/8
    """
    arr = np.array(arr)
    if len(arr) % 2 == 0:
        newArray = np.append(arr, [np.multiply(np.ones(arr[0].shape), np.max(arr))], axis=0)
        return np.median(newArray, *args, **kwargs)
    else:
        return np.median(arr, *args, **kwargs)


def sorted_by_number(lst: Iterable[Union[str, Path]]) -> Iterable[Union[str, Path]]:
    """
    Returns sorted list of `lst` where sorting is done in ascending order by the
    the first number present in the string. If no string is present, falls back
    to alphabetic sorting
    """
    # Note that this step is important if the `lst` passed is a generator
    # This is because, after we've read it once, it would be empty
    lst = list(lst)
    if not all([isinstance(x, str) or isinstance(x, Path) for x in lst]):
        raise ValueError("items of list must be either str or Path instance")
    # Get filename if path objects are given
    lst_path_normalized = [x if isinstance(x, str) else x.name for x in lst]
    # Sort by alphabet (secondary)
    alphabet_sorted = sorted(enumerate(lst_path_normalized), key=lambda x: x[1])
    # Sort by first number present in the
    MATCHER = re.compile(r"\D*(\d*).*")
    foo = zip(*list(sorted(alphabet_sorted, key=lambda x: int(MATCHER.match(x[1])[1] or 0))))
    indices, _ = foo
    return [lst[i] for i in indices]


__all__ = [
    "customMedian",
    "fitFilesInFolder",
    "rename",
    "get_closet_date",
    "raw_data_name_format",
    "sorted_by_number",
]
