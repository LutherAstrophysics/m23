import sys
from pathlib import Path
from typing import Callable, TypedDict

import toml

from m23.constants import INPUT_CALIBRATION_FOLDER_NAME
from m23.processor.config_loader import (
    ConfigImage,
    is_night_name_valid,
    sanity_check_image,
)
from m23.utils import get_darks, get_date_from_input_night_folder_name, get_flats


class MasterflatGeneratorConfig(TypedDict):
    input: Path | str
    output: Path | str
    image: ConfigImage
    image_duration: float


def is_valid(config: MasterflatGeneratorConfig) -> bool:
    """
    Returns whether the configuration file is valid
    """
    NIGHT_INPUT_PATH = Path(config["input"])
    if not NIGHT_INPUT_PATH.exists():
        sys.stderr.write(f"Input folder {NIGHT_INPUT_PATH} doesn't exist.\n")
        return False

    # Verify that the Night folder name matches the naming convention
    if not is_night_name_valid(NIGHT_INPUT_PATH):
        # No error message needed as the function `is_night_name_valid` write error if there's one
        return False

    # Verify that the CALIBRATION FOLDER exists
    CALIBRATION_FOLDER_PATH = NIGHT_INPUT_PATH / INPUT_CALIBRATION_FOLDER_NAME
    if not CALIBRATION_FOLDER_PATH.exists():
        sys.stderr.write(f"Calibration folder {CALIBRATION_FOLDER_PATH} doesn't exist.\n")
        return False

    # Verify that the image duration is a float
    if not type(config["image_duration"]) not in [float, int]:
        sys.stderr.write(f"Image duration has to be a float. Got {config['image_duration']}\n")
        return False

    image_duration = config["image_duration"]

    # Verify that the night contains darks to use
    if len(list(get_darks(CALIBRATION_FOLDER_PATH, image_duration))) == 0:
        sys.stderr.write(
            f"Night {NIGHT_INPUT_PATH} doesn't contain darks for image duration of {image_duration} in {CALIBRATION_FOLDER_PATH}.\n"  # noqa ES501
        )
        return False

    # Verify that the night contains flats to use
    if len(list(get_flats(CALIBRATION_FOLDER_PATH, image_duration))) == 0:
        sys.stderr.write(
            f"Night {NIGHT_INPUT_PATH} doesn't contain flats for image duration of {image_duration} in {CALIBRATION_FOLDER_PATH}.\n"  # noqa ES501
        )
        return False

    try:
        output_path = Path(config["output"])
        output_path.mkdir(parents=True, exist_ok=True)  # Create directory if not exists
    except Exception as e:
        sys.stderr.write(f"Error in output folder. {e} \n")
        return False

    if not is_image_properties_valid(config["image"]):
        # No error message needed as the function
        # `is_image_properties_valid` write error if there's one
        return False

    return True  # No errors detected


def is_image_properties_valid(image_config: ConfigImage) -> bool:
    """
    Checks and returns if  the image_properties is valid.
    If invalid, write the error msg in stderr.
    """

    # Validate the image properties in the configuration file
    # Ensure that rows and cols are int > 0
    rows, cols = image_config["rows"], image_config["columns"]
    if type(rows) != int or type(cols) != int or rows <= 0 or cols <= 0:
        sys.stderr.write(
            f"Rows and columns of image have to be > 0. Got  rows:{rows} cols:{cols}\n"
        )
        return False
    # Ensure that if crop_region is present, it has to be list of list of list of ints
    if crop_region := image_config.get("crop_region"):
        try:
            for i in crop_region:
                for j in i:
                    valid_values = all([type(x) == int and x >= 0 for x in j])
                    if not valid_values:
                        sys.stderr.write(f"Invalid value detected in crop_region {j}.\n")
                        return False
        except [ValueError]:
            sys.stderr.write(f"Error in crop_region {j}.\n")
            return False

    return True  # No error detected


def create_enhanced_config(
    config: MasterflatGeneratorConfig,
) -> MasterflatGeneratorConfig:
    """
    This function enhances the configuration file for ease of functions
    that later require processing of the config file
    """
    # Covert folder str to path
    config["input"] = Path(config["input"])
    config["output"] = Path(config["output"])
    return config


def sanity_check(config: MasterflatGeneratorConfig) -> MasterflatGeneratorConfig:
    """
    This method is warn about technically correct but abnormal configuration values
    """
    night_date = get_date_from_input_night_folder_name(config["input"])
    # Since we dont crop out (meaning fill the vignetting ring with bogus values)
    # in the case of masterdark and masterflat, its not necessary to check it
    sanity_check_image(config["image"], night_date, check_crop=False)
    return config


def validate_generate_masterflat_config_file(
    file_path: Path, on_success: Callable[[MasterflatGeneratorConfig], None]
):
    """
    This method reads configuration file for generating masterflat
    and if the config is valid, calls the unary on_success function with the
    configuration file
    """

    if not file_path.exists():
        raise FileNotFoundError("Cannot find configuration file")
    match toml.load(file_path):
        case {
            "input": _,
            "output": _,
            "image": {"rows": int(_), "columns": int(_)},
        } as masterflat_generator_config if is_valid(masterflat_generator_config):
            on_success(sanity_check(create_enhanced_config(masterflat_generator_config)))
        case _:
            sys.stderr.write("Invalid format.\n")
