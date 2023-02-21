import re
from pathlib import Path

from astropy.io.fits import getdata as getfitsdata


class RawImageFile:
    # Class attributes
    file_name_re = re.compile("m23_(\d+\.?\d*)-(\d+).fit")

    def __init__(self, file_path: str) -> None:
        self.__path = Path(file_path)
        self.__is_read = False
        self.__data = None

    def _read(self):
        if not self.exists():
            raise FileNotFoundError(f"File not found {self.path()}")
        if not self.path().is_file() and self.__path.suffix != ".fit":
            raise ValueError(f"Invalid fit file {self.path()}")
        self.__data = getfitsdata(self.path())
        self.__is_read = True

    def exists(self):
        return self.path().exists()

    def path(self):
        return self.__path

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
        return float(self.file_name_re.match(self.path().name)[2])

    def data(self):
        if not self.__is_read:
            self._read()
        return self.__data

    def __repr__(self):
        return self.__str__()

    def __str__(self) -> str:
        return f"Raw Image {self.path().name}"
