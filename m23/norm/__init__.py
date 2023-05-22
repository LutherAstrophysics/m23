import math
from datetime import date
from pathlib import Path
from typing import List

import numpy as np

from m23.constants import INTRA_NIGHT_IMPACT_THRESHOLD_PIXELS
from m23.file.flux_log_combined_file import FluxLogCombinedFile
from m23.file.log_file_combined_file import LogFileCombinedFile
from m23.file.normfactor_file import NormfactorFile
from m23.file.reference_log_file import ReferenceLogFile

from .get_line import get_star_to_ignore_bit_vector


def normalize_log_files(
    reference_log_file: ReferenceLogFile,
    log_files_to_normalize: List[LogFileCombinedFile],
    output_folder : Path,
    radius: int,
    img_duration: float,
    night_date: date
):
    """
    This function normalizes (intra night *not* inter night) the
    LogFilesCombined files provided.  Note that the normalization **isn't** done
    with respect to the data in the reference image but with respect to some
    sample images take throughout the night.

    Note that this code assumes that the all stars in the log files are
    available in reference log file and no more or less.
    """

    # We are sorting the log files so that we know what's the first logfile 
    # we are using and what's the last. This data is needed written in header
    # of all flux log combined files that we create
    log_files_to_normalize.sort(key=lambda log_file : log_file.img_number())
    no_of_files = len(log_files_to_normalize)

    # Normalization is done with reference to images 20%, 40%, 60% and 80%
    # throughout night The indices here are the index of the images from the
    # night to which to normalize.  Note, we aren't normalizing with reference
    # to the ref file
    indices_to_normalize_to = np.linspace(0, no_of_files, 6, dtype="int")[1:-1]
    all_log_files = [] # This is an array of arrays

    # This holds the normalization factor for each log_file to use
    all_norm_factors = []

    for file_index, log_file in enumerate(log_files_to_normalize):

        adu_of_current_log_file = log_files_to_normalize[file_index].get_adu(radius)

        # Perform linear fits, cropping in 12 pixels from stars closest to the
        # four corners creating a quadrilateral region, and excluding stars
        # outside of this area
        stars_to_ignore_bit_vector = get_star_to_ignore_bit_vector(log_file, radius)

        # Mask out stars with center more than 1 pixel away from those in the
        # ref file also mask if the star is outside the 12px box around the
        # image
        for star_index in range(len(log_file)):
            # Note not to be confused between logfile and reference file here we
            # call logfile combined that's to be normalized as logfile and the
            # reference file that we use to look up the standard positions of
            # star as reference file
            star_no = star_index + 1

            # Mark the adu of the star as 0 if that's to be ignored
            if stars_to_ignore_bit_vector[star_index] == 0: 
                adu_of_current_log_file[star_index] = 0
                # We go to the next star in the for loop as we already know ADU for this star for this image
                continue 

            star_data_in_log_file = log_file.get_star_data(star_no)
            if not all([x > 0 for x in star_data_in_log_file.radii_adu.values()]) or star_data_in_log_file.sky_adu <= 0:
                adu_of_current_log_file[star_index] = 0 # Ignore this star for normfactor calc of this logfile
                continue

            star_x_reffile, star_y_reffile = reference_log_file.get_star_xy(star_no)
            star_x_position, star_y_position = star_data_in_log_file.x, star_data_in_log_file.y
            
            if math.sqrt((star_x_reffile - star_x_position) ** 2 + (star_y_reffile - star_y_position) ** 2) > INTRA_NIGHT_IMPACT_THRESHOLD_PIXELS:
                adu_of_current_log_file[star_index] = 0
            
        all_log_files.append(adu_of_current_log_file)
    
    # Now for each log file we calculate its normfactor
    # For each logfile, its normfactor is the median of normfactors of the stars
    # in that image.
    # For a star, it's normfactor in a logfile, is sum of adus in reference log file
    # divided by 4 * its adu
    reference_log_files = []
    for index, log_file in enumerate(all_log_files):
        if index in indices_to_normalize_to:
            reference_log_files.append(log_file)

    all_log_files = np.array(all_log_files) # Convert to numpy array
    reference_log_files = np.array(reference_log_files) # Convert to numpy array
    for file_index, log_file in enumerate(all_log_files):
        no_of_stars = len(log_file)
        norm_factor_for_stars = []
        for star_index in range(no_of_stars):
            star_adu_in_reference_log_files = []
            for ref_log_file in reference_log_files:
                star_adu_in_reference_log_files.append(ref_log_file[star_index])
            star_adu = log_file[star_index]
            if all([value > 0 for value in star_adu_in_reference_log_files]) and star_adu > 0 :
                normfactor = sum(star_adu_in_reference_log_files) / (4 * star_adu)
            else:
                normfactor = 0    
            norm_factor_for_stars.append(normfactor)
        good_scale_factors = [x for x in norm_factor_for_stars if 0 < x <= 5]
        norm_factor_for_logfile = np.median(good_scale_factors)
        all_norm_factors.append(norm_factor_for_logfile)
        all_log_files[file_index] = norm_factor_for_logfile * all_log_files[file_index]

    # Save normfactors
    normfactors_file_name = NormfactorFile.generate_file_name(night_date, img_duration)
    normfactor_file = NormfactorFile(output_folder / normfactors_file_name)
    normfactor_file.create_file(all_norm_factors)

    # Save the normalized data for each star
    noOfStars = len(all_log_files[0])
    for star_index in range(noOfStars):
        star_no = star_index + 1
        star_data = [
            all_log_files[file_index][star_index] for file_index in range(no_of_files)
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