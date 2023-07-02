import math

import numpy as np

from m23.extract.bg import SkyBgCalculator


class TestPixelBg:
    def test_px_1(self):
        x, y = 746.58, 459.64
        expected_box_row = y // 128
        expected_box_col = x // 128
        expected_small_box_no = (y - (expected_box_row * 128)) // 32

        assert SkyBgCalculator.get_box_number(x, y) == (
            expected_box_row,
            expected_box_col,
            expected_small_box_no,
        )

    def test_box_details(self):
        image = np.arange(1024 * 1024).reshape(1024, 1024)
        assert image.shape == (1024, 1024)
        assert image[5][3] == 1024 * 5 + 3
        box_row_col_small_box = (2, 7, 3)  # row, col, row strip no.
        box = SkyBgCalculator(image).get_image_data_at_box(box_row_col_small_box)
        assert box.shape == (32, 128)
        expected_row = (128 * 2) + (32 * 3) + (10)
        expected_col = 128 * 7 + 5
        assert box[10][5] == image[expected_row][expected_col]

    def test_px_bg(self):
        image = np.arange(1024 * 1024).reshape(1024, 1024)
        box_row_col_small_box = (2, 7, 3)  # row, col, row strip no.
        bg_calculator = SkyBgCalculator(image)
        box = bg_calculator.get_image_data_at_box(box_row_col_small_box)
        box_row, box_col, small_box = box_row_col_small_box
        box_local_row, box_local_col = 5, 15
        pixel_row = box_row * 128 + small_box * 32 + box_local_row
        pixel_col = box_col * 128 + box_local_col
        assert bg_calculator.get_box_number(pixel_col, pixel_row) == box_row_col_small_box
        assert box.shape == (32, 128)
        box_values_col_and_adu = []
        for row in range(32):
            for col in range(128):
                adu = box[row][col]
                if adu > 0:
                    box_values_col_and_adu.append((col, adu))
        box_values_col_and_adu.sort(key=lambda x: x[1])
        mid_values = box_values_col_and_adu[
            int(0.4 * len(box_values_col_and_adu)) : int(0.55 * len(box_values_col_and_adu)) + 1
        ]
        x_to_plot, y_to_plot = zip(*mid_values)
        fn = np.poly1d(np.polyfit(x=x_to_plot, y=y_to_plot, deg=2))
        pixel_local_col = pixel_col - 128 * box_col
        expected_adu = bg_calculator.calculate_bg_at_position(pixel_col, pixel_row)
        result = fn(pixel_local_col)
        assert abs((result - expected_adu)) < 0.00001
        # Expect increase towards right (higher col number)
        assert bg_calculator.calculate_bg_at_position(pixel_col + 1, pixel_row) > result
        assert bg_calculator.calculate_bg_at_position(pixel_col + 10, pixel_row) > result
        # Expect same ADU on the cell below (as the function is wrt. col not row)
        assert bg_calculator.calculate_bg_at_position(pixel_col, pixel_row + 1) == result
        assert bg_calculator.calculate_bg_at_position(pixel_col, pixel_row + 5) == result

    def test_star_positions(self):
        x, y = 746.58, 459.64
        radii = [3, 4, 5]
        for radius in radii:
            potential = []
            size = 2 * radius + 1
            zoo = [[0 for _ in range(size)] for _ in range(size)]
            for row in range(-radius, radius + 1):
                for col in range(-radius, radius + 1):
                    candidate = x + col, y + row
                    if math.ceil(math.sqrt((row) ** 2 + (col) ** 2)) <= radius:
                        potential.append(candidate)
                        zoo[row][col] = candidate

            expected = sorted(potential, key=lambda x: x[0])
            result = sorted(SkyBgCalculator.star_positions(x, y, radius), key=lambda x: x[0])
            assert expected == result

    def test_average_star_bg(self):
        image = np.arange(1024 * 1024).reshape(1024, 1024)
        star_position = 746.58, 459.64
        bg_calculator = SkyBgCalculator(image)
        radius = 4
        star_positions = bg_calculator.star_positions(*star_position, radius)
        adu_bg_sum = 0
        for p in star_positions:
            adu_bg_sum += bg_calculator.calculate_bg_at_position(*p)
        assert adu_bg_sum / len(star_positions) == bg_calculator.get_star_average_bg_per_pixel(
            star_position[0], star_position[1], radius
        )
