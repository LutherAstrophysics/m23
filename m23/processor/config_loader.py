import os
import sys
from functools import reduce
from pathlib import Path
from typing import Callable, Dict, List, NotRequired, TypedDict

import toml

from m23.constants import CALIBRATION_FOLDER_NAME, M23_RAW_IMAGES_FOLDER_NAME
from m23.utils import (
    get_all_fit_files,
    get_date_from_input_night_folder_name,
    get_raw_darks,
    get_raw_flats,
)


# TYPE related to Config object described by the configuration file
class ConfigImage(TypedDict):
    rows: int
    columns: int
    crop_region: NotRequired[List[List[int]]]


class ConfigProcessing(TypedDict):
    no_of_images_to_combine: int
    radii_of_extraction: List[int]


class ConfigInputNight(TypedDict):
    path: str
    masterflat: NotRequired[str]


class ConfigInput(TypedDict):
    nights: List[ConfigInputNight]
    radii_of_extraction: List[int]


class ConfigOutput(TypedDict):
    path: str


class Config(TypedDict):
    image: ConfigImage
    processing: ConfigProcessing
    input: ConfigImage
    output: ConfigOutput


b = Path("./brown.toml")
r = Path("./rainbow.toml")


def is_valid_radii_of_extraction(lst):
    """Verifies that each radius of extraction is a positive integer"""
    is_valid = all([type(i) == int and i > 0 for i in lst])
    if not is_valid:
        sys.stdout.write("Radius of extraction must be positive integers\n")
    return is_valid


def load_defaults(config_dict: Config) -> Config:
    """
    Mutates `config_dict` with default values if optional values aren't provided
    """
    # Add empty list as the crop region if not present
    if not config_dict["image"].get("crop_region"):
        config_dict["image"]["crop_region"] = []

    return config_dict


def sanity_check(config_dict: Config) -> Config:
    """
    This method performs any sanity checks on the configuration file.
    """

    def prompt_to_continue(msg: str):
        sys.stdout(f"{msg}\n")
        response = input("Do you want to continue (y/yes to continue): ")
        if response.upper() not in ["Y", "YES"]:
            os._exit(1)

    # Ensure sane values for rows/cols, etc.
    SANE_ROWS = [1024, 2048]
    SANE_COLS = [1024, 2048]
    if config_dict["image"]["columns"] not in SANE_COLS:
        prompt_to_continue(
            f"Unusual values for no of columns provided in configuration file. Value: {config_dict['image']['columns']}"
        )
    if config_dict["image"]["rows"] not in SANE_ROWS:
        prompt_to_continue(
            f"Unusual values for no of rows provided in configuration file. Value: {config_dict['image']['rows']}"
        )

    # Make sure that we're using only processing old camera nights or new camera nights
    # and that we're using corresponding settings like no.of.rows/cols etc.

    return config_dict


def verify_optional_image_options(options: Dict) -> bool:
    """
    Verifies that the optional image options are valid
    """
    if len(options.keys()) > 1:
        return False
    crop_region: List[List[int]] = options.get("crop_region", [])
    # Ensure that all values in crop_region are non-negative integers
    values: List[int] = reduce(lambda prev, curr: prev + curr, crop_region, [])
    is_valid = all([type(i) == i and i >= 0 for i in values])
    if not is_valid:
        sys.stdout.write("Crop region must be an array of array of integers >= 0\n")
    return is_valid


def validate_night(night: ConfigInputNight) -> bool:
    """
    Checks whether the input configuration provided for night is valid.
    We check whether the input folders follow the required conventions,
    whether the right files are present and more.
    """
    NIGHT_INPUT_PATH = Path(night["path"])
    # Check if the night input path exists
    if not NIGHT_INPUT_PATH.exists():
        sys.stdout(f"Images path for {night} doesn't exist")
        return False

    # Check if the name of input folder matches the convention
    try:
        get_date_from_input_night_folder_name(NIGHT_INPUT_PATH.name)
    except:
        sys.stdout(f"Night {night} folder name doesn't match the naming convention")
        return False

    CALIBRATION_FOLDER_PATH = NIGHT_INPUT_PATH / CALIBRATION_FOLDER_NAME
    # Check if Calibration Frames exists
    if not CALIBRATION_FOLDER_PATH.exists():
        sys.stdout(f"Path {CALIBRATION_FOLDER_PATH} doesn't exist\n")
        return False

    M23_FOLDER_PATH = NIGHT_INPUT_PATH / M23_RAW_IMAGES_FOLDER_NAME
    # Check if m23 folder exists
    if not M23_FOLDER_PATH.exists():
        sys.stdout(f"Path {M23_FOLDER_PATH} doesn't exist\n")
        return False

    # Check for flats
    # Either the masterflat should be provided or the night should contain its own flats.
    if night.get("masterflat"):
        if not Path(night["masterflat"]).exists():
            sys.stdout(f"Provided masterflat path for {night} doesn't exist.\n")
            return False
    # If masterflat isn't provided, the night should have flats to use
    elif len(list(get_raw_flats(CALIBRATION_FOLDER_PATH))) == 0:
        sys.stdout(f"Night {night} doesn't contain flats. Provide masterflat path.\n")
        return False

    # Check for darks
    if len(list(get_raw_darks(CALIBRATION_FOLDER_PATH))) == 0:
        sys.stdout(f"Night {night} doesn't contain darks. Cannot continue without darks.\n")
        return False

    # Check for raw images
    if len(list(get_all_fit_files(M23_FOLDER_PATH))) == 0:
        sys.stdout(f"Night {night} doesn't raw images.\n")
        return False

    return True  # Assuming we did the best we could to catch errors


def validate_input_nights(list_of_nights: List[ConfigInputNight]) -> bool:
    """
    Returns True if input for all nights is valid, False otherwise.
    """
    return all([validate_night(night) for night in list_of_nights])


def validate_file(file_path: Path, on_success: Callable[[Config]]) -> None:
    """
    This method reads data processing configuration from the file path
    provided and calls the unary function on_success if the configuration
    file is valid with the configuration dictionary (Note, *not* config file).
    """
    if not file_path.exists() or not file_path.exists():
        raise FileNotFoundError("Cannot find configuration file")
    match toml.load(file_path):
        case {
            "image": {"rows": int(_), "columns": int(_), **optional_image_options},
            "processing": {
                "no_of_images_to_combine": int(_),
                "radii_of_extraction": list(radii_of_extraction),
            },
            "input": {"nights": list(list_of_nights)},
            "output": {"path": str(_)},
        } if (
            verify_optional_image_options(optional_image_options)
            and is_valid_radii_of_extraction(radii_of_extraction)
            and validate_input_nights(list_of_nights)
        ):
            on_success(sanity_check(load_defaults(toml.load(file_path))))
        case _:
            sys.stdout("Stopping because the provided configuration file has issues.\n")
