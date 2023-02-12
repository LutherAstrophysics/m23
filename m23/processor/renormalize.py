from pathlib import Path

from m23.constants import FLUX_LOGS_COMBINED_FOLDER_NAME
from m23.processor.process_nights import normalization_helper
from m23.utils import get_date_from_input_night_folder_name

from .renormalize_config_loader import (
    RenormalizeConfig,
    validate_renormalize_config_file,
)


def renormalize_auxiliary(renormalize_dict: RenormalizeConfig):
    for night in renormalize_dict["input"]["nights"]:
        NIGHT_FOLDER = night["path"]
        normalization_helper(
            renormalize_dict["processing"]["radii_of_extraction"],
            NIGHT_FOLDER / FLUX_LOGS_COMBINED_FOLDER_NAME,
            renormalize_dict["reference"]["file"],
            night["files_to_use"],
            get_date_from_input_night_folder_name(NIGHT_FOLDER.name),
        )


def renormalize(file_path: str):
    """
    Starts renormalization with the configuration file `file_path` provided as the argument.
    Calls auxiliary function `renormalize_auxiliary` if the configuration is valid.
    """
    validate_renormalize_config_file(Path(file_path), on_success=renormalize_auxiliary)
