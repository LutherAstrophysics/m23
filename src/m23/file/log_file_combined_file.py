import re
from collections import namedtuple
from datetime import date, datetime
from pathlib import Path
from typing import Dict, Iterable, Tuple

import numpy as np
import numpy.typing as npt

from m23.constants import OBSERVATION_DATETIME_FORMAT
from m23.file.aligned_combined_file import AlignedCombinedFile
from m23.sky import angle_of_elevation


# Note that LogFileCombined is the one that that has the data for aligned combined
# images after extracting stars from the image. This is not to be confused with FluxLogCombined
# that is created after intra-night normalization (note *not* internight normalization)
class LogFileCombinedFile:
    # Class attributes
    header_rows = 9
    data_titles_row_zero_index = 8
    date_format = "%m-%d-%y"
    sky_adu_column = 5
    x_column = 0
    y_column = 1
    file_name_re = re.compile(r"(\d{2}-\d{2}-\d{2})_m23_(\d+\.\d*)-(\d{3})\.txt")
    star_adu_radius_re = re.compile(r"Star ADU (\d+)")

    StarLogfileCombinedData = namedtuple(
        "StarLogfileCombinedData",
        ["x", "y", "xFWHM", "yFWHM", "avgFWHM", "sky_adu", "radii_adu"],
    )
    LogFileCombinedDataType = Dict[int, StarLogfileCombinedData]

    date_observed_datetime_format = OBSERVATION_DATETIME_FORMAT

    @classmethod
    def generate_file_name(cls, night_date: date, img_no: int, img_duration: float):
        """
        Returns the file name to use for a given star night for the given night date
        param : night_date: Date for the night
        param: img_no : Image number corresponding to the Aligned combined image
        param: img_duration : the duration of images taken on the night
        """
        return f"{night_date.strftime(cls.date_format)}_m23_{img_duration}-{img_no:03}.txt"

    def __init__(self, file_path: str) -> None:
        self.__path = Path(file_path)
        self.__is_read = False
        self.__header = None
        self.__data = None
        self.__title_row = None
        self.__cluster_angle = None

    def _read(self):
        with self.__path.open() as fd:
            lines = [line.strip() for line in fd.readlines()]
            # Save the title row
            # We split the title row by gap of more than two spaces
            self.__title_row = re.split(r"\s{2,}", lines[self.data_titles_row_zero_index])
            # Try splitting on tab if not split on spaces
            if len(self.__title_row) == 1:
                self.__title_row = re.split(r"\t", lines[self.data_titles_row_zero_index])
            self.__header = lines[: self.header_rows]
            lines = lines[self.header_rows :]  # Skip headers - 1
            # Create a 2d list
            lines = [line.split() for line in lines]
            # Convert to 2d numpy array
            self.__data = np.array(lines, dtype="float")
        self.__is_read = True

    def _title_row(self):
        if not self.__is_read:
            self._read()
        return self.__title_row

    def _adu_radius_header_name(self, radius: int):
        return f"Star ADU {radius}"

    def _get_column_number_for_adu_radius(self, radius: int):
        titles = self._title_row()
        return titles.index(self._adu_radius_header_name(radius))

    def get_cluster_angle_with_uncertainty(self) -> Tuple[float, float]:
        """
        Return the cluster angle along with uncertainty of measurement of the
        time the image was taken
        """
        if not self.__cluster_angle:
            self.__cluster_angle = angle_of_elevation(
                datetime.strptime(self.datetime(), OBSERVATION_DATETIME_FORMAT)
            )
        # Note that cluster angle contains the angle as well as uncertainty
        return self.__cluster_angle

    def get_cluster_angle(self) -> float:
        """Return the cluster angle of the time the image was taken"""
        return self.get_cluster_angle_with_uncertainty()[0]

    def is_valid_file_name(self) -> bool:
        """
        Checks if the filename matches the naming convention
        """
        return bool(self.file_name_re.match(self.path().name))

    def header(self) -> Iterable[str]:
        """
        Returns an iterable to string representing the header information in the
        file
        """
        if not self.__is_read:
            self._read()
        return self.__header

    def datetime(self) -> str:
        """
        Return the datetime string representing the observation of this image
        or empty string if no data is present
        """
        return self.header()[0].split("\t")[-1]

    def night_date(self) -> date | None:
        """
        Returns the night date that can be inferred from the file name
        """
        if self.is_valid_file_name():
            # The first capture group contains the night date
            return datetime.strptime(
                self.file_name_re.match(self.path().name)[1],
                self.date_format,
            ).date()

    def get_adu(self, radius: int):
        """
        Returns an ordered array of ADU for stars for given `radius`.
        The first row of the array is the adu of star 1, 200th row for star 200,
        and the like
        """
        radius_col = self._get_column_number_for_adu_radius(radius)
        return self.data()[:, radius_col]

    def get_sky_adu_column(self):
        """
        Returns an ordered array of stars sky adu.
        The first row of the array is the sky adu of star 1, 200th row for star 200,
        and the like
        """
        return self.data()[:, self.sky_adu_column]

    def get_x_position_column(self):
        """
        Returns an ordered array of stars x positions.
        The first row of the array is the x position of star 1, 200th row for star 200,
        and the like
        """
        return self.data()[:, self.x_column]

    def get_y_position_column(self) -> npt.NDArray:
        """
        Returns an ordered array of stars y positions.
        The first row of the array is the y position of star 1, 200th row for star 200,
        and the like
        """
        return self.data()[:, self.y_column]

    def get_star_data(self, star_no: int) -> StarLogfileCombinedData:
        """
        Returns the details related to a particular `star_no`
        Returns a named tuple `StarLogfileCombinedData`
        """
        star_data = self.data()[star_no - 1]
        titles = self._title_row()
        first_radii_adu_column = 6
        radii_adu = {}
        for index, col_name in enumerate(titles[first_radii_adu_column:]):
            radius = int(self.star_adu_radius_re.match(col_name)[1])
            radii_adu[radius] = star_data[first_radii_adu_column + index]
        return self.StarLogfileCombinedData(*star_data[:first_radii_adu_column], radii_adu)

    def img_duration(self) -> float | None:
        """
        Returns the image duration that can be inferred from the file name
        """
        if self.is_valid_file_name():
            # The second capture group contains the image duration
            return float(self.file_name_re.match(self.path().name)[2])

    def img_number(self) -> int | None:
        """
        Returns the image number associated to the filename if the file name is valid
        """
        if self.is_valid_file_name():
            # The third capture group contains the image number
            return int(self.file_name_re.match(self.path().name)[3])

    def is_file_format_valid(self):
        """
        Checks if the file format is valid
        """
        return True

    def path(self):
        return self.__path

    def data(self):
        if not self.__is_read:
            self._read()
        # Return the copy of the data so that the a caller
        # doesn't get affected by another misbehaving caller.
        return np.copy(self.__data)

    def create_file(
        self,
        data: LogFileCombinedDataType,
        aligned_combined_file: AlignedCombinedFile,
        datetime_of_img: str = "",
    ):
        """
        Creates logfile combined file based on the provided data

        param: data : Data that's to be written
        param: aligned_combined_file: AlignedCombinedFile on which this file is based
        """
        if not self.is_valid_file_name():
            raise ValueError(f"Invalid file name {self.path()}")

        if len(data) == 0:
            radii = []
        else:
            radii = data[list(data.keys())[0]].radii_adu.keys()

        stars = sorted(data.keys())
        no_of_stars = len(stars)
        with self.path().open("w") as fd:
            # First line represents the datetime
            fd.write(f"ObservedAt:\t{datetime_of_img}\n")
            fd.write("Star Data Extractor Tool: (Note: This program mocks format of AIP_4_WIN) \n")
            fd.write(f"\tImage {aligned_combined_file.path().name}\n")
            fd.write(f"\tTotal no of stars: {no_of_stars}\n")
            fd.write(f"\tRadius of star diaphragm: {', '.join(map(str, radii))}\n")
            fd.write("\tSky annulus inner radius: \n")
            fd.write("\tSky annulus outer radius: \n")
            fd.write("\tThreshold factor: \n")

            headers = [
                "X",
                "Y",
                "XFWHM",
                "YFWHM",
                "Avg FWHM",
                "Sky ADU",
            ] + [self._adu_radius_header_name(radius) for radius in radii]
            for header in headers:
                fd.write(f"{header:>16s}")
            fd.write("\n")

            for star in stars:  # Sorted in ascending order by star number
                star_data = data[star]
                fd.write(
                    f"{star_data.x:>16.2f}{star_data.y:>16.2f}{star_data.xFWHM:>16.4f}{star_data.yFWHM:>16.4f}{star_data.avgFWHM:>16.4f}{star_data.sky_adu:>16.2f}"  # noqa
                )
                for radius in radii:
                    fd.write(f"{star_data.radii_adu[radius]:16.2f}")
                fd.write("\n")

    def __len__(self):
        """Returns the number of stars present in the dataset"""
        return len(self.data())

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f"Log file combined: {self.__path}"
