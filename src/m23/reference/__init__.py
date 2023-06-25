from pathlib import Path

from m23 import REFERENCE_DIR


def get_reference_files_dict():
    ref = {
        "color": str(Path(REFERENCE_DIR) / "MeanRI100.txt"),
        "file": str(Path(REFERENCE_DIR) / "ref_no_na_w_2509_10.txt"),
        "image": str(Path(REFERENCE_DIR) / "m23_3.5_071.fit"),
        "logfile": str(Path(REFERENCE_DIR) / "08-05-03_m23_3.5-071.txt"),
    }
    return ref
