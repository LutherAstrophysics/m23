from pathlib import Path

from m23.processor.config_loader import Config, validate_file


def start_data_processing_auxiliary(config: Config):
    """
    This function processes (one or more) nights defined in config dict by
    putting together various functionalities like calibration, alignment,
    extraction, and normalization together.
    """

    OUTPUT_PATH: Path = config["output"]["path"]
    # If directory doesn't exist create directory including necessary parent directories.
    OUTPUT_PATH.mkdir(parents=True, exist_ok=True)


def start_data_processing_helper(file_path: Path):
    """
    Starts data processing with the configuration file `file_path` provided as the argument.
    Calls auxiliary function `start_data_processing_auxiliary` if the configuration is valid.
    """
    validate_file(file_path, on_success=start_data_processing_auxiliary)
