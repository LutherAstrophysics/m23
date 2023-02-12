import logging
from pathlib import Path

from m23.constants import FLUX_LOGS_COMBINED_FOLDER_NAME
from m23.processor.process_nights import normalization_helper
from m23.utils import get_date_from_input_night_folder_name, get_log_file_name

from .renormalize_config_loader import (
    RenormalizeConfig,
    validate_renormalize_config_file,
)


def renormalize_auxiliary(renormalize_dict: RenormalizeConfig):
    for night in renormalize_dict["input"]["nights"]:
        NIGHT_FOLDER = night["path"]
        night_date = get_date_from_input_night_folder_name(NIGHT_FOLDER.name)
        log_file_path = NIGHT_FOLDER / get_log_file_name(night_date)
        radii_of_extraction = renormalize_dict["processing"]["radii_of_extraction"]
        logging.basicConfig(
            filename=log_file_path,
            format="%(asctime)s %(message)s",
            level=logging.INFO,
        )
        logging.info(f"Running renormalization for radii {radii_of_extraction}")

        LOG_FILES_COMBINED_FOLDER: Path = NIGHT_FOLDER / FLUX_LOGS_COMBINED_FOLDER_NAME
        # Create log files combined folder if it doesn't yet exist
        LOG_FILES_COMBINED_FOLDER.mkdir(exist_ok=True)

        normalization_helper(
            radii_of_extraction,
            LOG_FILES_COMBINED_FOLDER,
            renormalize_dict["reference"]["file"],
            night["files_to_use"],
            night_date,
        )


def renormalize(file_path: str):
    """
    Starts renormalization with the configuration file `file_path` provided as the argument.
    Calls auxiliary function `renormalize_auxiliary` if the configuration is valid.
    """
    validate_renormalize_config_file(Path(file_path), on_success=renormalize_auxiliary)
