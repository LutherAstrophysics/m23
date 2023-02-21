from pathlib import Path

import numpy as np


class NormfactorFile:
    def __init__(self, file_path: str) -> None:
        self.__path = Path(file_path)
        self.__data = None
        self.__is_read = False

    def _read(self):
        self.is_valid_file()
        if not self.exists():
            raise FileNotFoundError(f"File not found {self.__path}")
        with self.__path.open() as fd:
            lines = [line.strip() for line in fd.readlines()]
            self.__data = np.array(lines, dtype="float")
            self.__is_read = True

    def is_valid_file(self):
        if self.__path.is_dir() or self.__path.suffix != ".txt":
            raise ValueError("Invalid txt file {self.__path}")

    def exists(self):
        return self.__path.exists()

    def data(self):
        if not self.__is_read:
            self._read()
        return self.__data
