import numpy as np

from m23.extract import calculate_star_sky_adu, get_star_background_boxes


def sky_bg_fn(position):
    row, col = position
    return row**2 + col - 5


def generate_backgrounds():
    backgrounds = {}
    for row in range(16):
        for col in range(16):
            position = row, col
            backgrounds[position] = sky_bg_fn(position)
    return backgrounds


class TestStarSkyBg:
    backgrounds = generate_backgrounds()
    box_width = 64

    def pos(self, x, y):
        # We mimic IDL convention where x is considered a col unlike in Python
        row, col = y, x
        return row // self.box_width, col // self.box_width

    def tests_boxes_1(self):
        position = 100, 50
        expected_boxes_col_rows = [(0, 1), (1, 1), (0, 1), (0, 1)]  # L,R,T,B
        assert set(expected_boxes_col_rows) == set(
            get_star_background_boxes(position, self.box_width)
        )

    def tests_boxes_2(self):
        position = 10, 64
        expected_boxes_col_rows = [(0, 0), (1, 0), (1, 0), (1, 0)]  # L,R,T,B
        assert set(expected_boxes_col_rows) == set(
            get_star_background_boxes(position, self.box_width)
        )

    def tests_boxes_3(self):
        position = 1023, 120
        expected_boxes_col_rows = [(1, 15), (2, 15), (1, 15), (1, 15)]  # L,R,T,B
        assert set(expected_boxes_col_rows) == set(
            get_star_background_boxes(position, self.box_width)
        )

    def test_bg_1(self):
        x, y = 50, 100
        b1 = sky_bg_fn(self.pos(x - 20, y))
        b2 = sky_bg_fn(self.pos(x + 20, y))
        b3 = sky_bg_fn(self.pos(x, y + 20))
        b4 = sky_bg_fn(self.pos(x, y - 20))

        expected = np.mean([b1, b2, b3, b4])
        result = calculate_star_sky_adu((x, y), self.backgrounds, self.box_width)
        assert expected == result

    def test_bg_2(self):
        x, y = 70, 1020
        b1 = sky_bg_fn(self.pos(x - 20, y))
        b2 = sky_bg_fn(self.pos(x + 20, y))
        b3 = sky_bg_fn(self.pos(x, y))
        b4 = sky_bg_fn(self.pos(x, y - 20))

        expected = np.mean([b1, b2, b3, b4])
        result = calculate_star_sky_adu((x, y), self.backgrounds, self.box_width)
        assert expected == result
