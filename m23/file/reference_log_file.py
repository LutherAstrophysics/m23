from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import numpy.typing as npt

from m23.file.index import line_str_contains_numbers_and_non_alphabets


class ReferenceLogFile:
    header_rows = 9  # The first x rows that don't contain data but metadata

    column_numbers: Dict[str, int] = {
        "x": 0,  # Beware of the zero indexing
        "y": 1,
        "sigma": 2,
        "fwhm": 3,
        "sky_adu": 4,
        "star_adu": 5,
    }

    def __init__(self, file_path: str) -> None:
        self.__path = Path(file_path)
        self.__is_read = False
        self.__data = None

    def _read(self):
        with self.__path.open() as fd:
            lines = [line.strip() for line in fd.readlines()]
            lines = lines[self.header_rows :]  # Skip headers
            lines = filter(line_str_contains_numbers_and_non_alphabets, lines)
            # Create a 2d list
            lines = [line.split() for line in lines]
            # Convert to 2d numpy array
            self.__data = np.array(lines, dtype="float")
        self.__is_read = True

    def _get_col_value(self, star_no: int, col: str) -> float:
        if not self.__is_read:
            self._read()
        column_number = self.column_numbers[col]
        # Return None if star_no is out of bound
        if star_no < 1 or star_no > len(self.__data):
            return None
        # Note that -1 is necessary bc of 0 indexing
        return self.__data[star_no - 1][column_number]

    def get_star_xy(self, star_no: int) -> Tuple[float]:
        """
        Returns the tuple of `star_no`'s x and y coordinate
        """
        return self._get_col_value(star_no, "x"), self._get_col_value(star_no, "y")

    def get_star_adu(self, star_no: int) -> float:
        """
        Returns the adu for a given star
        """
        return self._get_col_value(star_no, "star_adu")

    def get_star_sky_adu(self, star_no: int) -> float:
        """
        Returns the sky adu for a given star
        """
        return self._get_col_value(star_no, "sky_adu")

    def data(self) -> npt.NDArray:
        """
        Returns the stars data in the reference file as 2 dimensional numpy array
        """
        if not self.__is_read:
            self._read()
        return self.__data

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"Reference log file: {self.__path}"
