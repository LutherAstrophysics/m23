import logging
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Iterable, List

import numpy as np
import toml
from astropy.io.fits import getdata
from m23.align import image_alignment
from m23.calibrate.calibration import calibrateImages
from m23.calibrate.master_calibrate import makeMasterDark
from m23.charts import draw_normfactors_chart
from m23.constants import (ALIGNED_COMBINED_FOLDER_NAME, ALIGNED_FOLDER_NAME,
                           CONFIG_FILE_NAME, FLUX_LOGS_COMBINED_FOLDER_NAME,
                           INPUT_CALIBRATION_FOLDER_NAME,
                           LOG_FILES_COMBINED_FOLDER_NAME,
                           M23_RAW_IMAGES_FOLDER_NAME, MASTER_DARK_NAME,
                           MASTER_FLAT_NAME, OUTPUT_CALIBRATION_FOLDER_NAME,
                           SKY_BG_BOX_REGION_SIZE, SKY_BG_FOLDER_NAME)
from m23.exceptions import CouldNotAlignException
from m23.extract import extract_stars, sky_bg_average_for_all_regions
from m23.file.aligned_combined_file import AlignedCombinedFile
from m23.file.alignment_stats_file import AlignmentStatsFile
from m23.file.log_file_combined_file import LogFileCombinedFile
from m23.file.raw_image_file import RawImageFile
from m23.file.reference_log_file import ReferenceLogFile
from m23.file.sky_bg_file import SkyBgFile
from m23.internight_normalize import internight_normalize
from m23.matrix import crop
from m23.matrix.fill import fillMatrix
from m23.norm import normalize_log_files
from m23.processor.config_loader import Config, ConfigInputNight, validate_file
from m23.utils import (fit_data_from_fit_images, get_darks,
                       get_date_from_input_night_folder_name, get_flats,
                       get_log_file_name,
                       get_output_folder_name_from_night_date,
                       get_radius_folder_name, get_raw_images,
                       time_taken_to_capture_and_save_a_raw_file)


def normalization_helper(
    radii_of_extraction: List[int],
    reference_log_file: ReferenceLogFile,
    log_files_to_use: List[LogFileCombinedFile],
    img_duration: float,
    night_date: date,
    color_ref_file_path: Path,
    output: Path,
    logfile_combined_reference_logfile: LogFileCombinedFile,
):
    """
    This is a normalization helper function extracted so that it can be reused
    by the renormalization script
    """
    FLUX_LOGS_COMBINED_OUTPUT_FOLDER = output / FLUX_LOGS_COMBINED_FOLDER_NAME
    logger = logging.getLogger("LOGGER_" + str(night_date))

    if len(log_files_to_use) < 4:
        logger.error(f"Less than 4 data points present. Skipping normalization.")
        return

    for radius in radii_of_extraction:
        logger.info(f"Normalizing for radius of extraction {radius} px")
        RADIUS_FOLDER = FLUX_LOGS_COMBINED_OUTPUT_FOLDER / get_radius_folder_name(radius)
        RADIUS_FOLDER.mkdir(exist_ok=True)  # Create folder if it doesn't exist
        for file in RADIUS_FOLDER.glob("*"):
            if file.is_file():
                file.unlink()  # Remove each file in the folder
        normalize_log_files(
            reference_log_file,
            log_files_to_use,
            RADIUS_FOLDER,
            radius,
            img_duration,
            night_date,
        )

    draw_normfactors_chart(log_files_to_use, FLUX_LOGS_COMBINED_OUTPUT_FOLDER.parent)

    # Generate sky bg file
    sky_bg_filename = output / SKY_BG_FOLDER_NAME / SkyBgFile.generate_file_name(night_date)

    # Internight normalization
    normfactors = internight_normalize(
        output,
        logfile_combined_reference_logfile,
        color_ref_file_path,
        radii_of_extraction,
    )

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
    )


def create_sky_bg_file(
    sky_bg_file: SkyBgFile,
    log_files_to_use: Iterable[LogFileCombinedFile],
    night_date: date,
    color_normfactors_title: Iterable[str],
    color_normfactors_values: Iterable[float],
    brightness_normfactors_title: Iterable[str],
    brightness_normfactors_values: Iterable[float],
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

    for index, logfile in enumerate(log_files_to_use):
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
    )
    logger.info("Completed generating sky background file")


def get_datetime_to_use(
    aligned_combined: AlignedCombinedFile,
    night_config: ConfigInputNight,
    no_of_raw_images_in_one_combination: int,
    raw_images_folder: Path,
) -> str:
    """
    Returns the datetime to use in the logfile combined file,
    based on the a given `config` and `aligned_combine` file

    Returns an empty string if no datetime is available to use
    """

    # We use the same format of the datetime string as is in the
    # header of our fit files
    datetime_format = aligned_combined.date_observed_datetime_format

    # If the datetime option was passed in the header we use that one
    # Otherwise we use the datetime in the header, if that's present
    if start := night_config.get("starttime"):
        duration_of_raw_img = time_taken_to_capture_and_save_a_raw_file(raw_images_folder)
        img_no = aligned_combined.image_number()
        time_taken_to_capture_one_combined_image = (
            duration_of_raw_img * no_of_raw_images_in_one_combination
        )
        seconds_elapsed_from_beginning_of_night = (
            time_taken_to_capture_one_combined_image * (img_no - 1)
            + time_taken_to_capture_one_combined_image * 0.5
        )
        return (start + timedelta(seconds=seconds_elapsed_from_beginning_of_night)).strftime(
            datetime_format
        )
    elif datetime_in_aligned_combined := aligned_combined.datetime():
        return datetime_in_aligned_combined.strftime(datetime_format)
    else:
        return ""


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
    logger.info(f"Starting processing for {night_date}")

    ref_image_path = config["reference"]["image"]
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

    for folder in [
        JUST_ALIGNED_NOT_COMBINED_OUTPUT_FOLDER,
        CALIBRATION_OUTPUT_FOLDER,
        ALIGNED_COMBINED_OUTPUT_FOLDER,
        LOG_FILES_COMBINED_OUTPUT_FOLDER,
        FLUX_LOGS_COMBINED_OUTPUT_FOLDER,
    ]:
        if folder.exists():
            [file.unlink() for file in folder.glob("*") if file.is_file()]  # Remove existing files
        folder.mkdir(exist_ok=True)

    crop_region = config["image"]["crop_region"]

    # Darks
    darks = fit_data_from_fit_images(get_darks(NIGHT_INPUT_CALIBRATION_FOLDER))
    # Ensure that image dimensions are as specified by rows and cols
    # If there's extra noise cols or rows, we crop them
    darks = [crop(matrix, rows, cols) for matrix in darks]
    master_dark_data = makeMasterDark(
        saveAs=CALIBRATION_OUTPUT_FOLDER / MASTER_DARK_NAME,
        headerToCopyFromName=next(get_darks(NIGHT_INPUT_CALIBRATION_FOLDER)).absolute(),
        listOfDarkData=darks,
    )
    logger.info("Created master dark")
    del darks  # Deleting to free memory as we don't use darks anymore

    # Flats
    if night.get("masterflat"):
        master_flat_data = getdata(night["masterflat"])
        logger.info("Using pre-provided masterflat")
    else:
        flats = fit_data_from_fit_images(get_flats(NIGHT_INPUT_CALIBRATION_FOLDER))
        # Ensure that image dimensions are as specified by rows and cols
        # If there's extra noise cols or rows, we crop them
        flats = [crop(matrix, rows, cols) for matrix in flats]

        master_flat_data = makeMasterDark(
            saveAs=CALIBRATION_OUTPUT_FOLDER / MASTER_FLAT_NAME,
            headerToCopyFromName=next(
                get_flats(NIGHT_INPUT_CALIBRATION_FOLDER)
            ).absolute(),  # Gets absolute path of first flat file
            listOfDarkData=flats,
        )
        logger.info("Created masterflat")
        del flats  # Deleting to free memory as we don't use flats anymore

    raw_images: List[RawImageFile] = list(get_raw_images(NIGHT_INPUT_IMAGES_FOLDER))
    image_duration = raw_images[0].image_duration()
    logger.info("Processing images")
    no_of_images_to_combine = config["processing"]["no_of_images_to_combine"]
    logger.info(f"Using no of images to combine: {no_of_images_to_combine}")
    logger.info(f"Radii of extraction: {radii_of_extraction}")

    # We now Calibrate/Crop/Align/Combine/Extract set of images in the size of no of combination
    # Note the subtle typing difference between no_of_combined_images and no_of_images_to_combine
    no_of_combined_images = len(raw_images) // no_of_images_to_combine

    log_files_to_normalize: List[LogFileCombinedFile] = []

    # Create a file for storing alignment transformation
    alignment_stats_file_name = AlignmentStatsFile.generate_file_name(night_date)
    alignment_stats_file = AlignmentStatsFile(output / alignment_stats_file_name)
    alignment_stats_file.create_file_and_write_header()

    for i in range(no_of_combined_images):
        # NOTE
        # It's very easy to get confused between no_of_combined_images
        # and the no_of_images_to_combine. THe later is the number of raw images
        # that are combined together to form on aligned combined image

        from_index = i * no_of_images_to_combine
        # Note the to_index is exclusive
        to_index = (i + 1) * no_of_images_to_combine

        images_data = [raw_image_file.data() for raw_image_file in raw_images[from_index:to_index]]
        # Ensure that image dimensions are as specified by rows and cols
        # If there's extra noise cols or rows, we crop them
        images_data = [crop(matrix, rows, cols) for matrix in images_data]

        # Calibrate images
        images_data = calibrateImages(
            masterDarkData=master_dark_data,
            masterFlatData=master_flat_data,
            listOfImagesData=images_data,
        )

        # Fill out the cropped regions with value of 1
        # Note, it's important to fill after the calibration step
        if len(crop_region) > 0:
            images_data = [fillMatrix(matrix, crop_region, 1) for matrix in images_data]

        # Alignment
        # We want to discard this set of images if any one image in this set cannot be aligned
        aligned_images_data = []
        for index, image_data in enumerate(images_data):
            raw_image_to_align = raw_images[from_index + index]
            raw_image_to_align_name = raw_image_to_align.path().name
            try:
                aligned_data, statistics = image_alignment(image_data, ref_image_path)
                aligned_images_data.append(aligned_data)
                # We add the transformation statistics to the alignment stats
                # file Information of the file that can't be aligned isn't
                # written only in the logfile. This is intended so that we can
                # easily process the alignment stats file if we keep it in a TSV
                # like format

                # Note that we're down-scaling the matrix dtype from float to int16 for
                # support in the image viewing softwares. For the combination step though
                # we are using the more precise float data. This means that if you read
                # the data of the aligned images from the fit file and combined them yourself
                # that is going to be off by a small amount that the data in the aligned
                # combined image.
                aligned_image = RawImageFile(
                    JUST_ALIGNED_NOT_COMBINED_OUTPUT_FOLDER / raw_image_to_align_name
                )
                aligned_image.create_file(aligned_data.astype("int16"), raw_image_to_align)

                alignment_stats_file.add_record(raw_image_to_align_name, statistics)
                logger.info(f"Aligned {raw_image_to_align_name}")
            except CouldNotAlignException:
                logger.error(f"Could not align image {raw_image_to_align}")
                logger.error(f"Skipping combination {from_index}-{to_index}")
                break

        del images_data  # Delete unused object to free up memory

        # We proceed to next set of images if the alignment wasn't successful for any one
        # image in the combination set. We now this by checking no of aligned images.
        if len(aligned_images_data) < no_of_images_to_combine:
            continue

        # Combination
        combined_images_data = np.sum(aligned_images_data, axis=0)

        # We take the middle image from the combination as the sample This is
        # the image whose header will be copied to the combined image fit file
        midpoint_index = from_index + no_of_images_to_combine // 2
        sample_raw_image_file = raw_images[midpoint_index]

        aligned_combined_image_number = to_index // no_of_images_to_combine
        aligned_combined_file_name = AlignedCombinedFile.generate_file_name(
            image_duration, aligned_combined_image_number
        )
        aligned_combined_file = AlignedCombinedFile(
            ALIGNED_COMBINED_OUTPUT_FOLDER / aligned_combined_file_name
        )
        # Image viewing softwares like Astromagic and Fits Liberator don't work
        # if the image data type is float, for some reason that we don't know.
        # So we're setting the datatype to int32 which has enough precision for
        # us. Note int16 is problematic as our combined images ADU are bigger
        # than 2^16
        # Note that for extraction though, we use the same, more precise format
        # that we have
        aligned_combined_file.create_file(
            combined_images_data.astype("int32"), sample_raw_image_file
        )
        logger.info(f"Combined images {from_index}-{to_index}")

        # Extraction
        log_file_combined_file_name = LogFileCombinedFile.generate_file_name(
            night_date, aligned_combined_image_number, image_duration
        )
        log_file_combined_file = LogFileCombinedFile(
            LOG_FILES_COMBINED_OUTPUT_FOLDER / log_file_combined_file_name
        )

        date_time_to_use = get_datetime_to_use(
            aligned_combined_file, night, no_of_images_to_combine, NIGHT_INPUT_IMAGES_FOLDER
        )

        extract_stars(
            combined_images_data,
            reference_log_file,
            radii_of_extraction,
            log_file_combined_file,
            aligned_combined_file,
            date_time_to_use,
        )
        log_files_to_normalize.append(log_file_combined_file)
        logger.info(f"Extraction from combination {from_index}-{to_index} completed")

    # Intranight + Internight Normalization
    normalization_helper(
        radii_of_extraction,
        reference_log_file,
        log_files_to_normalize,
        image_duration,
        night_date,
        color_ref_file_path,
        output,
        logfile_combined_reference_logfile,
    )


def start_data_processing_auxiliary(config: Config):
    """
    This function processes (one or more) nights defined in config dict by
    putting together various functionalities like calibration, alignment,
    extraction, and normalization together.
    """

    OUTPUT_PATH: Path = config["output"]["path"]
    # If directory doesn't exist create directory including necessary parent directories.
    OUTPUT_PATH.mkdir(parents=True, exist_ok=True)

    for night in config["input"]["nights"]:
        night_path: Path = night["path"]
        night_date = get_date_from_input_night_folder_name(night_path.name)
        OUTPUT_NIGHT_FOLDER = OUTPUT_PATH / get_output_folder_name_from_night_date(night_date)
        # Create output folder for the night, if it doesn't already exist
        OUTPUT_NIGHT_FOLDER.mkdir(exist_ok=True)
        process_night(night, config, OUTPUT_NIGHT_FOLDER, night_date)


def start_data_processing(file_path: str):
    """
    Starts data processing with the configuration file `file_path` provided as the argument.
    Calls auxiliary function `start_data_processing_auxiliary` if the configuration is valid.
    """
    validate_file(Path(file_path), on_success=start_data_processing_auxiliary)
