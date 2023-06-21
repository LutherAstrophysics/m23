from pathlib import Path
from typing import Callable, List, TypedDict

import toml

from m23.constants import COLOR_NORMALIZED_FOLDER_NAME, SKY_BG_FOLDER_NAME
from m23.file.color_normalized_file import ColorNormalizedFile
from m23.file.sky_bg_file import SkyBgFile
from m23.utils import get_date_from_input_night_folder_name, get_radius_folder_name


class NightsCSVConfig(TypedDict):
    color_normalized_files: List[Path]
    sky_bg_files: List[Path]
    output: Path
    radius: int


def handle_night(night, radius, color_normalized_files, sky_bg_files):
    night_path = Path(night)
    if not night_path.exists():
        raise Exception(f"night {night} doesn't exist")
    try:
        night_date = get_date_from_input_night_folder_name(night_path)
    except ValueError:
        raise Exception(f"{night} name doesn't match naming conventions")
    color_normalized_file_name = ColorNormalizedFile.get_file_name(night_date, radius)
    sky_bg_file_name = SkyBgFile.generate_file_name(night_date)
    cn_file_path = (
        night_path
        / COLOR_NORMALIZED_FOLDER_NAME
        / get_radius_folder_name(radius)
        / color_normalized_file_name
    )
    sky_bg_file_path = night_path / SKY_BG_FOLDER_NAME / sky_bg_file_name
    if not sky_bg_file_path.exists():
        raise Exception(
            f"Sky background file for {night_date} doesn't exist with name {sky_bg_file_path.name}"
            f" in {night_path / SKY_BG_FOLDER_NAME}"
        )
    if not cn_file_path.exists():
        raise Exception(
            f"Color normalized file for {night_date} doesn't exist with name {cn_file_path.name}"
        )
    color_normalized_files.append(cn_file_path)
    sky_bg_files.append(sky_bg_file_path)


def validate_nights_csv_config_file(
    file_path: Path, on_success: Callable[[NightsCSVConfig], None]
):
    """
    This method reads configuration file for generating a csv file of stars
    daily flux values for the given nights and calls the unary on_success
    function with the configuration file if the config file is valid
    """
    if not file_path.exists():
        raise FileNotFoundError("Cannot find configuration file")
    # Make sure the output path exists
    config_data = toml.load(file_path)
    input_nights = config_data.get("input")
    radius = config_data.get("radius")

    # Radius is an int
    if type(radius) != int:
        raise Exception("Improper radius value, must be an int")

    # Input key exists
    if not input_nights:
        raise Exception("Can't find 'input' in config file")
    # All input locations are valid
    if type(input_nights) != list:
        raise Exception("'input' must be a list of night paths")

    color_normalized_files = []
    sky_bg_files = []

    for night in input_nights:
        handle_night(night, radius, color_normalized_files, sky_bg_files)

    output_location = config_data.get("output")
    # Output key exists
    if not output_location:
        raise Exception("Can't find 'output' in config file")
    # Output dir exists
    output_path = Path(output_location)
    if not output_path.is_dir() or not output_path.exists():
        raise Exception("Output path must be an existing directory")

    on_success(
        {
            "color_normalized_files": color_normalized_files,
            "sky_bg_files": sky_bg_files,
            "radius": radius,
            "output": output_path,
        }
    )
