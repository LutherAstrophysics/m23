import csv
import random

from m23.file.color_normalized_file import ColorNormalizedFile
from m23.processor.nights_csv_config_loader import (
    NightsCSVConfig,
    validate_nights_csv_config_file,
)


def create_nights_csv_auxiliary(config: NightsCSVConfig):
    """
    Creates and saves a csv of star fluxes for night specified in the
    contents of the `file_path`.
    """
    radius = config["radius"]
    fluxes_file_name = f"fluxes_{radius}px.txt"
    output_folder = config["output"]
    fluxes_file = output_folder / fluxes_file_name
    # We ensure that the filename doesn't already exist so that we don't override
    # existing file
    while fluxes_file.exists():
        fluxes_file = output_folder / f"flux_{radius}px_{random.randrange(1, 100)}.txt"
    color_normalized_files = [
        ColorNormalizedFile(file) for file in config["color_normalized_files"]
    ]
    color_normalized_files = sorted(color_normalized_files, key=lambda x: x.night_date())

    all_color_files_data = [
        color_normalized_files[i].data() for i in range(len(color_normalized_files))
    ]
    night_dates = [
        str(color_normalized_files[i].night_date()) for i in range(len(color_normalized_files))
    ]

    with open(fluxes_file, "w", newline="") as file:
        writer = csv.writer(file, delimiter=",")
        writer.writerow(["Star#"] + night_dates)
        for star_no in range(len(all_color_files_data[0])):  # Writes the data of 2510 stars
            star_data = [
                all_color_files_data[i][star_no + 1].normalized_median_flux
                for i in range(len(color_normalized_files))
            ]
            writer.writerow([str(star_no + 1)] + star_data)
        if (
            len(all_color_files_data[0]) == 2508
        ):  # If no data for stars 2509 and 2510, then write them as empty
            writer.writerow(["2509"] + ["0" for i in range(len(color_normalized_files))])
            writer.writerow(["2510"] + ["0" for i in range(len(color_normalized_files))])
    file.close()

    # Create a combined sky background file
    sky_bg_file = output_folder / "sky_bg.txt"
    while sky_bg_file.exists():
        sky_bg_file = output_folder / f"sky_bg_{random.randrange(1, 100)}.txt"

    sky_bg_files = config["sky_bg_files"]
    if len(sky_bg_files) == 0:
        raise Exception("No sky background files found.")

    with open(sky_bg_files[0], "r") as fd:
        sky_bg_header = fd.readline()
    sky_bg_header_cols = len(sky_bg_header.split())

    lines_to_write = [sky_bg_header]
    for f in sky_bg_files:
        with open(f, "r") as fd:
            lines = fd.readlines()[1:]
            if length := len(lines):
                line_to_write = lines[length // 2]
                if len(line_to_write.split()) != sky_bg_header_cols:
                    raise Exception(
                        f"file {f} and {sky_bg_files[0]} have different number of columns"
                    )
                lines_to_write.extend(lines[1:])

    with open(sky_bg_file, "w") as fd:
        fd.writelines(lines_to_write)


def create_nights_csv(file_path: str):
    """
    Creates and saves a csv of star fluxes for night specified in the
    contents of the `file_path`. This function calls
    `validate_nights_csv_config_file` to do most of its job
    """
    validate_nights_csv_config_file(file_path, create_nights_csv_auxiliary)
