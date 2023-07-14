import logging
import os
import shutil
import sys
import traceback
from datetime import date
from pathlib import Path
from typing import Iterable, List

import multiprocess as mp
import toml
from astropy.io.fits import getdata

from m23 import __version__
from m23.calibrate.master_calibrate import makeMasterDark, makeMasterFlat
from m23.charts import draw_normfactors_chart
from m23.constants import (
    ALIGNED_COMBINED_FOLDER_NAME,
    ALIGNED_FOLDER_NAME,
    CONFIG_FILE_NAME,
    FLUX_LOGS_COMBINED_FOLDER_NAME,
    INPUT_CALIBRATION_FOLDER_NAME,
    LOG_FILES_COMBINED_FOLDER_NAME,
    M23_RAW_IMAGES_FOLDER_NAME,
    MASTER_DARK_NAME,
    OUTPUT_CALIBRATION_FOLDER_NAME,
    RAW_CALIBRATED_FOLDER_NAME,
    SKY_BG_BOX_REGION_SIZE,
    SKY_BG_FOLDER_NAME,
)
from m23.exceptions import InternightException
from m23.extract import sky_bg_average_for_all_regions
from m23.file.aligned_combined_file import AlignedCombinedFile
from m23.file.alignment_stats_file import AlignmentStatsFile
from m23.file.log_file_combined_file import LogFileCombinedFile
from m23.file.masterflat_file import MasterflatFile
from m23.file.raw_image_file import RawImageFile
from m23.file.reference_log_file import ReferenceLogFile
from m23.file.sky_bg_file import SkyBgFile
from m23.internight_normalize import internight_normalize
from m23.matrix import crop
from m23.norm import normalize_log_files
from m23.processor.align_combined_extract import align_combined_extract
from m23.processor.config_loader import Config, ConfigInputNight, validate_file
from m23.utils import (
    fit_data_from_fit_images,
    get_darks,
    get_date_from_input_night_folder_name,
    get_flats,
    get_log_file_name,
    get_output_folder_name_from_night_date,
    get_radius_folder_name,
    get_raw_images,
    sorted_by_number,
)


def normalization_helper(  # noqa
    radii_of_extraction: List[int],
    reference_log_file: ReferenceLogFile,
    log_files_to_use: List[LogFileCombinedFile],
    img_duration: float,
    night_date: date,
    color_ref_file_path: Path,
    output: Path,
    logfile_combined_reference_logfile: LogFileCombinedFile,
    is_running_as_part_of_process=False,
):
    """
    This is a normalization helper function extracted so that it can be reused
    by the renormalization script
    """

    # If running as part of process, we save flux log combined in a special
    # folder will all images from the night included which will be helpful for
    # Eclipsing binary study.
    if is_running_as_part_of_process:
        FLUX_LOGS_COMBINED_OUTPUT_FOLDER = output / (FLUX_LOGS_COMBINED_FOLDER_NAME + "(All)")
    else:
        FLUX_LOGS_COMBINED_OUTPUT_FOLDER = output / FLUX_LOGS_COMBINED_FOLDER_NAME
    FLUX_LOGS_COMBINED_OUTPUT_FOLDER.mkdir(exist_ok=True)  # Create folder if it doesn't exist
    logger = logging.getLogger("LOGGER_" + str(night_date))

    if len(log_files_to_use) < 4:
        logger.error("Less than 4 data points present. Skipping normalization.")
        return

    intranight_norm_results = {}

    for radius in radii_of_extraction:
        logger.info(f"Normalizing for radius of extraction {radius} px")
        RADIUS_FOLDER = FLUX_LOGS_COMBINED_OUTPUT_FOLDER / get_radius_folder_name(radius)
        RADIUS_FOLDER.mkdir(exist_ok=True)  # Create folder if it doesn't exist
        for file in RADIUS_FOLDER.glob("*"):
            if file.is_file():
                file.unlink()  # Remove each file in the folder
        intranight_norm_result = normalize_log_files(
            reference_log_file,
            log_files_to_use,
            RADIUS_FOLDER,
            radius,
            img_duration,
            night_date,
        )
        intranight_norm_results[radius] = intranight_norm_result

    draw_normfactors_chart(log_files_to_use, FLUX_LOGS_COMBINED_OUTPUT_FOLDER, radii_of_extraction)
    logger.info("Completed drawing normfactors chart")

    # Stop running further if running as part of process.  This is because, one
    # would usually have to run renorm with a section of a night and it is then that
    # the final color normalized files, sky background files are generated. Therefore
    # it's not necessary to generate them twice.
    if is_running_as_part_of_process:
        return

    # Generate sky bg file
    sky_bg_filename = output / SKY_BG_FOLDER_NAME / SkyBgFile.generate_file_name(night_date)

    # Internight normalization
    try:
        normfactors = internight_normalize(
            output,
            logfile_combined_reference_logfile,
            color_ref_file_path,
            radii_of_extraction,
        )
    except InternightException:
        logger.error("Returning in middle of internight normalization")
        return

    # Create folder if it doesn't exist
    sky_bg_filename.parent.mkdir(parents=True, exist_ok=True)
    color_normfactors = {
        radius: normfactors[radius]["color"].items() for radius in radii_of_extraction
    }
    brightness_normfactors = {
        radius: normfactors[radius]["brightness"].items() for radius in radii_of_extraction
    }

    color_normfactors_titles = []
    color_normfactors_values = []

    for radius in color_normfactors:
        for section, section_value in color_normfactors[radius]:
            color_normfactors_titles.append(f"norm_{radius}px_color_{section}")
            color_normfactors_values.append(section_value)

    brightness_normfactors_titles = []
    brightness_normfactors_values = []

    for radius in brightness_normfactors:
        for section, section_value in brightness_normfactors[radius]:
            brightness_normfactors_titles.append(f"norm_{radius}px_brightness{section}")
            brightness_normfactors_values.append(section_value)

    create_sky_bg_file(
        SkyBgFile(sky_bg_filename),
        log_files_to_use,
        night_date,
        color_normfactors_titles,
        color_normfactors_values,
        brightness_normfactors_titles,
        brightness_normfactors_values,
        intranight_norm_results[radii_of_extraction[0]].get("normalized_cluster_angle"),
    )


def create_sky_bg_file(
    sky_bg_file: SkyBgFile,
    log_files_to_use: Iterable[LogFileCombinedFile],
    night_date: date,
    color_normfactors_title: Iterable[str],
    color_normfactors_values: Iterable[float],
    brightness_normfactors_title: Iterable[str],
    brightness_normfactors_values: Iterable[float],
    normalized_cluster_angle: int,
):
    """
    Creates sky bg data. Note that this isn't performed right after extraction
    is that we want to re-perform it after re-normalization. If we do it as part
    of `normalization_helper` which is what both `process_night` and `renorm`
    use, we wouldn't have to do it twice.

    param: sky_bg_file: SkyBgFile object to use
    param: log_files_to_use: List of log files to use
    param: night_date: Date object of the night
    normfactors: Dictionary of normfactors for various radii of extraction

    """
    logger = logging.getLogger("LOGGER_" + str(night_date))
    logger.info("Generating sky background file")
    bg_data_of_all_images = []

    for logfile in log_files_to_use:
        date_time_of_image = logfile.datetime()
        # Here we find the corresponding aligned combined file first
        # so we can use that to calculate the sky bg data.
        aligned_combined_folder = logfile.path().parent.parent / ALIGNED_COMBINED_FOLDER_NAME
        aligned_combined_file_name = AlignedCombinedFile.generate_file_name(
            logfile.img_duration(), logfile.img_number()
        )
        aligned_combined_file = AlignedCombinedFile(
            aligned_combined_folder / aligned_combined_file_name
        )
        bg_data_of_image = sky_bg_average_for_all_regions(
            aligned_combined_file.data(), SKY_BG_BOX_REGION_SIZE
        )
        image_number = aligned_combined_file.image_number()

        # Append tuple of result
        bg_data_of_all_images.append(
            (
                date_time_of_image,
                bg_data_of_image,
                image_number,
            )
        )

    sky_bg_file.create_file(
        bg_data_of_all_images,
        color_normfactors_title,
        color_normfactors_values,
        brightness_normfactors_title,
        brightness_normfactors_values,
        log_files_to_use[0].img_number(),
        log_files_to_use[-1].img_number(),
        normalized_cluster_angle,
    )
    logger.info("Completed generating sky background file")


def process_night(night: ConfigInputNight, config: Config, output: Path, night_date: date):  # noqa
    """
    Processes a given night of data based on the settings provided in `config` dict
    """
    # Save the config file used to do the current data processing
    CONFIG_PATH = output / CONFIG_FILE_NAME
    with CONFIG_PATH.open("w+") as fd:
        toml.dump(config, fd)

    # Number of expected rows and columns in all raw images
    rows, cols = config["image"]["rows"], config["image"]["columns"]
    radii_of_extraction = config["processing"]["radii_of_extraction"]
    image_duration = config["processing"]["image_duration"]

    log_file_path = output / get_log_file_name(night_date)
    # Clear file contents if exists, so that reprocessing a night wipes out
    # contents instead of appending to it
    if log_file_path.exists():
        log_file_path.unlink()

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
    logger.info(f"Starting processing for {night_date} with m23 version: {__version__}")

    ref_file_path = config["reference"]["file"]
    color_ref_file_path = config["reference"]["color"]

    reference_log_file = ReferenceLogFile(ref_file_path)
    logfile_combined_reference_logfile = LogFileCombinedFile(config["reference"]["logfile"])

    # Define relevant input folders for the night being processed
    NIGHT_INPUT_FOLDER: Path = night["path"]
    NIGHT_INPUT_CALIBRATION_FOLDER: Path = NIGHT_INPUT_FOLDER / INPUT_CALIBRATION_FOLDER_NAME
    NIGHT_INPUT_IMAGES_FOLDER = NIGHT_INPUT_FOLDER / M23_RAW_IMAGES_FOLDER_NAME

    # Define and create relevant output folders for the night being processed
    JUST_ALIGNED_NOT_COMBINED_OUTPUT_FOLDER = output / ALIGNED_FOLDER_NAME
    CALIBRATION_OUTPUT_FOLDER = output / OUTPUT_CALIBRATION_FOLDER_NAME
    ALIGNED_COMBINED_OUTPUT_FOLDER = output / ALIGNED_COMBINED_FOLDER_NAME
    LOG_FILES_COMBINED_OUTPUT_FOLDER = output / LOG_FILES_COMBINED_FOLDER_NAME
    FLUX_LOGS_COMBINED_OUTPUT_FOLDER = output / FLUX_LOGS_COMBINED_FOLDER_NAME
    RAW_CALIBRATED_OUTPUT_FOLDER = output / RAW_CALIBRATED_FOLDER_NAME

    for folder in [
        JUST_ALIGNED_NOT_COMBINED_OUTPUT_FOLDER,
        CALIBRATION_OUTPUT_FOLDER,
        RAW_CALIBRATED_OUTPUT_FOLDER,
        ALIGNED_COMBINED_OUTPUT_FOLDER,
        LOG_FILES_COMBINED_OUTPUT_FOLDER,
        FLUX_LOGS_COMBINED_OUTPUT_FOLDER,
    ]:
        if folder.exists():
            [file.unlink() for file in folder.glob("*") if file.is_file()]  # Remove existing files
        folder.mkdir(exist_ok=True)

    # Darks
    darks = fit_data_from_fit_images(get_darks(NIGHT_INPUT_CALIBRATION_FOLDER, image_duration))
    # Ensure that image dimensions are as specified by rows and cols
    # If there's extra noise cols or rows, we crop them
    # Note this is different from the crop_region that's defined in image
    # options for process. More than crop, it's a fill that fills out the
    # vignetting ring with zero values
    darks = [crop(matrix, rows, cols) for matrix in darks]
    master_dark_data = makeMasterDark(
        saveAs=CALIBRATION_OUTPUT_FOLDER / MASTER_DARK_NAME,
        headerToCopyFromName=next(
            get_darks(NIGHT_INPUT_CALIBRATION_FOLDER, image_duration)
        ).absolute(),
        listOfDarkData=darks,
    )
    logger.info("Created master dark")
    del darks  # Deleting to free memory as we don't use darks anymore

    # Flats
    if night.get("masterflat"):
        master_flat_data = getdata(night["masterflat"])
        # Copy the masterflat provided to the calibration frames
        masterflat_path = Path(night["masterflat"])
        shutil.copy(masterflat_path, CALIBRATION_OUTPUT_FOLDER)
        logger.info("Using pre-provided masterflat")
    else:
        # Note the order is important when generating masterflat
        flats = fit_data_from_fit_images(
            sorted_by_number(get_flats(NIGHT_INPUT_CALIBRATION_FOLDER, image_duration))
        )  # noqa
        # Ensure that image dimensions are as specified by rows and cols
        # If there's extra noise cols or rows, we crop them
        flats = [crop(matrix, rows, cols) for matrix in flats]

        master_flat_data = makeMasterFlat(
            saveAs=CALIBRATION_OUTPUT_FOLDER / MasterflatFile.generate_file_name(night_date),
            masterDarkData=master_dark_data,
            headerToCopyFromName=next(
                get_flats(NIGHT_INPUT_CALIBRATION_FOLDER)
            ).absolute(),  # Gets absolute path of first flat file
            listOfFlatData=flats,
        )
        logger.info("Created masterflat")
        del flats  # Deleting to free memory as we don't use flats anymore

    raw_images: List[RawImageFile] = list(
        get_raw_images(NIGHT_INPUT_IMAGES_FOLDER, image_duration)
    )
    logger.info("Processing images")
    no_of_images_to_combine = config["processing"]["no_of_images_to_combine"]
    logger.info(f"Using no of images to combine: {no_of_images_to_combine}")
    logger.info(f"Radii of extraction: {radii_of_extraction}")

    # We now Calibrate/Crop/Align/Combine/Extract set of images in the size of no of combination
    # Note the subtle typing difference between no_of_combined_images and no_of_images_to_combine
    no_of_combined_images = len(raw_images) // no_of_images_to_combine

    # Create a file for storing alignment transformation
    alignment_stats_file_name = AlignmentStatsFile.generate_file_name(night_date)
    alignment_stats_file = AlignmentStatsFile(output / alignment_stats_file_name)
    alignment_stats_file.create_file_and_write_header()
    logger.info("Created alignment stats file")

    log_files_to_normalize: List[LogFileCombinedFile] = []
    for nth_combined_image in range(no_of_combined_images):
        try:
            align_combined_extract(
                config,
                night,
                output,
                night_date,
                nth_combined_image,
                raw_images,
                master_dark_data,
                master_flat_data,
                alignment_stats_file,
                image_duration,
                log_files_to_normalize,
            )
        except Exception as e:
            tb = traceback.format_exc()
            logger.error("Exception during alignment combination extraction")
            logger.error(e)
            logger.error(tb)
            return

    # Intranight + Internight Normalization
    try:
        normalization_helper(
            radii_of_extraction,
            reference_log_file,
            log_files_to_normalize,
            image_duration,
            night_date,
            color_ref_file_path,
            output,
            logfile_combined_reference_logfile,
            is_running_as_part_of_process=True,
        )
    except Exception as e:
        tb = traceback.format_exc()
        logger.error("Exception during normalization/sky_bg generation")
        logger.error(e)
        logger.debug(tb)
        return


def start_data_processing_auxiliary(config: Config):
    """
    This function processes (one or more) nights defined in config dict by
    putting together various functionalities like calibration, alignment,
    extraction, and normalization together.
    """

    OUTPUT_PATH: Path = config["output"]["path"]
    # If directory doesn't exist create directory including necessary parent directories.
    OUTPUT_PATH.mkdir(parents=True, exist_ok=True)

    def process_nights_mapper(night):
        night_path: Path = night["path"]
        night_date = get_date_from_input_night_folder_name(night_path.name)
        OUTPUT_NIGHT_FOLDER = OUTPUT_PATH / get_output_folder_name_from_night_date(night_date)
        # Create output folder for the night, if it doesn't already exist
        OUTPUT_NIGHT_FOLDER.mkdir(exist_ok=True)
        process_night(night, config, OUTPUT_NIGHT_FOLDER, night_date)

    cpu_fraction = config["processing"]["cpu_fraction"]
    if cpu_fraction > 0:
        cpu_count = int(os.cpu_count() * cpu_fraction)
        print(f"Multiprocessing module used. CPU count: {cpu_count}")
        with mp.Pool(cpu_count) as p:  # Use 75% CPU
            p.map(process_nights_mapper, config["input"]["nights"])
    else:
        # Dont use multiprocessing
        for night in config["input"]["nights"]:
            print("Using single processor.")
            process_nights_mapper(night)


def start_data_processing(file_path: str):
    """
    Starts data processing with the configuration file `file_path` provided as the argument.
    Calls auxiliary function `start_data_processing_auxiliary` if the configuration is valid.
    """
    validate_file(Path(file_path), on_success=start_data_processing_auxiliary)
