import re
from collections import namedtuple
from datetime import date, datetime
from pathlib import Path
from typing import Dict

import numpy as np

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

    # Class attributes
    header_rows = 6  # Specifies the first x rows that don't contain header information
    file_name_re = re.compile("(\d{4}-\d{2}-\d{2})_Normalized_(.*)\.txt")

    @classmethod
    def get_file_name(cls, night_date: date, radius_of_extraction: int) -> str:
        return f"{night_date.strftime('%Y-%m-%d')}_Normalized_{get_radius_folder_name(radius_of_extraction)}.txt"  # noqa

    def __init__(self, file_path: Path) -> None:
        self.__path = file_path
        self.__read_data = False

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
                f"{headers[0]:<8s}{headers[1]:>32s}{headers[2]:>24s}{headers[3]:>32s}{headers[4]:>32s}\n"  # noqa
            )
            for star_no in sorted(data_dict.keys()):
                star_data = data_dict[star_no]
                fd.write(
                    f"{star_no:<8d}{star_data.normalized_median_flux:>32.7f}{star_data.norm_factor:>24.7f}{star_data.measured_mean_r_i:>32.7f}{star_data.used_mean_r_i:>32.7f}\n"  # noqa
                )

    def _read(self):
        self.__read_data = True
        with self.path().open() as fd:
            lines = [line.strip() for line in fd.readlines()]
            lines = lines[3:]  # Skip the header rows
            self.__data = {}
            for line in lines:
                star_data = line.split()
                star_no = int(star_data[0])
                normalized_median_flux = float(star_data[1])
                normfactor = float(star_data[2])
                measured_mean_ri = float(star_data[3])
                used_mean_ri = float(star_data[4])
                self.__data[star_no] = self.StarData(
                    normalized_median_flux=normalized_median_flux,
                    norm_factor=normfactor,
                    measured_mean_r_i=measured_mean_ri,
                    used_mean_r_i=used_mean_ri,
                    attendance=np.nan,
                    reference_log_adu=np.nan,
                    median_flux=np.nan,
                )
        self.__read_data = True  # Marks file as read

    def is_valid_file_name(self):
        return bool(self.file_name_re.match(self.path().name))

    def path(self):
        return self.__path

    def night_date(self) -> date | None:
        """
        Returns the night date that can be inferred from the file name
        """
        if self.is_valid_file_name():
            # The first capture group contains the night date
            return datetime.strptime(
                self.file_name_re.match(self.path().name)[1],
                "%Y-%m-%d",
            ).date()

    def data(self):
        if not self.__read_data:
            self._read()
        return self.__data
