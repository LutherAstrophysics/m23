from datetime import date
from pathlib import Path

import numpy as np
import numpy.typing as npt


class NormfactorFile:
    # Class attributes
    date_format = "%m-%d-%y"

    @classmethod
    def generate_file_name(cls, night_date: date, img_duration: float):
        return f"{night_date.strftime(cls.date_format)}_m23_{img_duration}_normfactors.txt"

    def __init__(self, file_path: str) -> None:
        self.__path = Path(file_path)
        self.__data = None
        self.__is_read = False

    def _read(self):
        self.is_valid_file_name()
        if not self.exists():
            raise FileNotFoundError(f"File not found {self.__path}")
        with self.__path.open() as fd:
            lines = [line.strip() for line in fd.readlines()]
            self.__data = np.array(lines, dtype="float")
            self.__is_read = True

    def path(self):
        return self.__path

    def is_valid_file_name(self):
        if self.__path.is_dir() or self.__path.suffix != ".txt":
            return False
        return True

    def exists(self):
        return self.__path.exists()

    def data(self):
        if not self.__is_read:
            self._read()
        return self.__data

    def create_file(self, data: npt.NDArray):
        if not self.is_valid_file_name():
            raise ValueError(f"Invalid normfactor filename {self.path()}")
        with self.path().open("w") as fd:
            np.savetxt(
                fd,
                np.array(data),
                fmt="%3.5f",
            )

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f"Normfactors {self.path()}"
