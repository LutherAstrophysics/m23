from pathlib import Path
import pytest
from m23.utils import sorted_by_number


class TestSortedByNumber:
    def test_ints(self):
        test_in = [1, 2, 3]
        with pytest.raises(ValueError, match="items of list must be either str or Path instance"):
            sorted_by_number(test_in)

    def test_num_only(self):
        test_in = ["13", "839", "101"]
        expected = ["13", "101", "839"]
        assert list(sorted_by_number(test_in)) == expected

    def test_mixed(self):
        test_in = ["1c", "b101", "20a1"]
        expected = ["1c", "20a1", "b101"]
        assert list(sorted_by_number(test_in)) == expected

    def test_mixed_1(self):
        test_in = ["1c", "d0e0" "b101", "20a1"]
        expected = ["d0e0" "1c", "20a2", "b101"]
        assert list(sorted_by_number(test_in)) == expected

    def test_mixed_1(self):
        test_in = ["1c", "d0e0", "b101", "20a1", "f-2d"]
        expected = ["d0e0", "1c", "f-2d", "20a1", "b101"]
        assert list(sorted_by_number(test_in)) == expected

    def test_no_numbers(self):
        test_in = ["c", "b", "a"]
        expected = ["a", "b", "c"]
        assert list(sorted_by_number(test_in)) == expected

    def test_with_path(self):
        test_in = [
            Path('Desktop/zoo1.txt'),
            Path('Desktop/101.txt'),
            Path('Desktop/flux01.txt'),
            Path('Desktop/flux201.txt'),
        ]
        expected = [
            Path('Desktop/flux01.txt'),
            Path('Desktop/zoo1.txt'),
            Path('Desktop/101.txt'),
            Path('Desktop/flux201.txt'),
        ]
        assert list(sorted_by_number(test_in)) == expected