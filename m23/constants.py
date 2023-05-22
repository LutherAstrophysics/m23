from datetime import date

ASSUMED_MAX_BRIGHTNESS = 65_000

# Input folder/file name conventions
INPUT_CALIBRATION_FOLDER_NAME = "Calibration Frames"
M23_RAW_IMAGES_FOLDER_NAME = "m23"

# Date related settings
INPUT_NIGHT_FOLDER_NAME_DATE_FORMAT = "%B %d, %Y"
OUTPUT_NIGHT_FOLDER_NAME_DATE_FORMAT = "%B %d, %Y"
LOG_FILE_COMBINED_FILENAME_DATE_FORMAT = "%m-%d-%y"
FLUX_LOG_COMBINED_FILENAME_DATE_FORMAT = "%m-%d-%y"
COLOR_NORMALIZED_FILENAME_DATE_FORMAT = "%m-%d-%y"

# Output folder/file name conventions
CONFIG_FILE_NAME = "config.toml"
OUTPUT_CALIBRATION_FOLDER_NAME = "Calibration Frames"
ALIGNED_COMBINED_FOLDER_NAME = "Aligned Combined"
LOG_FILES_COMBINED_FOLDER_NAME = "Log Files Combined"
FLUX_LOGS_COMBINED_FOLDER_NAME = "Flux Logs Combined"
COLOR_NORMALIZED_FOLDER_NAME = "Color Normalized"
CHARTS_FOLDER_NAME = "Charts"
MASTER_DARK_NAME = "masterdark.fit"
MASTER_FLAT_NAME = "masterflat.fit"

# INTRA_NIGHT
# Any star that appears more than this threshold away from the reference file
# will be masked out during intra night normalization
INTRA_NIGHT_IMPACT_THRESHOLD_PIXELS = 2

# MISC
CAMERA_CHANGE_2022_DATE = date(2022, 6, 16)
TYPICAL_NEW_CAMERA_CROP_REGION = [
    [[0, 448], [0, 0], [492, 0], [210, 181]],
    [[0, 1600], [0, 2048], [480, 2048], [210, 1867]],
    [[1400, 2048], [2048, 2048], [2048, 1500], [1834, 1830]],
    [[1508, 0], [1852, 241], [2048, 521], [2048, 0]],
]
