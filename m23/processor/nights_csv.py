import csv
import random

from m23.file.color_normalized_file import ColorNormalizedFile
from m23.processor.nights_csv_config_loader import (
    NightsCSVConfig, validate_nights_csv_config_file)


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
    while output_file.exists():
        output_file = output_folder / f"flux{random.randrange(1, 100)}.txt"
    color_normalized_files = [
        ColorNormalizedFile(file) for file in config['color_normalized_files']
        ]
    color_normalized_files = sorted(
        color_normalized_files, 
        key=lambda x : x.night_date()
        )

    stardata = [color_normalized_files[i].data() for i in range(len(color_normalized_files))]   
    night_dates = [str(color_normalized_files[i].night_date()) for i in range(len(color_normalized_files))]
    
    with open(output_file, 'w', newline = '') as file: 
        writer = csv.writer(file)
        writer.writerow(['Star #'] + night_dates)
        for starno in range(len(stardata[0])): # Writes the data of 2510 stars
                star_data = [stardata[i][starno+1].normalized_median_flux for i in range(len(color_normalized_files))]
                writer.writerow([str(starno+1)] + star_data)
        if len(stardata[0]) == 2508: # If no data for stars 2509 and 2510, then write them as empty 
            writer.writerow(['2509'] + ['0' for i in range(len(color_normalized_files))])
            writer.writerow(['2510'] + ['0' for i in range(len(color_normalized_files))])
    file.close()

def create_nights_csv(file_path: str):
    """
    Creates and saves a csv of star fluxes for night specified in the  
    contents of the `file_path`. This function calls  
    `validate_nights_csv_config_file` to do most of its job
    """
    validate_nights_csv_config_file(file_path, create_nights_csv_auxiliary)
