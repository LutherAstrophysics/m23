from datetime import date
from pathlib import Path


class MasterflatFile:
    @classmethod
    def generate_file_name(cls, night_date: date) -> str:
        """
        Generates a masterflat filename based on the night date

        Param: night_date: The date of the night for which to generate filename
        Returns: Filename string
        """
        date_string = night_date.strftime("%Y-%m-%d")  # YYYY-MM-DD format
        return f"{date_string}_masterflat.fit"

    def __init__(self, file_path: Path) -> None:
        self.__path = file_path
        self.__data = None

    def _validate_file(self):
        """Validates that the file exists"""
        if not self.path().exists():
            raise FileNotFoundError(f"{self.path()}")
        if not self.path().is_file():
            ValueError(f"{self.path()} isn't a file")
        if not self.path().suffix == ".fit":
            ValueError(f"{self.path()} isn't a fit file")

    def _read_data(self):
        # TODO
        pass

    def path(self):
        return self.__path

    def data(self):
        self._validate_file()
        return self.__data

    def save_file(self, data, header=None):
        # TODO
        pass

    def get_data(self, data, header=None):
        # TODO
        pass
