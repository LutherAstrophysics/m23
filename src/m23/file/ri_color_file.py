from pathlib import Path

import numpy as np

from m23.file import is_string_float


class RIColorFile:
    header_rows = 1  # First x rows that contain header information

    def __init__(self, file_path: str) -> None:
        self.__path = Path(file_path)
        self.__data = None
        self.__is_read = False

    def _validate_file(self):
        if not self.path().exists():
            raise FileNotFoundError(f"{self.path()} not found")
        if not self.path().is_file() or self.path().suffix != ".txt":
            raise ValueError(f"{self.path()} is not a valid txt file")

    def _read(self):
        self._validate_file()
        with self.path().open() as fd:
            lines = [line.strip() for line in fd.readlines()]
            lines = lines[self.header_rows :]  # Skip the header rows
            self.__data = np.array([x for x in lines if is_string_float(x)], dtype="float")
            self.__is_read = True

    def data(self):
        if not self.__is_read:
            self._read()
        return self.__data

    def get_star_color(self, star_no: int):
        if not self.__is_read:
            self._read()
        return self.data()[star_no - 1]  # Subtract 1 because of zero indexing

    def path(self):
        return self.__path

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"R-I color file: {self.path()}"
