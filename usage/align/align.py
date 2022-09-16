import astroalign as aa
import matplotlib.pyplot as plt
import numpy as np
from astropy.io import fits
from scipy.ndimage import rotate


def getImgName(index):
    return f"m23_7.0-{index}.fit"


def returnFitData(fileName):
    with fits.open(fileName) as fd:
        return fd[0].data


###
# target is the reference image
# source is the image that will be transformed

# target = returnFitData(getImgName("0504"))
# source = returnFitData(getImgName("0667"))

source = returnFitData(getImgName("0504"))
target = returnFitData("m23_3.5_071.fit")

registered, footprint = aa.register(source, target, fill_value=50000)

fig, axes = plt.subplots(2, 2, figsize=(10, 10))
axes[0, 0].imshow(
    source, cmap="gray", interpolation="none", origin="lower", vmin=1500, vmax=4000
)
axes[0, 0].axis("off")
axes[0, 0].set_title("Source Image")

axes[0, 1].imshow(
    target, cmap="gray", interpolation="none", origin="lower", vmin=1500, vmax=4000
)
axes[0, 1].axis("off")
axes[0, 1].set_title("Target Image")

axes[1, 1].imshow(
    registered, cmap="gray", interpolation="none", origin="lower", vmin=1500, vmax=4000
)

axes[1, 1].axis("off")
axes[1, 1].set_title("Source Image aligned with Target")

axes[1, 0].axis("off")

plt.tight_layout()
plt.show()
