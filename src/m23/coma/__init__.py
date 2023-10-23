from typing import Dict, List, Tuple
from pathlib import Path

from m23.constants import (
    ALIGNED_COMBINED_FOLDER_NAME,
    COMA_PATCH_SIZE,
    COMA_PSF_SIZE,
    COMA_EPSILON,
    COMA_ALPHA
)
from m23.file.raw_image_file import RawImageFile
from m23.file.aligned_combined_file import AlignedCombinedFile
from m23.file.log_file_combined_file import LogFileCombinedFile
import numpy as np
import regularizepsf as rpsf


def coma_correction(
    output: Path,
    logfiles: List[LogFileCombinedFile]
    ):
    """
    Returns a function that takes raw image of type RawImageFile and returns
    its corrected image corrected using appropriate coma correction model

    Preconditions:
        1. Aligned combined images are generated and available in appropriate folder 
        without performing coma correction.
    """

    # Calculate target fwhm for the night
    xfwhm_target, yfwhm_target = best_fwhm_from_the_night(logfiles)

    ALIGNED_COMBINED_OUTPUT_FOLDER = output / ALIGNED_COMBINED_FOLDER_NAME

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
    coma_correction_models : Dict[str, rpsf.ArrayCorrector] = {}

    for name, aligned_images in group_of_aligned_combined.items():
        # Sort the aligned images so that we can choose the aligned combined
        # file from the middle of the hour as the sample
        aligned_images.sort(key=lambda x: x.image_number())
        mid_aligned_image = aligned_images[len(aligned_images) // 2]
        # Find the raw images associated with that image.
        raw_images_paths = [x.path() for x in mid_aligned_image.raw_images]
        # Create correction model based on the given raw images 
        coma_correction_models[name] = make_coma_correction_model(
            raw_images_paths, xfwhm_target, yfwhm_target
        )

    def get_corrected_data_for(raw_img : RawImageFile):
        data = raw_img.data()
        group_name = coma_group_name_for_image(raw_img)
        ac = coma_correction_models.get(group_name, None)
        # If there is no array corrector, return the uncorrected data 
        # Users can find out that uncorrected image was returned if 
        # the result returned and data are the same object.
        if ac is None:
            return data
        corrected_image = ac.correct_image(data, alpha=COMA_ALPHA, epsilon=COMA_EPSILON).copy(order='C')
        return corrected_image

    return get_corrected_data_for
    


def coma_group_name_for_image(a: AlignedCombinedFile | RawImageFile) -> str:
    """
    Return the group name for the aligned combined file to be used in coma
    correction Aligned combined files that have the same coma group use the
    same correction model. 
    Beware though that its the raw images in the aligned combined file on which
    coma correction model is applied not the aligned combined file.
    """
    d = a.datetime()
    if d is None:
        raise Exception("No datetime found in aligned combine file", a)
    # Since we want images from the same hour to have the same coma correction 
    # model, our group name is day of month followed by the hour of day.
    # Note that we also keep day of month as a safety mechanism when some
    # data runs could be as long as 12 hours.
    return d.strftime("%d-%H")



def make_coma_correction_model(images: List[str]|List[Path], xfwhm_target: float, yfwhm_target: float) -> rpsf.ArrayCorrector:

    # Define the target PSF
    @rpsf.simple_psf
    def target(x, 
            y,
            x0=COMA_PATCH_SIZE/2, 
            y0=COMA_PATCH_SIZE/2,
            sigma_x=xfwhm_target/2.355, 
            sigma_y=yfwhm_target/2.355):
        return np.exp(-(np.square(x - x0) / (2 * np.square(sigma_x)) + np.square(y - y0) / (2 * np.square(sigma_y))))

    target_evaluation = target(*np.meshgrid(np.arange(COMA_PATCH_SIZE), np.arange(COMA_PATCH_SIZE)))

    # Extract all the stars from that image and create a PSF model with a target PSF
    image_paths = [str(p) for p in images]  # No support for pathlib.Path yet
    cpc = rpsf.CoordinatePatchCollection.find_stars_and_average(image_paths, COMA_PSF_SIZE, COMA_PATCH_SIZE)

    return cpc.to_array_corrector(target_evaluation)


def best_fwhm_from_the_night(logfiles: List[LogFileCombinedFile]) -> Tuple[float, float]:
    """
    Returns the best X_FWHM and Y_FWHM from the list of logfiles 
    The best is chosen by sorting the list by sum of XFWHM and YFWHM
    """
    assert len(logfiles) > 0
    fwhm : List[Tuple[float, float]] = []
    for logfile in logfiles:
        fwhm_x, fwhm_y = get_best_fwhm_in_logfile(logfile)
        fwhm.append((fwhm_x, fwhm_y))
    # Sort by the sum of X,Y FWHM
    fwhm.sort(key=lambda x: x[0]+x[1])
    return fwhm[0]


def get_best_fwhm_in_logfile(logfile: LogFileCombinedFile):
    """
    Divide the image into four squares, and return the median XFWHM, YFWHM of
    stars in the segment that looks the best
    """
    df = logfile.df
    xs, ys = df["X"], df["Y"]
    maxx = np.max(xs)
    maxy = np.max(ys)
    midx, midy = maxx // 2, maxy // 2

    # Here we assume origin to be at top left.
    fwhm : List[Tuple[float, float]] = []

    def add_median(frame):
        x, y = np.median(frame["XFWHM"]), np.median(frame["YFWHM"])
        fwhm.append((x, y))


    # Top Left
    df_top_left = df.loc[(df["X"] <= midx) & (df["Y"] <= midy) & (df["XFWHM"]>0) & (df["YFWHM"]>0)]
    add_median(df_top_left)
     
    # Bottom Left
    df_bottom_left = df.loc[(df["X"] <= midx) & (df["Y"] > midy) & (df["XFWHM"]>0) & (df["YFWHM"]>0)]
    add_median(df_bottom_left)

    # Top Right
    df_top_right = df.loc[(df["X"] > midx) & (df["Y"] <= midy) & (df["XFWHM"]>0) & (df["YFWHM"]>0)]
    add_median(df_top_right)

    # Bottom Right
    df_bottom_right = df.loc[(df["X"] > midx) & (df["Y"] > midy) & (df["XFWHM"]>0) & (df["YFWHM"]>0)]
    add_median(df_bottom_right)

    # Return the one set of X,Y FWHM where the sum is the smallest
    fwhm.sort(key=lambda x: x[0] + x[0])
    return fwhm[0]