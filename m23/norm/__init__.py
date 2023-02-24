import math
from datetime import date
from pathlib import Path
from typing import List

import numpy as np

from .get_line import get_star_to_ignore_bit_vector
from m23.file.flux_log_combined_file import FluxLogCombinedFile
from m23.file.log_file_combined_file import LogFileCombinedFile
from m23.file.normfactor_file import NormfactorFile
from m23.file.reference_log_file import ReferenceLogFile


# TODO: Mask out stars with center pixel not matching + crop the outlier stars using linfit
def normalize_log_files(
    reference_log_file: ReferenceLogFile,
    log_files_to_normalize: List[LogFileCombinedFile],
    output_folder : Path,
    radius: int,
    img_duration: float,
    night_date: date
):
    """
    This function normalizes (intra night *not* inter night) the LogFilesCombined files provided.
    Note that the normalization **isn't** done with respect to the data in the reference image
    but with respect to some sample images take throughout the night.

    Note that this code assumes that the all stars in the log files are available in
    reference log file and no more or less.
    """
    # We are sorting the log files so that we know what's the first logfile 
    # we are using and what's the last. This data is needed written in header
    # of all flux log combined files that we create
    log_files_to_normalize.sort(key=lambda log_file : log_file.img_number())

    no_of_files = len(log_files_to_normalize)

    # Normalization is done with reference to images 20%, 40%, 60% and 80% throughout night
    # The indices here are the index of the images from the night to which to normalize.
    # Note, we aren't normalizing with reference to the ref file
    indices_to_normalize_to = np.linspace(0, no_of_files, 6, dtype="int")[1:-1]
    log_files_to_which_all_other_logfiles_are_normalized_to  = np.array(log_files_to_normalize, dtype="object")[indices_to_normalize_to]

    # Get the ADUs of the logfiles based on which normalization is to be done
    adus_in_data_to_normalize_to = np.array(
        [logfile.get_adu(radius) for logfile in log_files_to_which_all_other_logfiles_are_normalized_to]
    )

    # Matrix of image by star so 4th star in 100th image will be normalized_star_data[99][3]
    normalized_star_data = np.zeros((no_of_files, len(reference_log_file)))

    # This holds the normalization factor for each log_file to use
    all_norm_factors = []

    for file_index, log_file in enumerate(log_files_to_normalize):

        adu_of_current_log_file = log_files_to_normalize[file_index].get_adu(radius)

        # Perform linear fits, cropping in 12 pixels from stars closest to the four corners
        # creating a quadrilateral region, and excluding stars outside of this area
        # Returns the updated list of star coordinates
        stars_to_ignore_bit_vector = get_star_to_ignore_bit_vector(log_file)

        # Mask out stars with center more than 1 pixel away from those in the ref file
        # also mask if the star is outside the 12px box around the image
        for star_index in range(len(log_file)):
            # Note not to be confused between logfile and reference file here we call logfile 
            # combined that's to be normalized as logfile and the reference file that we use 
            # to look up the standard positions of star as reference file
            star_no = star_index + 1
            
            # Mark the adu of the star as 0 if that's to be ignored
            if stars_to_ignore_bit_vector[star_index] == 0: 
                adu_of_current_log_file[star_index] = 0
                continue # We go to the next star in the for loop as we already know ADU for this star for this image

            star_data_in_log_file = log_file.get_star_data(star_no)
            star_x_reffile, star_y_reffile = reference_log_file.get_star_xy(star_no)
            star_x_position, star_y_position = star_data_in_log_file.x, star_data_in_log_file.y
            
            if math.sqrt((star_x_reffile - star_x_position) ** 2 + (star_y_reffile - star_y_position) ** 2) > 1:
                adu_of_current_log_file[star_index] = 0
            

        # Normalization factor is the median of the scale_factors of all stars for scale_factors <= 5
        # where scale_factor for a star for that image is 
        # star's adu in sum of data_to_normalize_to divided by 4 * adu in current image
        # Note that use are finding normalization factors for all stars at once using numpy's array division
        # Note that we're multiplying the sum by the bit vector to that we ignore all the stars that are to ignored
        sum_of_adus_in_data_to_normalize_to = np.sum(adus_in_data_to_normalize_to, axis=0) * stars_to_ignore_bit_vector
        scale_factors_for_stars = sum_of_adus_in_data_to_normalize_to / (
            4 * adu_of_current_log_file
        )
        # Only get the median value for scale factors between 0 and 5, since some values are -inf or nan
        # We get the upper threshold 5 from the IDL code
        # good_scale_factors = scale_factors_for_stars[
        #     np.where((scale_factors_for_stars < 5) & (scale_factors_for_stars > 0))
        # ]
        good_scale_factors = scale_factors_for_stars[
            np.where((scale_factors_for_stars > 0) & (scale_factors_for_stars <= 5))
        ]
        breakpoint()

        # Now the norm factor for the image is the median of norm factors for all the stars in that image
        norm_factor = np.median(good_scale_factors) if len(good_scale_factors) > 0 else 0
        all_norm_factors.append(norm_factor)
        # We now apply the normalization for all stars in the image and save it in our multidimensional array
        normalized_star_data[file_index] = norm_factor * adu_of_current_log_file

    # Save normfactors
    normfactors_file_name = NormfactorFile.generate_file_name(night_date, img_duration)
    normfactor_file = NormfactorFile(output_folder / normfactors_file_name)
    normfactor_file.create_file(all_norm_factors)

    # Save the normalized data for each star
    noOfStars = len(normalized_star_data[0])
    for star_index in range(noOfStars):
        star_no = star_index + 1
        star_data = [
            normalized_star_data[file_index][star_index] for file_index in range(no_of_files)
        ]
        # Turn all star_data that's negative to 0
        star_data = [current_data if current_data > 0 else 0 for current_data in star_data]

        # We now create flux log combined file
        flux_log_combined_file_name = FluxLogCombinedFile.generate_file_name(night_date, star_no, img_duration)
        flux_log_combined_file = FluxLogCombinedFile(output_folder / flux_log_combined_file_name)

        fist_log_file_number = log_files_to_normalize[0].img_number()
        last_log_file_number = log_files_to_normalize[-1].img_number()

        # To write x,y position, we use the position from the first log file
        x_position = log_files_to_normalize[0].get_star_data(star_no).x
        y_position = log_files_to_normalize[0].get_star_data(star_no).y

        flux_log_combined_file.create_file(star_data, fist_log_file_number, last_log_file_number, (x_position, y_position), reference_log_file)
