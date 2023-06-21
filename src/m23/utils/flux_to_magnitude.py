import math

import numpy as np


def flux_to_magnitude(flux: float, radius: int) -> float:
    if not flux > 0:
        return np.nan
    if radius == 5:
        return 23.99 - 2.5665 * math.log10(flux)
    elif radius == 4:
        return 24.176 - 2.6148 * math.log10(flux)
    elif radius == 3:
        return 23.971 - 2.5907 * math.log10(flux)
    else:
        raise ValueError(f"No formula to convert for radius {radius}")
