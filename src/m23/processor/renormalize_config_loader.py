import sys
from functools import cache
from pathlib import Path
from typing import Callable, List, TypedDict

import toml
from typing_extensions import NotRequired

from m23.constants import DEFAULT_CPU_FRACTION_USAGE, LOG_FILES_COMBINED_FOLDER_NAME
from m23.file.log_file_combined_file import LogFileCombinedFile
from m23.processor.config_loader import (
    is_night_name_valid,
    is_valid_radii_of_extraction,
    load_configuration_with_necessary_reference_files,
)
from m23.utils import get_image_number_in_log_file_combined_file


class RenormalizeConfigProcessing(TypedDict):
    radii_of_extraction: List[int]
    cpu_fraction: NotRequired[float]


class RenormalizeConfigReference(TypedDict):
    file: Path | str
    logfile: Path | str
    color: Path | str


class RenormalizeConfigNight(TypedDict):
    path: Path | str
    first_logfile_number: int
    last_logfile_number: int
    files_to_use: NotRequired[List[Path]]


class RenormalizeConfigInput(TypedDict):
    nights: List[RenormalizeConfigNight]


class RenormalizeConfig(TypedDict):
    processing: RenormalizeConfigProcessing
    reference: RenormalizeConfigReference
    input: RenormalizeConfigInput


@cache
def get_relevant_log_files_combined_files(folder: Path, start: int, end: int) -> List[Path]:
    """
    Returns the list of log files combined files in the range enclosed
    (inclusively) by start and end path.

    param: folder: Path containing log files combined
    param: start: First file number to consider
    param: end: Last file number to consider

    Note that if start and/or end number fall of the edges of the available file
    numbers, the result contains the result that goes to the edge on the
    respective side.
    """
    result = []
    for file in folder.glob("*"):
        if file.is_file() and file.suffix == ".txt":
            if start <= get_image_number_in_log_file_combined_file(file) <= end:
                result.append(file)
    return result


def validate_night(night):
    path = Path(night["path"])

    first_logfile = night["first_logfile_number"]
    last_logfile = night["last_logfile_number"]

    # Validate path
    if not path.exists():
        sys.stderr.write(f"Path {path} doesn't exist\n")
        return False

    # Check if the naming convention is valid for the input night
    if not is_night_name_valid(path):
        sys.stderr.write("Naming convention is invalid\n")
        return False

    LOG_FILES_COMBINED_FOLDER = path / LOG_FILES_COMBINED_FOLDER_NAME

    if not LOG_FILES_COMBINED_FOLDER.exists():
        sys.stderr.write(f"Path {LOG_FILES_COMBINED_FOLDER} doesn't exist\n")
        return False

    if (type(first_logfile) != int or type(last_logfile) != int) and not (
        last_logfile >= first_logfile >= 1
    ):
        sys.stderr.write(
            f"Invalid logfile numbers. First: {first_logfile} Last: {last_logfile} for night {night}\n"  # noqa
        )
        return False

    # Ensure that the list of files to use from LOG_FILES_COMBINED_FOLDER isn't empty
    # based on given constraints of start and end indices
    if (
        len(
            get_relevant_log_files_combined_files(
                LOG_FILES_COMBINED_FOLDER, first_logfile, last_logfile
            )
        )
        == 0
    ):
        sys.stderr.write(f"No logfiles in range {first_logfile}-{last_logfile} \n")
        return False

    return True


def is_valid(config: RenormalizeConfig) -> bool:  # noqa
    """
    Returns whether any error can be found in renormalize config dict
    """
    # Validate radii of extraction
    if not is_valid_radii_of_extraction(config["processing"]["radii_of_extraction"]):
        return False

    # Validate reference file
    ref_file = Path(config["reference"]["file"])
    if not (ref_file.exists() and ref_file.is_file() and ref_file.suffix == ".txt"):
        sys.stderr.write("Make sure the provided reference file exits and has txt extension\n")
        return False

    # Validate logfile file
    logfile = Path(config["reference"]["logfile"])
    if not (logfile.exists() and logfile.is_file() and logfile.suffix == ".txt"):
        sys.stderr.write("Make sure the provided logfile file exits and has txt extension\n")
        return False

    # Make sure that the logfile combined reference file has
    # all radii of extraction data
    available_radii = LogFileCombinedFile(logfile).get_star_data(1).radii_adu.keys()
    for i in config["processing"]["radii_of_extraction"]:
        if i not in available_radii:
            sys.stderr.write(
                f"Radius {i} ADU data not present in provided logfile combined file. \n"
            )
            return False

    if cpu_fraction := config["processing"].get("cpu_fraction"):
        if not 0 <= cpu_fraction <= 1:
            sys.stderr.write(f"CPU fraction has to be between 0 and 1. Received {cpu_fraction} \n")
            return False

    color_ref_file = Path(config["reference"]["color"])
    if not (
        color_ref_file.exists() and color_ref_file.is_file() and color_ref_file.suffix == ".txt"
    ):
        sys.stderr.write(
            "Make sure the provided color reference file exits and has txt extension\n"
        )
        return False

    # Validate each night
    for night in config["input"]["nights"]:
        is_valid = validate_night(night)
        if not is_valid:
            sys.stderr.write(f"Invalid night {night}\n")
            return False

        return True  # No errors detected


def sanity_check(config: RenormalizeConfig):
    """
    Performs any sanity check in the renormalization config
    """
    return config


def create_enhanced_config(config: RenormalizeConfig):
    """
    Creates an enhanced version of the renormalize config by converting str types to Path objects
    and other possible sanitation/optimizations
    """
    if type(config["reference"]["file"]) == str:
        config["reference"]["file"] = Path(config["reference"]["file"])
    if type(config["reference"]["color"]) == str:
        config["reference"]["color"] = Path(config["reference"]["color"])

    for night in config["input"]["nights"]:
        if type(night["path"]) == str:
            night["path"] = Path(night["path"])
        # Set the list of log files to use for normalization based on the
        # provided start, end indices
        night["files_to_use"] = get_relevant_log_files_combined_files(
            night["path"] / LOG_FILES_COMBINED_FOLDER_NAME,
            night["first_logfile_number"],
            night["last_logfile_number"],
        )

    # Remove duplicates in radii of extraction
    radii = config["processing"]["radii_of_extraction"]
    config["processing"]["radii_of_extraction"] = list(set(radii))

    if config["processing"].get("cpu_fraction", None) is None:
        config["processing"]["cpu_fraction"] = DEFAULT_CPU_FRACTION_USAGE

    return config


def validate_renormalize_config_file(
    file_path: Path, on_success: Callable[[RenormalizeConfig], None]
) -> None:
    """
    This method reads data processing configuration from the file path
    provided and calls the unary function on_success if the configuration
    file is valid with the configuration dictionary (Note, *not* config file).
    """
    if not file_path.exists() or not file_path.exists():
        raise FileNotFoundError("Cannot find configuration file")
    configuration = toml.load(file_path)
    load_configuration_with_necessary_reference_files(configuration, pop=("image",))
    match configuration:
        case {
            "processing": {"radii_of_extraction": list(_)},
            "input": {"nights": list(_)},
            "reference": {"file": str(_), "color": str(_), "logfile": str(_)},
        } as renormalize_config if is_valid(renormalize_config):
            on_success(sanity_check(create_enhanced_config(renormalize_config)))
        case _:
            sys.stderr.write("Stopping\n")


if __name__ == "__main__":
    validate_renormalize_config_file(Path("1.toml"), on_success=lambda *args: print("Success"))
