import os
import sys
from datetime import date
from functools import reduce
from pathlib import Path
from typing import Callable, Dict, List, TypedDict

import toml
from typing_extensions import NotRequired

from m23.constants import (
    CAMERA_CHANGE_2022_DATE,
    INPUT_CALIBRATION_FOLDER_NAME,
    M23_RAW_IMAGES_FOLDER_NAME,
    TYPICAL_NEW_CAMERA_CROP_REGION,
)
from m23.file.log_file_combined_file import LogFileCombinedFile
from m23.utils import (
    get_darks,
    get_date_from_input_night_folder_name,
    get_flats,
    get_raw_images,
)


# TYPE related to Config object described by the configuration file
class ConfigImage(TypedDict):
    rows: int
    columns: int
    crop_region: NotRequired[List[List[List[int]]]]


class ConfigProcessing(TypedDict):
    no_of_images_to_combine: int
    radii_of_extraction: List[int]


class ConfigInputNight(TypedDict):
    path: str | Path
    masterflat: NotRequired[str]


class ConfigInput(TypedDict):
    nights: List[ConfigInputNight]
    radii_of_extraction: List[int]


class ConfigReference(TypedDict):
    image: str | Path
    file: str | Path
    logfile : str | Path
    color: str | Path


class ConfigOutput(TypedDict):
    path: str | Path


class Config(TypedDict):
    image: ConfigImage
    processing: ConfigProcessing
    reference: ConfigReference
    input: ConfigInput
    output: ConfigOutput


def is_valid_radii_of_extraction(lst):
    """Verifies that each radius of extraction is a positive integer"""
    is_valid = all([type(i) == int and i > 0 for i in lst])
    if not is_valid:
        sys.stderr.write.write(
            "Radius of extraction must be positive integers\n"
        )
    return is_valid


def create_processing_config(config_dict: Config) -> Config:
    """
    Mutates `config_dict` to :
    1. Provide default values if optional values aren't provided.
    2. Replace all path str with Path objects
    """
    # Add empty list as the crop region if not present
    if not config_dict["image"].get("crop_region"):
        config_dict["image"]["crop_region"] = []

    # Convert input night str to Path objects
    for night in config_dict["input"]["nights"]:
        if type(night["path"]) == str:
            night["path"] = Path(night["path"])
        if night.get("masterflat") and type(night["masterflat"] == str):
            night["masterflat"] = Path(night["masterflat"])

    # Convert output path to Path object
    if type(config_dict["output"]["path"]) == str:
        config_dict["output"]["path"] = Path(config_dict["output"]["path"])

    # Convert reference file/img to Path object
    if type(config_dict["reference"]["file"]) == str:
        config_dict["reference"]["file"] = Path(
            config_dict["reference"]["file"]
        )
    if type(config_dict["reference"]["image"]) == str:
        config_dict["reference"]["image"] = Path(
            config_dict["reference"]["image"]
        )
    if type(config_dict["reference"]["color"]) == str:
        config_dict["reference"]["color"] = Path(
            config_dict["reference"]["color"]
        )

    # Remove duplicates radii of extraction
    radii = list(set(config_dict["processing"]["radii_of_extraction"]))
    config_dict["processing"]["radii_of_extraction"] = radii

    return config_dict


def prompt_to_continue(msg: str):
    sys.stderr.write(msg + "\n")
    response = input("Do you want to continue (y/yes to continue): ")
    if response.upper() not in ["Y", "YES"]:
        os._exit(1)


def sanity_check_image(config: ConfigImage, night_date: date):
    """
    Checks for abnormal values in configuration images
    """
    rows, cols = config["rows"], config["columns"]
    crop_region = config.get("crop_region")
    old_camera = night_date < CAMERA_CHANGE_2022_DATE
    if old_camera:
        if rows != 1024:
            prompt_to_continue(
                f"Detected non 1024 image row value for old camera date"
            )
        if cols != 1024:
            prompt_to_continue(
                f"Detected non 1024 image column value for old camera date"
            )
        if crop_region and type(crop_region) == list and len(crop_region) > 0:
            prompt_to_continue(f"Detected use of crop region for old camera.")
    else:
        if rows != 2048:
            prompt_to_continue(
                f"Detected non 2048 image row value for new camera date"
            )
        if cols != 2048:
            prompt_to_continue(
                f"Detected non 2048 image column value for new camera date"
            )
        if (
            not crop_region
            or crop_region
            and type(crop_region) != list
            or type(crop_region) == list
            and len(crop_region) == 0
        ):
            prompt_to_continue(
                f"We typically use crop images from new camera, you don't seem to define it"
            )
        else:
            try:
                for crop_section_index, crop_section in enumerate(crop_region):
                    for (
                        section_coordinate_index,
                        section_coordinate,
                    ) in enumerate(crop_section):
                        if (
                            section_coordinate
                            != TYPICAL_NEW_CAMERA_CROP_REGION[
                                crop_section_index
                            ][section_coordinate_index]
                        ):
                            prompt_to_continue(
                                f"Mismatch between default crop region used in new camera and config file."
                            )
                            return  # Ignore further checking if already made the user aware of inconsistency once

            except Exception as e:
                prompt_to_continue(
                    f"Error while checking crop region with standard crop region value. {e}"
                )


def sanity_check(config_dict: Config) -> Config:
    """
    This method performs any sanity checks on the configuration file.
    """
    # Ensure sane values for rows/cols, etc.
    for night in config_dict["input"]["nights"]:
        night_date = get_date_from_input_night_folder_name(night["path"])
        sanity_check_image(config_dict["image"], night_date)
    return config_dict


def verify_optional_image_options(options: Dict) -> bool:
    """
    Verifies that the optional image options are valid
    """
    if len(options.keys()) > 1:
        return False
    crop_region: List[List[int]] = options.get("crop_region", [])
    # Ensure that all values in crop_region are non-negative integers
    try:
        for i in crop_region:
            for j in i:
                valid_values = all([type(x) == int and x >= 0 for x in j])
                if not valid_values:
                    sys.stderr.write(
                        f"Invalid value detected in crop_region {j}.\n"
                    )
                    return False
    except Exception as e:
        sys.stderr.write(f"Error in crop_region {j}.\n")
        return False
    return True  # Valid


def is_night_name_valid(NIGHT_INPUT_PATH: Path):
    """
    Returns if the input night folder name follows naming conventions.
    Prints msg to stderr if invalid.
    """
    # Check if the name of input folder matches the convention
    try:
        get_date_from_input_night_folder_name(NIGHT_INPUT_PATH.name)
        return True
    except:
        sys.stderr.write(
            f"Night {NIGHT_INPUT_PATH} folder name doesn't match the naming convention\n"
        )
        return False


def validate_night(night: ConfigInputNight) -> bool:
    """
    Checks whether the input configuration provided for night is valid.
    We check whether the input folders follow the required conventions,
    whether the right files are present and more.
    """
    try:
        NIGHT_INPUT_PATH = Path(night["path"])
    except:
        sys.stderr.write(
            f"Invalid night {night} in config file.\nCheck path spell\n"
        )
        return False

    # Check if the night input path exists
    if not NIGHT_INPUT_PATH.exists():
        sys.stderr.write(f"Images path for {night} doesn't exist\n")
        return False

    if not is_night_name_valid(NIGHT_INPUT_PATH):
        return False

    CALIBRATION_FOLDER_PATH = NIGHT_INPUT_PATH / INPUT_CALIBRATION_FOLDER_NAME
    # Check if Calibration Frames exists
    if not CALIBRATION_FOLDER_PATH.exists():
        sys.stderr.write(f"Path {CALIBRATION_FOLDER_PATH} doesn't exist\n")
        return False

    M23_FOLDER_PATH = NIGHT_INPUT_PATH / M23_RAW_IMAGES_FOLDER_NAME
    # Check if m23 folder exists
    if not M23_FOLDER_PATH.exists():
        sys.stderr.write(f"Path {M23_FOLDER_PATH} doesn't exist\n")
        return False

    # Check for flats
    # Either the masterflat should be provided or the night should contain its own flats.
    if night.get("masterflat"):
        if not Path(night["masterflat"]).exists():
            sys.stderr.write(
                f"Provided masterflat path for {night} doesn't exist.\n"
            )
            return False
    # If masterflat isn't provided, the night should have flats to use
    elif len(list(get_flats(CALIBRATION_FOLDER_PATH))) == 0:
        sys.stderr.write(
            f"Night {night} doesn't contain flats in {CALIBRATION_FOLDER_PATH}. Provide masterflat path.\n"
        )
        return False

    # Check for darks
    if len(list(get_darks(CALIBRATION_FOLDER_PATH))) == 0:
        sys.stderr.write(
            f"Night {night} doesn't contain darks in {CALIBRATION_FOLDER_PATH}. Cannot continue without darks.\n"
        )
        return False

    # Check for raw images
    try:
        if len(list(get_raw_images(M23_FOLDER_PATH))) == 0:
            sys.stderr.write(
                f"Night {night} doesn't have raw images in {M23_FOLDER_PATH}.\n"
            )
            return False
    except ValueError as e:
        sys.stderr.write(
            "Raw image in night {night} doesn't confirm to 'something-00x.fit' convention.\n"
        )
        raise e

    return True  # Assuming we did the best we could to catch errors


def validate_input_nights(list_of_nights: List[ConfigInputNight]) -> bool:
    """
    Returns True if input for all nights is valid, False otherwise.
    """
    return all([validate_night(night) for night in list_of_nights])


def validate_reference_files(
    reference_image: str, reference_file: str, color_ref_file: str, logfile : str, radii : List[int]
) -> bool:
    """
    Returns True if reference_image and reference_file paths exist
    """
    img_path = Path(reference_image)
    file_path = Path(reference_file)
    color_path = Path(color_ref_file)
    logfile_path = Path(logfile)
    if not (
        img_path.exists() and img_path.is_file() and img_path.suffix == ".fit"
    ):
        sys.stderr.write(
            "Make sure that the reference exists and has .fit extension"
        )
        return False
    if not (
        file_path.exists()
        and file_path.is_file()
        and file_path.suffix == ".txt"
    ):
        sys.stderr.write(
            "Make sure that the reference file exists and has .txt extension\n"
        )
        return False
    if not (
        color_path.exists()
        and color_path.is_file()
        and color_path.suffix == ".txt"
    ):
        sys.stderr.write(
            "Make sure that the color reference file exists and has .txt extension\n"
        )
        return False
    if not (
        logfile_path.exists()
        and logfile_path.is_file()
        and logfile_path.suffix == ".txt"
    ):
        sys.stderr.write(
            "Make sure that the log file exists and has .txt extension\n"
        )
        return False
    
    # Make sure that the logfile combined reference file has 
    # all radii of extraction data
    available_radii = LogFileCombinedFile(logfile_path).get_star_data(1).radii_adu.keys()
    for i in radii:
        if i not in available_radii:
            sys.stderr.write(
                f"Radius {i} ADU data not present in provided logfile combined file. \n"
            )
            return False

    return True


def validate_file(
    file_path: Path, on_success: Callable[[Config], None]
) -> None:
    """
    This method reads data processing configuration from the file path
    provided and calls the unary function on_success if the configuration
    file is valid with the configuration dictionary (Note, *not* config file).
    """
    if not file_path.exists() or not file_path.exists():
        raise FileNotFoundError("Cannot find configuration file")
    match toml.load(file_path):
        case {
            "image": {
                "rows": int(_),
                "columns": int(_),
                **optional_image_options,
            },
            "processing": {
                "no_of_images_to_combine": int(_),
                "radii_of_extraction": list(radii_of_extraction),
            },
            "reference": {
                "image": str(reference_image),
                "file": str(reference_file),
                "logfile": str(logfile),
                "color": str(color_ref_file),
            },
            "input": {"nights": list(list_of_nights)},
            "output": {"path": str(_)},
        } if (
            verify_optional_image_options(optional_image_options)
            and is_valid_radii_of_extraction(radii_of_extraction)
            and validate_input_nights(list_of_nights)
            and validate_reference_files(
                reference_image, reference_file, color_ref_file, logfile, radii_of_extraction
            )
        ):
            on_success(
                sanity_check(create_processing_config(toml.load(file_path)))
            )
        case _:
            sys.stderr.write(
                "Stopping because the provided configuration file doesn't match the required format.\n"
            )
