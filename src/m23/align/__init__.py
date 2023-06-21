from pathlib import Path
from typing import Tuple

import astroalign as ast
import numpy as np
import numpy.typing as npt
from astropy.io.fits import getdata as getfitsdata

from m23.exceptions import CouldNotAlignException

ScaleType = float
RotationType = float
TranslationXType = float
TranslationYType = float
AlignmentTransformationType = Tuple[RotationType, TranslationXType, TranslationYType, ScaleType]


def image_alignment(
    image_data_to_align: npt.NDArray, ref_image_name: str | Path
) -> Tuple[npt.NDArray, AlignmentTransformationType]:
    """
    Aligns the image data provided in `image_data_to_align` with respect to a reference image

    param: image_data_to_align: Numpy two dimensional array represents fits image
    param: ref_image_name: Pathlike object for filepath string to which the source data is
            to be aligned

    return:
        - Aligned image data
        - Transformation object which is a tuple of information about the alignment

    raises:
        ValueError: If it cannot find more than 3 stars on any input.
    """

    ref_image_data = getfitsdata(ref_image_name)

    # Note it's important to use dtype of float
    target_fixed = np.array(ref_image_data, dtype="float")
    source_fixed = np.array(image_data_to_align, dtype="float")

    try:
        t, __ = ast.find_transform(
            source=source_fixed,
            target=target_fixed,
            max_control_points=50,
            # Detection signal states how much sigma higher must the signal be w. bg
            detection_sigma=5,
            min_area=5,
        )
    except ast.MaxIterError:
        raise CouldNotAlignException
    except ValueError:
        raise CouldNotAlignException

    aligned_image_data, _ = ast.apply_transform(
        t,
        source_fixed,
        target_fixed,
        fill_value=0,
    )
    translation_x, translation_y = t.translation
    transformation_metrics: AlignmentTransformationType = (
        t.rotation,
        translation_x,
        translation_y,
        t.scale,
    )
    return aligned_image_data, transformation_metrics
