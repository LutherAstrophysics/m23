import datetime
import os
import sys
from datetime import date
from pathlib import Path
from typing import Callable, Dict, List, TypedDict

import toml
from typing_extensions import NotRequired

from m23.constants import (
    CAMERA_CHANGE_2022_DATE,
    DEFAULT_CPU_FRACTION_USAGE,
    INPUT_CALIBRATION_FOLDER_NAME,
    M23_RAW_IMAGES_FOLDER_NAME,
    TYPICAL_NEW_CAMERA_CROP_REGION,
)
from m23.exceptions import InvalidDatetimeInConfig
from m23.file.log_file_combined_file import LogFileCombinedFile
from m23.reference import get_reference_files_dict
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
    image_duration: float
    cpu_fraction: NotRequired[float]


class ConfigInputNight(TypedDict):
    path: str | Path
    masterflat: NotRequired[str]
    starttime: NotRequired[datetime.datetime]
    endtime: NotRequired[datetime.datetime]


class ConfigInput(TypedDict):
    nights: List[ConfigInputNight]
    radii_of_extraction: List[int]


class ConfigReference(TypedDict):
    image: str | Path
    file: str | Path
    logfile: str | Path
    color: str | Path


class ConfigOutput(TypedDict):
    path: str | Path
    save_aligned: NotRequired[bool]
    save_calibrated: NotRequired[bool]


class ConfigDateTime(TypedDict):
    start: datetime.datetime
    end: datetime.datetime


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
        sys.stderr.write.write("Radius of extraction must be positive integers\n")
    return is_valid


def create_processing_config(config_dict: Config) -> Config:  # noqa
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

    # Add a boolean specifying whether or not to save aligned and calibrated images.
    if config_dict["output"].get("save_aligned"):
        config_dict["output"]["save_aligned"] = True
    else:
        config_dict["output"]["save_aligned"] = False

    if config_dict["output"].get("save_calibrated"):
        config_dict["output"]["save_calibrated"] = True
    else:
        config_dict["output"]["save_calibrated"] = False

    # Convert reference file/img to Path object
    if type(config_dict["reference"]["file"]) == str:
        config_dict["reference"]["file"] = Path(config_dict["reference"]["file"])
    if type(config_dict["reference"]["image"]) == str:
        config_dict["reference"]["image"] = Path(config_dict["reference"]["image"])
    if type(config_dict["reference"]["color"]) == str:
        config_dict["reference"]["color"] = Path(config_dict["reference"]["color"])

    # Remove duplicates radii of extraction
    radii = list(set(config_dict["processing"]["radii_of_extraction"]))
    config_dict["processing"]["radii_of_extraction"] = radii

    # Set default fraction of processors to use
    if config_dict["processing"].get("cpu_fraction", None) is None:
        config_dict["processing"]["cpu_fraction"] = DEFAULT_CPU_FRACTION_USAGE

    return config_dict


def prompt_to_continue(msg: str):
    sys.stderr.write(msg + "\n")
    response = input("Do you want to continue (y/yes to continue): ")
    if response.upper() not in ["Y", "YES"]:
        os._exit(1)


def sanity_check_image(config: ConfigImage, night_date: date, check_crop=True):  # noqa
    """
    Checks for abnormal values in configuration images
    """
    rows, cols = config["rows"], config["columns"]
    crop_region = config.get("crop_region")
    old_camera = night_date < CAMERA_CHANGE_2022_DATE
    if old_camera:
        if rows != 1024:
            prompt_to_continue("Detected non 1024 image row value for old camera date")
        if cols != 1024:
            prompt_to_continue("Detected non 1024 image column value for old camera date")
        if crop_region and type(crop_region) == list and len(crop_region) > 0:
            prompt_to_continue("Detected use of crop region for old camera.")
    else:
        if rows != 2048:
            prompt_to_continue("Detected non 2048 image row value for new camera date")
        if cols != 2048:
            prompt_to_continue("Detected non 2048 image column value for new camera date")
        if check_crop:
            if (
                not crop_region
                or crop_region
                and type(crop_region) != list
                or type(crop_region) == list
                and len(crop_region) == 0
            ):
                prompt_to_continue(
                    "We typically use crop images from new camera, you don't seem to define it"
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
                                != TYPICAL_NEW_CAMERA_CROP_REGION[crop_section_index][
                                    section_coordinate_index
                                ]
                            ):
                                prompt_to_continue(
                                    "Mismatch between default crop region"
                                    + " used in new camera and config file."
                                )
                                # Ignore further checking if already made the user
                                # aware of inconsistency once
                                return

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
                    sys.stderr.write(f"Invalid value detected in crop_region {j}.\n")
                    return False
    except ValueError:
        sys.stderr.write(f"Error in crop_region {j}.\n")
        return False
    return True  # Valid


def verify_optional_processing_options(options: Dict) -> bool:
    """
    Verifies that the optional processing options are valid
    """
    valid_options = ["cpu_fraction"]
    for key in options.keys():
        if key not in valid_options:
            sys.stderr.write(
                "Invalid option in processing setting",
                key,
                "valid options are",
                valid_options,
                "\n",
            )
            return False
    # CPU fraction has to be a number between 0 and 1
    if cpu_fraction := options.get("cpu_fraction"):
        if not 0 <= cpu_fraction <= 1:
            sys.stderr.write(
                f"CPU fraction has to be a value between 0 and 1. Received: {cpu_fraction}\n"
            )
            return False
    return True


def is_night_name_valid(NIGHT_INPUT_PATH: Path):
    """
    Returns if the input night folder name follows naming conventions.
    Prints msg to stderr if invalid.
    """
    # Check if the name of input folder matches the convention
    try:
        get_date_from_input_night_folder_name(NIGHT_INPUT_PATH.name)
        return True
    except Exception:  # noqa
        sys.stderr.write(
            f"Night {NIGHT_INPUT_PATH} folder name doesn't match the naming convention\n"
        )
        return False


def validate_night(night: ConfigInputNight, image_duration: float) -> bool:  # noqa
    """
    Checks whether the input configuration provided for night is valid.
    We check whether the input folders follow the required conventions,
    whether the right files are present and more.
    """
    try:
        NIGHT_INPUT_PATH = Path(night["path"])
    except Exception:  # noqa
        sys.stderr.write(f"Invalid night {night} in config file.\nCheck path spell\n")
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
            sys.stderr.write(f"Provided masterflat path for {night} doesn't exist.\n")
            return False
    # If masterflat isn't provided, the night should have flats to use
    elif len(list(get_flats(CALIBRATION_FOLDER_PATH, image_duration))) == 0:
        sys.stderr.write(
            f"Night {night} doesn't contain flats in {CALIBRATION_FOLDER_PATH}"
            f" for image duration {image_duration}." + " Provide masterflat path.\n"
        )
        return False

    # Check for darks
    if len(list(get_darks(CALIBRATION_FOLDER_PATH, image_duration))) == 0:
        sys.stderr.write(
            f"Night {night} doesn't contain darks in {CALIBRATION_FOLDER_PATH}"
            f" for image duration {image_duration}." + " Cannot continue without darks.\n"
        )
        return False

    # Check for raw images
    try:
        if len(list(get_raw_images(M23_FOLDER_PATH, image_duration))) == 0:
            sys.stderr.write(
                f"Night {night} doesn't have raw images in {M23_FOLDER_PATH}."
                f" for image duration {image_duration}\n"
            )
            return False
    except ValueError as e:
        sys.stderr.write(
            "Raw image in night {night} doesn't confirm to 'something-00x.fit' convention.\n"
        )
        raise e

    night_date = get_date_from_input_night_folder_name(Path(night.get("path")).name)
    # Validate the start and end time of observation if provided
    # Check if datetime is declared
    if start := night.get("starttime"):
        try:
            night["starttime"] = validate_datetime(start)
        except InvalidDatetimeInConfig:
            sys.stderr.write(
                f"OPTIONAL observation start time for {night} isn't"
                " in the format  YYYY-mm-ddTHH:MM:SS where timezone is UT\n"
            )
            return False

    if end := night.get("endtime"):
        try:
            night["endtime"] = validate_datetime(end)
        except InvalidDatetimeInConfig:
            sys.stderr.write(
                f"OPTIONAL observation end time for {night} isn't"
                " in the format  YYYY-mm-ddTHH:MM:SS where timezone is UT\n"
            )
            return False

    start_time = night.get("starttime")
    end_time = night.get("endtime")
    if start_time and end_time:
        # Start time must come before end_time
        assert start_time < end_time
        if (end_time - start_time).seconds < 60 * 60:
            prompt_to_continue(f"Start time and end time are within an hour for {night_date}.")
    if start_time:
        if abs((start_time.date() - night_date).days) > 3:
            sys.stderr.write(
                f"Starttime for night {night_date} is off night_date by more than 3 days.\n"
            )
            return False
    if end_time:
        if abs((end_time.date() - night_date).days) > 3:
            sys.stderr.write(
                f"Endtime for night {end_time}  is off night_date by more than 3 days.\n"
            )
            return False

    return True  # Assuming we did the best we could to catch errors


def validate_input_nights(list_of_nights: List[ConfigInputNight], image_duration: float) -> bool:
    """
    Returns True if input for all nights is valid, False otherwise.
    """
    return all([validate_night(night, image_duration) for night in list_of_nights])


def validate_reference_files(
    reference_image: str,
    reference_file: str,
    color_ref_file: str,
    logfile: str,
    radii: List[int],
) -> bool:
    """
    Returns True if reference_image and reference_file paths exist
    """
    img_path = Path(reference_image)
    file_path = Path(reference_file)
    color_path = Path(color_ref_file)
    logfile_path = Path(logfile)
    if not (img_path.exists() and img_path.is_file() and img_path.suffix == ".fit"):
        sys.stderr.write("Make sure that the reference image exists and has .fit extension\n")
        return False
    if not (file_path.exists() and file_path.is_file() and file_path.suffix == ".txt"):
        sys.stderr.write("Make sure that the reference file exists and has .txt extension\n")
        return False
    if not (color_path.exists() and color_path.is_file() and color_path.suffix == ".txt"):
        sys.stderr.write("Make sure that the color reference file exists and has .txt extension\n")
        return False
    if not (logfile_path.exists() and logfile_path.is_file() and logfile_path.suffix == ".txt"):
        sys.stderr.write("Make sure that the log file exists and has .txt extension\n")
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


def validate_datetime(time_obj):
    if isinstance(time_obj, str):
        try:
            time_obj = datetime.datetime.strptime(time_obj, "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            raise InvalidDatetimeInConfig
    if not isinstance(time_obj, datetime.datetime):
        raise InvalidDatetimeInConfig
    return time_obj


def verify_optional_output_options(output_options: Dict[str, any]):
    valid_keys = ["save_aligned", "save_calibrated"]
    for key in output_options.keys():
        if key not in valid_keys:
            sys.stderr.write(
                f"""Found invalid key {key} in output options configuration.
                Valid keys are: {valid_keys}"""
            )
            return False
    if save_aligned := output_options.get("save_aligned"):
        if not isinstance(save_aligned, bool):
            sys.stderr.write(
                f"Expected (true/false) instance for save_aligned option found {save_aligned}\n"
            )
            return False
    if save_calibrated := output_options.get("save_calibrated"):
        if not isinstance(save_aligned, bool):
            sys.stderr.write(
                "Expected (true/false) instance for save_calibrated"
                f" option found {save_calibrated}\n"
            )
            return False
    return True


def sanity_check_no_of_images_to_combine(no_of_images_to_combine: int, image_duration: float):
    if int(70 / image_duration) != no_of_images_to_combine:
        prompt_to_continue(
            f"You have said to combine {no_of_images_to_combine}"
            f" but image duration is {image_duration}."
        )
    return True


def validate_file(file_path: Path, on_success: Callable[[Config], None]) -> None:
    """
    This method reads data processing configuration from the file path
    provided and calls the unary function on_success if the configuration
    file is valid with the configuration dictionary (Note, *not* config file).
    """
    if not file_path.exists() or not file_path.exists():
        raise FileNotFoundError("Cannot find configuration file")
    configuration = toml.load(file_path)
    load_configuration_with_necessary_reference_files(configuration)
    match configuration:
        case {
            "image": {
                "rows": int(_),
                "columns": int(_),
                **optional_image_options,
            },
            "processing": {
                "no_of_images_to_combine": int(no_of_images_to_combine),
                "radii_of_extraction": list(radii_of_extraction),
                "image_duration": float(image_duration),
                **optional_processing_options,
            },
            "reference": {
                "image": str(reference_image),
                "file": str(reference_file),
                "logfile": str(logfile),
                "color": str(color_ref_file),
            },
            "input": {"nights": list(list_of_nights)},
            "output": {"path": str(_), **optional_output_options},
        } if (
            sanity_check_no_of_images_to_combine(no_of_images_to_combine, image_duration)
            and verify_optional_image_options(optional_image_options)
            and verify_optional_processing_options(optional_processing_options)
            and verify_optional_output_options(optional_output_options)
            and is_valid_radii_of_extraction(radii_of_extraction)
            and validate_input_nights(list_of_nights, image_duration)
            and validate_reference_files(
                reference_image,
                reference_file,
                color_ref_file,
                logfile,
                radii_of_extraction,
            )
        ):
            # Check for the optional configurations
            # Optional configs should either not be declared or be
            # correctly declared
            on_success(sanity_check(create_processing_config(configuration)))
        case _:
            sys.stderr.write("Stopping.\n")


def load_configuration_with_necessary_reference_files(configuration, pop=None):
    # Users need not define reference files optional
    reference_files_dict = get_reference_files_dict()
    if user_defined_reference := configuration.get("reference"):
        # If user defines any reference file, that takes precedence
        # over files configured to be used as default
        for key in reference_files_dict:
            if key not in user_defined_reference:
                user_defined_reference[key] = reference_files_dict[key]
    else:
        configuration["reference"] = reference_files_dict
    if pop:
        for item_to_pop in pop:
            configuration["reference"].pop(item_to_pop)
