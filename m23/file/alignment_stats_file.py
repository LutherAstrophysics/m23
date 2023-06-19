from datetime import date
from pathlib import Path

from m23.align import AlignmentTransformationType
from m23.constants import ALIGNED_STATS_FILE_DATE_FORMAT


class AlignmentStatsFile:
    @classmethod
    def generate_file_name(cls, night_date: date) -> str:
        """
        Generates filename based on the given `night_date`
        """
        return f"m23_aligned_stats_{night_date.strftime(ALIGNED_STATS_FILE_DATE_FORMAT)}.txt"

    def __init__(self, file_path) -> None:
        self.__path = Path(file_path)
        self.__is_read = False

    def path(self):
        return self.__path

    def create_file_and_write_header(self):
        """
        Create a file (wipes out if the file already exists)
        and writes header in the file
        """
        with open(self.path(), "w") as fd:
            fd.write(
                f"{'Image_Name':<30s}"
                f"{'Rotation':<20s}"
                f"{'Translation_X':<15s}"
                f"{'Translation_Y':<15s}"
                f"{'Scale':<10s}\n"
            )

    def add_record(self, image_name: str, alignment_stats: AlignmentTransformationType):
        """
        Adds a record to the file based on the provided `alignment_stats`
        """
        rotation, translation_x, translation_y, scale = alignment_stats
        with open(self.path(), "a") as fd:
            fd.write(
                f"{image_name:<30}"
                f"{rotation:<20.9f}"
                f"{translation_x:<15.3f}"
                f"{translation_y:<15.3f}"
                f"{scale:<10.3f}\n"
            )

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f"Aligned combined file: {self.path()}"
