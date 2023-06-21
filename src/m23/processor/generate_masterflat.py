from pathlib import Path

from m23.calibrate.master_calibrate import makeMasterDark, makeMasterFlat
from m23.constants import INPUT_CALIBRATION_FOLDER_NAME
from m23.file.masterflat_file import MasterflatFile
from m23.matrix import crop
from m23.processor.generate_masterflat_config_loader import (
    MasterflatGeneratorConfig,
    validate_generate_masterflat_config_file,
)
from m23.utils import (
    fit_data_from_fit_images,
    get_darks,
    get_date_from_input_night_folder_name,
    get_flats,
)


def generate_masterflat_auxiliary(config: MasterflatGeneratorConfig) -> None:
    """
    Generates masterflat based on the configuration provided
    this function assumes that the configuration provided is valid as it
    should be only calledfrom generate_master_flat that checks for the validity
    of the configuration file before calling this function.
    """
    rows, cols = config["image"]["rows"], config["image"]["columns"]
    crop_region = config["image"].get("crop_region", [])
    NIGHT_INPUT_CALIBRATION_FOLDER = config["input"] / INPUT_CALIBRATION_FOLDER_NAME
    flats = fit_data_from_fit_images(get_flats(NIGHT_INPUT_CALIBRATION_FOLDER))
    darks = fit_data_from_fit_images(get_darks(NIGHT_INPUT_CALIBRATION_FOLDER))
    night_date = get_date_from_input_night_folder_name(config["input"])

    # Crop images if crop region is defined
    if len(crop_region) > 0:
        flats = [crop(matrix, rows, cols) for matrix in flats]

    # We have to first create master dark before creating masterflat
    # as masteflat requires masterdark. Note that we're passing saveAs
    # as None because we don't want to save the masterdark created in this
    # process
    masterDarkData = makeMasterDark(
        listOfDarkData=darks,
    )

    # Make master flat
    filename = MasterflatFile.generate_file_name(night_date)
    save_file_path = config["output"] / filename

    makeMasterFlat(
        saveAs=save_file_path,
        masterDarkData=masterDarkData,
        headerToCopyFromName=next(
            get_flats(NIGHT_INPUT_CALIBRATION_FOLDER)
        ).absolute(),  # Gets absolute path of first flat file,
        listOfFlatData=flats,
    )


def generate_masterflat(file_path: str):
    """
    Starts generating masterflat based on the configuration specified in the
    file given by `file_path`
    """
    validate_generate_masterflat_config_file(
        Path(file_path), on_success=generate_masterflat_auxiliary
    )