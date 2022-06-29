from astropy.io.fits import getdata
import matplotlib.pyplot as plt

fig, axes = plt.subplots(2, 2, figsize=(10, 10))
axes[0, 0].imshow(
    getdata("masterflat.fit"),
    cmap="gray",
    interpolation="none",
    origin="lower",
    vmin=1000,
    vmax=1800,
)
axes[0, 0].axis("off")
axes[0, 0].set_title("Masterflat")

axes[0, 1].imshow(
    getdata("masterdark.fit"),
    cmap="gray",
    interpolation="none",
    origin="lower",
    vmin=1000,
    vmax=1800,
)
axes[0, 1].axis("off")
axes[0, 1].set_title("Master dark")

axes[1, 1].imshow(
    getdata("m23_7.0-0607.fit"),
    cmap="gray",
    interpolation="none",
    origin="lower",
    vmin=1000,
    vmax=1800,
)
axes[1, 1].axis("off")
axes[1, 1].set_title("607 raw")

axes[1, 0].imshow(
    getdata("607calibrated.fit"),
    cmap="gray",
    interpolation="none",
    origin="lower",
    vmin=1000,
    vmax=1800,
)
axes[1, 0].axis("off")
axes[1, 0].set_title("607 calibrated")

plt.tight_layout()
plt.show()
