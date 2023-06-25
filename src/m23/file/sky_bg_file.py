import datetime
import re
from datetime import date
from pathlib import Path
from typing import Dict, Iterable, Tuple

import numpy as np

from m23.constants import OBSERVATION_DATETIME_FORMAT, SKY_BG_FILENAME_DATE_FORMAT
from m23.sky import angle_of_elevation
from m23.sky.moon import moon_distance
from m23.sky.moon import phase as get_moon_phase_name
from m23.sky.moon import position as get_moon_phase
from m23.utils import half_round_up_to_int


class SkyBgFile:
    file_name_re = re.compile(r"(\d{2}-\d{2}-\d{2})_m23_(\d+\.\d*)_sky_bg\.txt")
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
    def generate_file_name(cls, night_date: date):
        """
        Returns the file name for the sky background for a night
        param : night_date: Date for the night
        """
        return f"{night_date.strftime(SKY_BG_FILENAME_DATE_FORMAT)}_m23_sky_bg.txt"

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
        first_img_number: int,
        last_img_number: int,
        normalized_cluster_angle: int,
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
                f"{'Image_number':<15s}"
                f"{'First_img':<15s}"  # Img number of the first logfile combined used
                f"{'Last_img':<15s}"  # Img number of the last logfile combined used
                f"{'Moon_Phase':<16s}"
                f"{'Moon_Phase_Name':<20s}"
                f"{'Normalized_cluster_angle':<30s}"
                f"{'Cluster_Angle_Round':<20s}"
                f"{'Cluster_Angle':<20s}"
                f"{'Cluster_Angle_Uncertainty':<30s}"
                f"{'Moon_Distance':<20s}"
                f"{'Mean':<10s}{'Median':<10s}"
                f"{'Std':<10s}"
                f"{color_normfactors_title_str}"
                f"{brightness_normfactors_title_str}"
                f"{bg_sections_str}\n"
            )
            for night_datetime, bg_data, img_number in sky_bg_data:
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
                cluster_angle, cluster_angle_uncertainty = angle_of_elevation(
                    date_time_of_observation
                )  # noqa
                moon_dist_degrees = moon_distance(date_time_of_observation)
                fd.write(
                    f"{night_datetime:<26s}"
                    f"{img_number:<15d}"
                    f"{first_img_number:<15d}"
                    f"{last_img_number:<15d}"
                    f"{moon_phase:<16.5f}"
                    f"{moon_phase_name:<20s}"
                    f"{normalized_cluster_angle:<30d}"
                    f"{half_round_up_to_int(cluster_angle):<20.0f}"
                    f"{cluster_angle:<20.1f}"
                    f"{cluster_angle_uncertainty:<30.1f}"
                    f"{moon_dist_degrees:<20.2f}"
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
