from typing import Dict, List
from pathlib import Path

from m23.constants import (
    ALIGNED_COMBINED_FOLDER_NAME,
    LOG_FILES_COMBINED_FOLDER_NAME
)
from m23.file.raw_image_file import RawImageFile
from m23.file.aligned_combined_file import AlignedCombinedFile
from m23.processor.config_loader import Config

def coma_correction(
    config: Config, 
    output: Path,
    raw_images: List[RawImageFile]
    ):
    """
    Perform coma correction to raw images and re-generate aligned combined images

    Preconditions:
        1. Aligned combined images are generated and available in appropriate folder 
        without performing coma correction.

    Postconditions:
        1. Aligned combined images are generated and available in appropriate folder 
        **with** performing coma correction.

    Notes:
        1. Coma correction is done to raw images.
        2. Appropriate FWHM is used based on the FWHM of stars as found in LogFileCombinedFile
    """
    ALIGNED_COMBINED_OUTPUT_FOLDER = output / ALIGNED_COMBINED_FOLDER_NAME
    LOG_FILES_COMBINED_OUTPUT_FOLDER = output / LOG_FILES_COMBINED_FOLDER_NAME

    # Group aligned combined files based on the hour they're processed
    # This is because for each hour, we generate a new correction model
    group_of_aligned_combined : Dict[str, List[AlignedCombinedFile]] = {}

    for f in ALIGNED_COMBINED_OUTPUT_FOLDER.glob('*'):
        a = AlignedCombinedFile(f)
        if not a.is_valid_file_name():
            continue
        coma_group_name = coma_group_name_for_aligned_combined_file(a)
        if v := group_of_aligned_combined.get(coma_group_name):
            v.append(a)
        else:
            group_of_aligned_combined[coma_group_name] = [a] 

    # For each item in the group, generate a correction model based on the
    # aligned combined image in the middle. Note that the raw images
    # corresponding to that aligned combined image should be used in creating a
    # the coma model.

    coma_correction_models : Dict[str, _] = {}

    # It is important we clean the old files like Calibrated, Aligned,
    # AlignedCombined, etc. But need to make sure that deleting AlignedCombined
    # files doesn't do something unintended as we still hold indirect reference
    # to it via group_of_aligned_combined.

    # TODO

    # For each group
    # For each aligned combined image in the group
    # Apply coma correction to raw images then generate perform align combined extract
    # on those images.
    


def coma_group_name_for_aligned_combined_file(a: AlignedCombinedFile) -> str:
    """
    Return the group name for the aligned combined file to be used in coma
    correction Aligned combined files that have the same coma group use the
    same correction model. 
    Beware though that its the raw images in the aligned combined file on which
    coma correction model is applied not the aligned combined file.
    """
    d = a.datetime()
    if d is None:
        raise Exception("No datetile found in aligned combine file", a)
    # Since we want images from the same hour to have the same coma correction 
    # model, our group name is day of month followed by the hour of day.
    # Note that we also keep day of month as a safety mechanism when some
    # data runs could be as long as 12 hours.
    return d.strftime("%d-%H")
