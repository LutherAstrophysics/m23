from pathlib import Path

from m23.reference import get_reference_files_dict


def test_ref_files_dict():
    reference_files_dict = get_reference_files_dict()
    for key, file_name in reference_files_dict.items():
        assert Path(file_name).exists()
