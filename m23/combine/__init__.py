from typing import Iterable

import numpy as np
import numpy.typing as npt

from m23.trans import createFitFileWithSameHeader


def image_combination(
    images_data: Iterable[npt.NDArray], file_name, fit_file_name_to_copy_header_from
) -> npt.NDArray:
    """
    Combines the `images_data` that's provided and saves the combination in fit file
    that's given by `file_name` copying header information of the fit file from
    `fit_file_name_to_copy_header_from`
    """
    images_data = np.array(images_data)
    combinedImageData = np.sum(images_data, axis=0)

    createFitFileWithSameHeader(
        combinedImageData.astype("int"), file_name, fit_file_name_to_copy_header_from
    )
    return combinedImageData
