import re
from datetime import date, datetime
from pathlib import Path
from typing import Tuple

import numpy as np
import numpy.typing as npt

from m23.constants import FLUX_LOG_COMBINED_FILENAME_DATE_FORMAT
from m23.file import is_string_float
from m23.file.normfactor_file import NormfactorFile
from m23.file.reference_log_file import ReferenceLogFile
from m23.utils import customMedian


# Note that FluxLogCombined is the one that we have for multiple
# radius of extraction. This is generated after intra-night (*not* inter-night)
# normalization. Don't confuse this file with LogFileCombined that
# is generated after extraction step.
class FluxLogCombinedFile:
    """
    This class is instantiated with the string representing
    file path for the Flux Log Combined file that you want to analyze

    This object could be useful for analyzing values like the attendance of a
    star on a particular night, it's mean and median values on the night, etc.
    """

    # Class attributes
    header_rows = 6  # Specifies the first x rows that don't contain header information
    file_name_re = re.compile('(\d{2}-\d{2}-\d{2})_m23_(\d+\.\d*)-(\d{1,4})_flux\.txt')
    file_name_re = re.compile('(\d{2}-\d{2}-\d{2})_m23_(\d+\.\d*)-(\d{1,4})_flux\.txt')

    def __init__(self, path: str | Path) -> None:
        if type(path) == str:
            path = Path(path)
        self.__path = path
        self.__data = None
        self.__valid_data = None
        self.__read_data = False
        self.__attendance = None

    @classmethod
    def generate_file_name(cls, night_date: date, star_no: int, img_duration: float):
        """
        Returns the file name to use for a given star night for the given night date
        param : night_date: Date for the night
        param: star_no : Star number
        param: img_duration : the duration of images taken on the night
        """
        return f"{night_date.strftime(FLUX_LOG_COMBINED_FILENAME_DATE_FORMAT)}_m23_{img_duration}-{star_no:04}_flux.txt"

    def _validate_file(self):
        if not self.path().exists():
            raise FileNotFoundError(f"File not found {self.path()}")
        if not self.path().is_file():
            raise ValueError("Directory provided, expected file f{self.path()}")

    def _calculate_attendance(self) -> float:
        """
        Calculates and returns the attendance for the night based on `self.data`
        Note that attendance is a value between 0-1.

        Preconditions:
            The object should have valid `self.data`
        Assumptions:
            `self.data` contains all data point albeit empty for a start for the night
        """
        data_points = len(self.data())
        positive_value_data_points = len(self.valid_data())
        return positive_value_data_points / data_points

    # Accessors

    def read_file_data(self):
        """
        Reads the file and sets the the data attribute and attendance attribute in the object
        """
        self._validate_file()
        with self.path().open() as fd:
            lines = [line.strip() for line in fd.readlines()]
            lines = lines[self.header_rows :]  # Skip the header rows
            self.__data = np.array(lines, dtype="float")  # Save data as numpy array
            self.__valid_data = np.array(
                [float(x) for x in self.__data if is_string_float(x) and float(x) > 0],
                dtype="float",
            )
        self.__read_data = True  # Marks file as read
        self.__attendance = self._calculate_attendance()

    def is_valid_file_name(self) -> bool:
        """
        Checks if the file name is valid as per the file naming conventions
        of m23 data processing library.
        """
        return bool(self.file_name_re.match(self.path().name))

    def night_date(self) -> date | None:
        """
        Returns the night date that can be inferred from the file name
        """
        if self.is_valid_file_name():
            # The first capture group contains the night date
            return datetime.strptime(
                self.file_name_re.match(self.path().name)[2],
                FLUX_LOG_COMBINED_FILENAME_DATE_FORMAT,
            ).date()

    def img_duration(self) -> float | None:
        """
        Returns the image duration that can be inferred from the file name
        """
        if self.is_valid_file_name():
            # The second capture group contains the image duration
            return float(self.file_name_re.match(self.path().name)[2])

    def star_number(self) -> int | None:
        """
        Returns the star number associated to the filename if the file name is valid
        """
        if self.is_valid_file_name():
            # The third capture group contains the star number
            return int(self.file_name_re.match(self.path().name)[3])

    def is_file_format_valid(self):
        """
        Checks if the file format is valid
        """
        return True

    def path(self) -> Path:
        return self.__path

    def data(self) -> None | npt.ArrayLike:
        """
        The data property returns either None or a numpy one dimensional array
        """
        if not self.__read_data:
            self.read_file_data()
        return self.__data

    def valid_data(self) -> None | npt.ArrayLike:
        """
        Returns a sample of data for the star for the nights with only valid data points > 0 magnitudes
        """
        if not self.__read_data:
            self.read_file_data()
        return self.__valid_data

    def attendance(self) -> float:
        """
        Returns the attendance % (between 0-1) for star corresponding to the flux log combined file for the night
        """
        self._validate_file()
        if not self.__read_data:
            self.read_file_data()
        return self.__attendance

    def median(self) -> float:
        """
        Returns the median value for the star for the night
        Note that this is the median of only valid data points (> 0 magnitudes)
        This means that 0.00 values are automatically ignored.
        Note that if the night doesn't contain any valid data, this returns nan
        """
        self._validate_file()
        if not self.__read_data:
            self.read_file_data()
        return np.median(
            self.valid_data()
        )  # Note to use only the valid data points to calculate median

    def specialized_median_for_internight_normalization(self) -> float:
        """
        Returns specialized median flux for the night to be used by internight normalization code.
        This is special in that the median is only calculated from images that got applied
        internight normalization factor within a certain range. Additionally (as always) we ignore
        data points that are zero values when calculating median
        This is just an implementation of the way things are/were done in the IDL code.
        """
        min_tolerable_intranight_normfactor = 0.85
        max_tolerable_intranight_normfactor = 1.15

        # Get the *intra* night norm factors file from the same directory as this file is in
        parent_dir = self.path().parent
        normfactor_files = list(parent_dir.glob("*normfactor*"))
        if len(normfactor_files) == 0:
            raise ValueError("Normfactor file not found in {parent_dir}")
        if len(normfactor_files) > 1:
            raise ValueError("Multiple Normfactor files found in {parent_dir}")
        normfactor_file = NormfactorFile(normfactor_files[0].absolute())

        data_to_use = []
        for index, data in enumerate(self.data()):
            # Add the value only if it's > 0 and the normfactor for the image is within specified range
            if (
                data > 0
                and min_tolerable_intranight_normfactor
                <= normfactor_file.data()[index]
                <= max_tolerable_intranight_normfactor
            ):
                data_to_use.append(data)
        
        # IDL style Median
        if len(data_to_use) == 0:
            return np.nan
        mid_value = len(data_to_use) // 2
        return sorted(data_to_use)[mid_value]

    def mean(self) -> float:
        """
        Returns the mean value for the star for the night
        Note that this is the median of only valid data points (> 0 magnitudes)
        This means that 0.00 values are automatically ignored.
        Note that if the night doesn't contain any valid data, this returns nan
        """
        self._validate_file()
        if not self.__read_data:
            self.read_file_data()
        return np.mean(
            self.valid_data()
        )  # Note to use only the valid data points to calculate mean

    def create_file(
        self,
        data: npt.NDArray,
        start_img: int,
        end_img: int,
        location: Tuple[float],
        reference_logfile: ReferenceLogFile,
    ):
        """
        Creates/Updates Flux Log Combined file

        param: data: The flux values for the star
        param: start_image: The first aligned combined image number used
        param: end_image: The last aligned combined image number used
        param: location: The x and y coordinates of the star in the image aligned combined image
        param: reference_logfile: The reference logfile used
        """
        if not self.is_valid_file_name():
            raise ValueError(f"File name is invalid {self.path()}")
        x, y = location
        with self.path().open("w") as fd:
            fd.write(f"Program:\n")
            fd.write(f"Started with image\t{start_img}\n")
            fd.write(f"Ended with image\t{end_img}\n")
            fd.write(f"Reference log file used: {reference_logfile}\n")
            fd.write(f"X location:\t{x:.3f}\n")
            fd.write(f"Y location:\t{y:.3f}\n")
            np.savetxt(
                fd,
                np.array(data),
                fmt="%10.2f",
            )

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f"FluxLogCombinedFile {self.path()}"
