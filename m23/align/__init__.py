from pathlib import Path
from typing import Tuple

import astroalign as ast
import numpy as np
import numpy.typing as npt
from astropy.io.fits import getdata as getfitsdata


def image_alignment(image_data_to_align: npt.NDArray, ref_image_name : str | Path) -> Tuple[npt.NDArray]:
    """
    Aligns the image data provided in `image_data_to_align` with respect to a reference image

    param: image_data_to_align: Numpy two dimensional array represents fits image
    param: ref_image_name: Pathlike object for filepath string to which the source data is to be aligned

    return: The tuple of aligned image data and the footprint containing information about alignment  
    """

    ref_image_data = getfitsdata(ref_image_name)

    # Note it's important to use dtype of float
    target_fixed = np.array(ref_image_data, dtype="float")
    source_fixed = np.array(image_data_to_align, dtype="float")

    aligned_image_data, footprint = ast.register(source_fixed, target_fixed, fill_value=0)

    return aligned_image_data, footprint
