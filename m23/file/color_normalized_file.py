from collections import namedtuple
from datetime import date
from pathlib import Path
from typing import Dict

from m23.utils import get_radius_folder_name


class ColorNormalizedFile:
    StarData = namedtuple(
        "StarRow",
        [
            "median_flux",  # Median flux for the night
            "normalized_median_flux",  # Normalized flux for the night
            "norm_factor",  # Norm factor used
            "measured_mean_r_i",  # The R-I value defined in reference file
            "used_mean_r_i",  # R-I actually used to calculate norm factor
            "attendance",  # Attendance of that star for the night
            "reference_log_adu",  # Star ADU in the reference file
        ],
    )
    Data_Dict_Type = Dict[int, StarData]

    @classmethod
    def get_file_name(cls, night_date: date, radius_of_extraction: int) -> str:
        return f"{night_date.strftime('%Y-%m-%d')}_Normalized_{get_radius_folder_name(radius_of_extraction)}.txt"

    def __init__(self, file_path: Path) -> None:
        self.__path = file_path

    def save_data(self, data_dict: Data_Dict_Type, night_date: date):
        if self.__path.is_dir() or self.__path.suffix != ".txt":
            raise ValueError(f"Given path {self.__path} is not a valid txt file")

        # Create parent directories if needed
        parent_dir = self.__path.parent
        parent_dir.mkdir(parents=True, exist_ok=True)

        # Open file in writing mode
        with self.__path.open("w") as fd:
            fd.write(f"Color-normalized Data for {night_date.strftime('%Y-%m-%d')}\n")
            fd.write("\n")
            headers = [
                "Star #",
                "Normalized Median Flux",
                "Norm Factor",
                "Measured Mean R-I",
                "Used Mean R-I",
            ]
            fd.write(
                f"{headers[0]:>8s}{headers[1]:>32s}{headers[2]:>24s}{headers[3]:>32s}{headers[4]:>32s}\n"
            )
            for star_no in sorted(data_dict.keys()):
                star_data = data_dict[star_no]
                fd.write(
                    f"{star_no:>8d}{star_data.normalized_median_flux:>32.7f}{star_data.norm_factor:>24.7f}{star_data.measured_mean_r_i:>32.7f}{star_data.used_mean_r_i:>32.7f}\n"
                )
