import logging
from datetime import timedelta
from pathlib import Path

import numpy as np

from m23.align import image_alignment
from m23.calibrate.calibration import calibrateImages
from m23.constants import (
    ALIGNED_COMBINED_FOLDER_NAME,
    ALIGNED_FOLDER_NAME,
    LOG_FILES_COMBINED_FOLDER_NAME,
    M23_RAW_IMAGES_FOLDER_NAME,
    RAW_CALIBRATED_FOLDER_NAME,
)
from m23.exceptions import CouldNotAlignException
from m23.extract import extract_stars
from m23.file.aligned_combined_file import AlignedCombinedFile
from m23.file.log_file_combined_file import LogFileCombinedFile
from m23.file.raw_image_file import RawImageFile
from m23.file.reference_log_file import ReferenceLogFile
from m23.matrix import crop
from m23.matrix.fill import fillMatrix
from m23.processor.config_loader import Config, ConfigInputNight
from m23.utils import time_taken_to_capture_and_save_a_raw_file


def align_combined_extract(
    config: Config,
    night: ConfigInputNight,
    output: Path,
    night_date,
    nth_combined_image,
    raw_images,
    master_dark_data,
    master_flat_data,
    alignment_stats_file,
    image_duration,
    log_files_to_normalize,
):
    logger = logging.getLogger("LOGGER_" + str(night_date))

    # Define relevant input folders for the night being processed
    NIGHT_INPUT_FOLDER: Path = night["path"]
    NIGHT_INPUT_IMAGES_FOLDER = NIGHT_INPUT_FOLDER / M23_RAW_IMAGES_FOLDER_NAME

    # Define and create relevant output folders for the night being processed
    JUST_ALIGNED_NOT_COMBINED_OUTPUT_FOLDER = output / ALIGNED_FOLDER_NAME
    ALIGNED_COMBINED_OUTPUT_FOLDER = output / ALIGNED_COMBINED_FOLDER_NAME
    LOG_FILES_COMBINED_OUTPUT_FOLDER = output / LOG_FILES_COMBINED_FOLDER_NAME
    RAW_CALIBRATED_OUTPUT_FOLDER = output / RAW_CALIBRATED_FOLDER_NAME

    ref_image_path = config["reference"]["image"]
    ref_file_path = config["reference"]["file"]
    reference_log_file = ReferenceLogFile(ref_file_path)
    rows, cols = config["image"]["rows"], config["image"]["columns"]
    no_of_images_to_combine = config["processing"]["no_of_images_to_combine"]

    crop_region = config["image"]["crop_region"]
    save_aligned_images = config["output"]["save_aligned"]
    save_calibrated_images = config["output"]["save_calibrated"]
    radii_of_extraction = config["processing"]["radii_of_extraction"]

    from_index = nth_combined_image * no_of_images_to_combine
    # Note the to_index is exclusive
    to_index = (nth_combined_image + 1) * no_of_images_to_combine

    # NOTE
    # It's very easy to get confused between no_of_combined_images
    # and the no_of_images_to_combine. The later is the number of raw images
    # that are combined together to form on aligned combined image

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

    if save_calibrated_images:
        for index, raw_image_index in enumerate(range(from_index, to_index)):
            raw_img = raw_images[raw_image_index]
            calibrated_image = RawImageFile(RAW_CALIBRATED_OUTPUT_FOLDER / raw_img.path().name)
            calibrated_image.create_file(images_data[index], raw_img)
            logger.info(f"Saving calibrated image. {raw_image_index}")

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

            # Note that we're down-scaling the matrix dtype from float to int32 for
            # support in the image viewing softwares. For the combination step though
            # we are using the more precise float data. This means that if you read
            # the data of the aligned images from the fit file and combined them yourself
            # that is going to be off by a small amount that the data in the aligned
            # combined image.
            aligned_image = RawImageFile(
                JUST_ALIGNED_NOT_COMBINED_OUTPUT_FOLDER / raw_image_to_align_name
            )

            if save_aligned_images:
                aligned_image.create_file(aligned_data.astype("int32"), raw_image_to_align)

            alignment_stats_file.add_record(raw_image_to_align_name, statistics)
            logger.info(f"Aligned {raw_image_to_align_name}")
        except CouldNotAlignException as e:
            logger.error(f"Could not align image {raw_image_to_align}")
            logger.error(f"Skipping combination {from_index}-{to_index}")
            logger.error(f"{e}")
            break
        except Exception as e:
            logger.error(f"Could not align image {raw_image_to_align}")
            logger.error(f"Skipping combination {from_index}-{to_index}")
            logger.error(f"{e}")
            break

    # We proceed to next set of images if the alignment wasn't successful for any one
    # image in the combination set. We now this by checking no of aligned images.
    if len(aligned_images_data) < no_of_images_to_combine:
        logger.warning(
            f"Length of aligned images {len(aligned_images_data)}. No of images to combined: {no_of_images_to_combine}"  # noqa
        )
        logger.warning("Skipping align-combine-extract")
        return

    # Combination
    combined_images_data = np.sum(aligned_images_data, axis=0)
    logger.info("Combined")

    # We take the middle image from the combination as the sample This is
    # the image whose header will be copied to the combined image fit file
    midpoint_index = from_index + no_of_images_to_combine // 2
    sample_raw_image_file = raw_images[midpoint_index]
    logger.info(f"Using {sample_raw_image_file} as sample")

    aligned_combined_image_number = to_index // no_of_images_to_combine
    logger.info(f"Aligned combined image number {aligned_combined_image_number}")
    aligned_combined_file_name = AlignedCombinedFile.generate_file_name(
        image_duration, aligned_combined_image_number
    )
    logger.info(f"Aligned combined image name {aligned_combined_file_name}")
    aligned_combined_file = AlignedCombinedFile(
        ALIGNED_COMBINED_OUTPUT_FOLDER / aligned_combined_file_name
    )
    # Image viewing softwares like Astromagic and Fits Liberator don't work
    # if the image data type is float, for some reason that we don't know.
    # So we're setting the datatype to int32 which has enough precision for
    # us.
    aligned_combined_file.create_file(combined_images_data.astype("int32"), sample_raw_image_file)
    logger.info(f"Set {aligned_combined_file_name} dtype to int32")
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
    logger.info(f"Using datetime {date_time_to_use} for extraction")

    extract_stars(
        combined_images_data,
        reference_log_file,
        radii_of_extraction,
        log_file_combined_file,
        aligned_combined_file,
        date_time_to_use,
    )

    logger.info(f"Extraction from combination {from_index}-{to_index} completed")
    log_files_to_normalize.append(log_file_combined_file)


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
        duration_of_raw_img = time_taken_to_capture_and_save_a_raw_file(
            raw_images_folder, night_config
        )
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
