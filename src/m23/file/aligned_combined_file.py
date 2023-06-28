import datetime
import re
from pathlib import Path

import numpy.typing as npt
from astropy.io import fits
from astropy.io.fits.header import Header

from m23.constants import OBSERVATION_DATETIME_FORMAT
from m23.file.raw_image_file import RawImageFile


class AlignedCombinedFile:
    # Class attributes
    file_name_re = re.compile(r"m23_(\d+\.?\d*)[-_](\d+).fit")
    date_observed_header_name = "DATE-OBS"
    time_observed_header_name = "TIME-OBS"
    date_observed_datetime_format = OBSERVATION_DATETIME_FORMAT

    @classmethod
    def generate_file_name(cls, img_duration: float, img_number: int) -> str:
        """
        Generates filename based on the given `img_duration` and `img_number`
        """
        return f"m23_{img_duration}-{img_number:04}.fit"

    def __init__(self, file_path) -> None:
        self.__path = Path(file_path)
        self.__is_read = False
        self.__data = None
        self.__header = None

    def _read(self):
        if not self.exists():
            raise FileNotFoundError(f"File not found {self.path()}")
        if not self.path().is_file() and self.__path.suffix != ".fit":
            raise ValueError(f"Invalid fit file {self.path()}")
        with fits.open(self.path()) as fd:
            self.__header = fd[0].header
            self.__data = fd[0].data
        self.__is_read = True

    def exists(self):
        return self.path().exists()

    def datetime(self) -> None | datetime.datetime:
        """
        Returns the datetime object of the time observed. Parses the datetime
        field from the header of the image
        """
        timestr = self.header().get(self.time_observed_header_name)
        datestr = self.header().get(self.date_observed_header_name)
        if timestr:
            # If time header is present, construct the datetime from date and time header
            return datetime.datetime.strptime(
                f"{datestr}T{timestr}", self.date_observed_datetime_format
            )
        else:
            # If time no time header is present, we assume that both date and
            # time are present in the date header in format given by
            # `self.date_observed_datetime_format`
            # Remove the millisecond part if present
            datestr = datestr.split(".")[0]
            return datetime.datetime.strptime(f"{datestr}", self.date_observed_datetime_format)

    def is_valid_file_name(self):
        """
        Checks if the file name is valid as per the file naming conventions
        of m23 data processing library.
        """
        return bool(self.file_name_re.match(self.path().name))

    def image_duration(self):
        """
        Returns the image duration if the filename is valid
        """
        if not self.is_valid_file_name():
            raise ValueError(f"{self.path().name} doesn't match naming conventions")
        return float(self.file_name_re.match(self.path().name)[1])

    def image_number(self):
        """
        Returns the image number if the filename is valid
        """
        if not self.is_valid_file_name():
            raise ValueError(f"{self.path().name} doesn't match naming conventions")
        return int(self.file_name_re.match(self.path().name)[2])

    def data(self) -> npt.NDArray:
        if not self.__is_read:
            self._read()
        return self.__data

    def header(self) -> Header:
        if not self.__is_read:
            self._read()
        return self.__header

    def path(self):
        return self.__path

    def create_file(self, data: npt.NDArray, copy_header_from: RawImageFile) -> None:
        """
        Create a fit file based on provided np array `data`.
        It copies the header information from the `RawImageFile`
        """
        fits.writeto(self.path(), data, header=copy_header_from.header())

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f"Aligned combined file: {self.path()}"
