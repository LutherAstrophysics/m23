import re
from collections import namedtuple
from datetime import date, datetime
from pathlib import Path
from typing import Dict

from m23.file.aligned_combined_file import AlignedCombinedFile


# Note that LogFileCombined is the one that that has the data for aligned combined
# images after extracting stars from the image. This is not to be confused with FluxLogCombined
# that is created after intra-night normalization (note *not* internight normalization)
class LogFileCombinedFile:
    # Class attributes
    header_rows = 9
    date_format = "%m-%d-%y"
    file_name_re = re.compile(
        "(\d{2}-\d{2}-\d{2})_m23_(\d+\.?\d*)-ref_revised_71_(\d{3, 4})_flux.txt"
    )

    StarLogfileCombinedData = namedtuple(
        "StarLogfileCombinedData", ["x", "y", "xFWHM", "yFWHM", "avgFWHM", "sky_adu", "radii_adu"]
    )
    LogFileCombinedDataType = Dict[int, StarLogfileCombinedData]

    @classmethod
    def generate_file_name(cls, night_date: date, star_no: int, img_duration: float):
        """
        Returns the file name to use for a given star night for the given night date
        param : night_date: Date for the night
        param: star_no : Star number
        param: img_duration : the duration of images taken on the night
        """
        return f"{night_date.strftime(cls.date_format)}_m23_{img_duration}-ref_revised_71_{star_no:04}_flux.txt"

    def __init__(self, file_path: str) -> None:
        self.__path = Path(file_path)
        self.__is_read = False
        self.__data = None

    def _read(self):
        self.__is_read = True

    def is_valid_file_name(self) -> bool:
        """
        Checks if the filename matches the naming convention
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
                self.date_format,
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

    def path(self):
        self.__path

    def data(self):
        if not self.__is_read:
            self._read()
        return self.__data

    def write(
        self,
        data: LogFileCombinedDataType,
        aligned_combined_file: AlignedCombinedFile,
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
            radii = data[data.keys()[0]].radii_adu.keys()

        stars = sorted(data.keys())
        no_of_stars = len(stars)
        with self.path().open("w") as fd:
            fd.write("\n")
            fd.write(
                f"Star Data Extractor Tool: (Note: This program mocks format of AIP_4_WIN) \n"
            )
            fd.write(f"\tImage {aligned_combined_file}:\n")
            fd.write(f"\tTotal no of stars: {no_of_stars}\n")
            fd.write(f"\tRadius of star diaphragm: {', '.join(map(str, radii))}\n")
            fd.write(f"\tSky annulus inner radius: \n")
            fd.write(f"\tSky annulus outer radius: \n")
            fd.write(f"\tThreshold factor: \n")

            headers = [
                "X",
                "Y",
                "XFWHM",
                "YFWHM",
                "Avg FWHM",
                "Sky ADU",
            ] + [f"Star ADU {radius}" for radius in radii]
            for header in headers:
                fd.write(f"{header:>16s}")
            fd.write("\n")

            for star in stars:  # Sorted in ascending order by star number
                star_data = data[star]
                fd.write(
                    f"{star_data.x:>16.2f}{star_data.y:>16.2f}{star_data.xFWHM:>16.4f}{star_data.yFWHM:>16.4f}{star_data.avgFWHM:>16.4f}{star_data.sky_adu:>16.2f}"
                )
                for radius in radii:
                    fd.write(f"{star_data.radii_adu[radius]}")
                fd.write("\n")

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f"Log file combined: {self.__path}"
