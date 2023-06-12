import datetime
import re
from datetime import date
from pathlib import Path
from typing import Dict, Iterable, Tuple

import numpy as np

from m23.constants import OBSERVATION_DATETIME_FORMAT, SKY_BG_FILENAME_DATE_FORMAT
from m23.sky.moon import phase as get_moon_phase_name
from m23.sky.moon import position as get_moon_phase


class SkyBgFile:
    file_name_re = re.compile("(\d{2}-\d{2}-\d{2})_m23_(\d+\.\d*)_sky_bg\.txt")
    date_observed_datetime_format = OBSERVATION_DATETIME_FORMAT

    # We divide up the sky into several square sections (currently, sized 64px)
    # and calculate the mean background in that region.  Additionally,
    # background data is associated with date and time at which it is
    # calculated.
    DateTimeType = str
    BackgroundRegionType = Tuple[int, int]
    BGAduPerPixelType = float
    BackgroundDictType = Dict[BackgroundRegionType, BGAduPerPixelType]
    SkyBGDataType = Iterable[Tuple[DateTimeType, BackgroundDictType]]

    @classmethod
    def generate_file_name(cls, night_date: date, img_duration: float):
        """
        Returns the file name for the sky background for a night
        param : night_date: Date for the night
        param: img_duration : the duration of images taken on the night
        """
        return f"{night_date.strftime(SKY_BG_FILENAME_DATE_FORMAT)}_m23_{img_duration}sky_bg.txt"

    def __init__(self, path: str | Path) -> None:
        if type(path) == str:
            path = Path(path)
        self.__path = path
        self.__data = None

    def path(self):
        return self.__path

    def _validate_file(self):
        if not self.path().exists():
            raise FileNotFoundError(f"File not found {self.path()}")
        if not self.path().is_file():
            raise ValueError("Directory provided, expected file f{self.path()}")

    def create_file(
        self,
        sky_bg_data: SkyBGDataType,
        color_normfactors_title: Iterable[str],
        color_normfactors_values: Iterable[float],
        brightness_normfactors_title: Iterable[str],
        brightness_normfactors_values: Iterable[float],
    ):
        """
        Creates/Updates sky background file based on the `sky_bg_data`
        """
        if len(sky_bg_data) == 0:
            # Nothing to do
            with open(self.path(), "w") as fd:
                pass
            return

        color_normfactors_title_str = " ".join(map("{:<30s}".format, color_normfactors_title))
        brightness_normfactors_title_str = " ".join(
            map("{:<30s}".format, brightness_normfactors_title)
        )
        color_normfactors_values_str = " ".join(map("{:<30.5f}".format, color_normfactors_values))
        brightness_normfactors_values_str = " ".join(
            map("{:<30.5f}".format, brightness_normfactors_values)
        )

        bg_sections = map(lambda x: "_".join(map(str, x)), sky_bg_data[0][1].keys())
        bg_sections_str = "".join(map("{:<10s}".format, bg_sections))

        with open(self.path(), "w") as fd:
            fd.write(
                f"{'Date':<26s}"
                f"{'Moon_Phase':<16s}"
                f"{'Moon_Phase_Name':<20s}"
                f"{'Mean':<10s}{'Median':<10s}"
                f"{'Std':<10s}"
                f"{color_normfactors_title_str}"
                f"{brightness_normfactors_title_str}"
                f"{bg_sections_str}\n"
            )
            for night_datetime, bg_data in sky_bg_data:
                bg_data_np = np.array([bg_data[x] for x in bg_data.keys()])

                # We ignore the bogus values before taking the mean and the median
                bg_data_ignoring_bogus_values = bg_data_np[(bg_data_np > 0)]

                mean, median = np.mean(bg_data_ignoring_bogus_values), np.median(
                    bg_data_ignoring_bogus_values
                )
                std = np.std(bg_data_ignoring_bogus_values)
                date_time_of_observation = datetime.datetime.strptime(
                    night_datetime, self.date_observed_datetime_format
                )
                moon_phase = get_moon_phase(date_time_of_observation)
                moon_phase_name = get_moon_phase_name(date_time_of_observation)

                values_str = "".join(map("{:<10.2f}".format, bg_data_np))
                fd.write(
                    f"{night_datetime:<26s}"
                    f"{moon_phase:<16.5f}"
                    f"{moon_phase_name:<20s}"
                    f"{mean:<10.2f}{median:<10.2f}"
                    f"{std:<10.2f}"
                    f"{color_normfactors_values_str}"
                    f"{brightness_normfactors_values_str}"
                    f"{values_str}\n"
                )

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f"SkyBackgroundFile {self.path()}"