import random

from m23.file.color_normalized_file import ColorNormalizedFile
from m23.processor.nights_csv_config_loader import (
    NightsCSVConfig,
    validate_nights_csv_config_file,
)


def create_nights_csv_auxiliary(config: NightsCSVConfig):
    """
    Creates and saves a csv of star fluxes for night specified in the  
    contents of the `file_path`.
    """
    output_name = 'fluxes.txt'
    output_folder = config['output']
    output_file = output_folder / output_name
    # We ensure that the filename doesn't already exist so that we don't override
    # existing file 
    while not output_file.exists():
        output_file = output_folder / f"flux{random.randrange(1, 100)}.txt"
    color_normalized_files = [
        ColorNormalizedFile(file) for file in config['color_normalized_files']
        ]
    color_normalized_files = sorted(
        color_normalized_files, 
        key=lambda x : x.night_date()
        )
    
     
     

def create_nights_csv(file_path: str):
    """
    Creates and saves a csv of star fluxes for night specified in the  
    contents of the `file_path`. This function calls  
    `validate_nights_csv_config_file` to do most of its job
    """
    validate_nights_csv_config_file(file_path, create_nights_csv_auxiliary)