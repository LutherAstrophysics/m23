import logging
import sys
from pathlib import Path

from m23.constants import FLUX_LOGS_COMBINED_FOLDER_NAME
from m23.file.log_file_combined_file import LogFileCombinedFile
from m23.file.reference_log_file import ReferenceLogFile
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

        logger = logging.getLogger("LOGGER_" + str(night_date))
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        ch = logging.FileHandler(log_file_path)
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        # Write to std out in addition to writing to a logfile
        ch2 = logging.StreamHandler(sys.stdout)
        ch2.setFormatter(formatter)
        logger.addHandler(ch2)  # Write to stdout

        first_image = night["first_logfile_number"]
        last_image = night["last_logfile_number"]
        logger.info(
            f"Running renormalization for radii {radii_of_extraction}. Img: {first_image}-{last_image}"
        )

        FLUX_LOGS_COMBINED_FOLDER: Path = NIGHT_FOLDER / FLUX_LOGS_COMBINED_FOLDER_NAME
        # Create log files combined folder if it doesn't yet exist
        FLUX_LOGS_COMBINED_FOLDER.mkdir(exist_ok=True)

        reference_log_file = ReferenceLogFile(
            renormalize_dict["reference"]["file"],
        )
        logfile_combined_reference_logfile = LogFileCombinedFile(renormalize_dict["reference"]["logfile"])

        # Ensure color ref file path is str
        color_ref_file_path = str(renormalize_dict["reference"]["color"])

        log_files_to_use = [LogFileCombinedFile(file) for file in night["files_to_use"]]
        img_duration = log_files_to_use[0].img_duration()

        # Perform intranight normalization then internight normalization
        normalization_helper(
            radii_of_extraction,
            reference_log_file,
            log_files_to_use,
            img_duration,
            night_date,
            color_ref_file_path,
            NIGHT_FOLDER,
            logfile_combined_reference_logfile
        )


def renormalize(file_path: str):
    """
    Starts renormalization with the configuration file `file_path` provided as the argument.
    Calls auxiliary function `renormalize_auxiliary` if the configuration is valid.
    """
    validate_renormalize_config_file(Path(file_path), on_success=renormalize_auxiliary)
