import matplotlib

# Use non interactive backend
matplotlib.use("agg")

import itertools  # noqa
import sys
from pathlib import Path
from typing import Callable, Dict, Iterable

import numpy as np
from matplotlib import pyplot as plt

from m23.constants import CHARTS_FOLDER_NAME
from m23.file.log_file_combined_file import LogFileCombinedFile
from m23.file.normfactor_file import NormfactorFile
from m23.utils import get_date_from_input_night_folder_name, get_radius_folder_name


def draw_normfactors_chart(
    log_files_used: Iterable[LogFileCombinedFile],
    flux_log_combined_folder: Path,
    radii_of_extraction: Iterable[int],
) -> None:
    """
    Draws normfactors vs image number chart for for a provided `night_folder`
    Note that you must also provided `log_files_used` because otherwise there is no way to know
    which logfile corresponds to which norm factor

    param: log_files_used: The list or sequence of log files to used when doing
            intra night normalization
    param: night_folder: The night folder that hosts other folders like Flux Logs Combined, etc.
    return: None

    Side effects:
    Creates a charts folder in night_folder and saves the normfactors charts there
    """
    # Sort log files
    night_folder = flux_log_combined_folder.parent
    log_files_used.sort(key=lambda logfile: logfile.img_number())
    night_date = get_date_from_input_night_folder_name(night_folder.name)
    chart_folder = night_folder / CHARTS_FOLDER_NAME
    chart_folder.mkdir(parents=True, exist_ok=True)  # Create folder if it doesn't exist
    valid_folder_names = list(map(get_radius_folder_name, radii_of_extraction))

    for radius_folder in flux_log_combined_folder.glob("*Radius*"):
        if radius_folder.name not in valid_folder_names:
            continue
        normfactor_files = list(radius_folder.glob("*normfactor*"))
        if len(normfactor_files) != 1:
            sys.stderr.write(
                f"Expected to find 1 normfactor file, found {len(normfactor_files)} in {radius_folder}\n"  # noqa
            )
            # Skip this radius folder
            continue
        normfactor_file = NormfactorFile(normfactor_files[0].absolute())
        normfactor_data = normfactor_file.data()
        log_file_number_to_normfactor_map = {}
        if len(log_files_used) != len(normfactor_data):
            sys.stderr.write(
                "Make sure you're providing exactly the same number of logfiles as there are normfactor values\n"  # noqa
            )
            raise ValueError(
                f"""Mismatch between number of logfiles and the normfactors.
                Found logfiles: {len(log_files_used)}
                Found normfactors: {len(normfactor_data)}
                """
            )
        for index, log_file in enumerate(log_files_used):
            log_file_number_to_normfactor_map[log_file.img_number()] = normfactor_data[index]

        first_img_number = log_files_used[0].img_number()
        last_img_number = log_files_used[-1].img_number()
        chart_name = f"{night_date} normfactors_chart_{first_img_number}-{last_img_number}_{radius_folder.name}.png"  # noqa
        chart_file_path = chart_folder / chart_name
        x, y = zip(
            *log_file_number_to_normfactor_map.items()
        )  # Unpack a list of pairs into two tuples
        plt.figure(dpi=300)
        plt.plot(x, y, "b+")
        plt.xlabel("Log file number")
        plt.ylabel("Normfactor")
        plt.grid()
        plt.title(f"{night_date}")
        plt.savefig(chart_file_path)
        plt.close()  # Important to close the figure


def draw_internight_color_chart(
    night: Path,
    radius: int,
    section_x_values: Dict[int, Iterable],
    section_y_values: Dict[int, Iterable],
    section_color_fit_fn: Dict[int, Callable[[float], float]],
) -> Dict[int, float]:
    """
    Creates and saves color chart for a given night for a particular radius data
    Returns the median value of each section of the chart
    """
    chart_folder = night / CHARTS_FOLDER_NAME
    night_date = get_date_from_input_night_folder_name(night.name)
    chart_name = f"{night_date} Color Curve Fit Radius {radius}_px.png"
    chart_save_path = chart_folder / chart_name
    sections = sorted(section_x_values.keys())
    all_x_values = list(
        itertools.chain.from_iterable([section_x_values[section] for section in sections])
    )
    all_y_values = list(
        itertools.chain.from_iterable([section_y_values[section] for section in sections])
    )
    plt.figure(dpi=300, figsize=(10, 6))
    plt.rcParams["axes.facecolor"] = "black"
    plt.plot(all_x_values, all_y_values, "wo", ms=0.5)
    # Plot the curves for each of the three sections
    section_line_colors = ["blue", "green", "red"]
    median_of_sections = {}
    for index, section in enumerate(sections):
        x = section_x_values[section]
        x_min = np.min(x)
        x_max = np.max(x)
        x_new = np.linspace(x_min, x_max, 300)
        y_new = [section_color_fit_fn[section](i) for i in x_new]
        # Add the median value for each section to the dictionary
        median_of_sections[index] = np.median(y_new)
        plt.plot(x_new, y_new, color=section_line_colors[index], linewidth=2)
    ax = plt.gca()
    ax.set_xlim([0, np.max(all_x_values) + 3 * np.std(all_x_values)])
    ax.set_ylim([0, np.max(all_y_values) + 3 * np.std(all_y_values)])
    plt.title(f"{night_date}")
    plt.xlabel("Color")
    plt.ylabel("Flux Ratio")
    plt.savefig(chart_save_path)
    plt.close()  # Important to close the figure
    return median_of_sections


def draw_internight_brightness_chart(
    night: Path,
    radius: int,
    section_x_values: Dict[int, Iterable],
    section_y_values: Dict[int, Iterable],
    section_fit_fn: Dict[int, Callable[[float], float]],
) -> Dict[int, float]:
    """
    Creates and saves brightness chart for a given night for a particular radius data
    Returns the median value of each section of the chart
    """
    chart_folder = night / CHARTS_FOLDER_NAME
    night_date = get_date_from_input_night_folder_name(night.name)
    chart_name = f"{night_date} Brightness Curve Fit Radius {radius}_px.png"
    chart_save_path = chart_folder / chart_name
    sections = sorted(section_x_values.keys())
    all_x_values = list(
        itertools.chain.from_iterable([section_x_values[section] for section in sections])
    )
    all_y_values = list(
        itertools.chain.from_iterable([section_y_values[section] for section in sections])
    )
    plt.figure(dpi=300, figsize=(10, 6))
    plt.rcParams["axes.facecolor"] = "black"
    plt.plot(all_x_values, all_y_values, "wo", ms=0.5)
    # Plot the curves for each of the three sections
    section_line_colors = ["blue", "green", "red"]
    median_of_sections = {}
    for index, section in enumerate(sections):
        x = section_x_values[section]
        x_min = np.min(x)
        x_max = np.max(x)
        x_new = np.linspace(x_min, x_max, 300)
        y_new = [section_fit_fn[section](i) for i in x_new]
        median_of_sections[index] = np.median(y_new)
        plt.plot(x_new, y_new, color=section_line_colors[index], linewidth=2)

    plt.title(f"{night_date}")
    plt.xlabel("Magnitudes")
    plt.ylabel("Flux Ratio")
    plt.savefig(chart_save_path)
    plt.close()  # Important to close the figure
    return median_of_sections
