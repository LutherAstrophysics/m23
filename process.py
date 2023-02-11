import argparse
from pathlib import Path

from m23.processor.process_nights import start_data_processing

parser = argparse.ArgumentParser(
    prog="M23 Data processor", description="Created by trouts", epilog="Made in Rapti"
)

parser.add_argument("config_file")  # positional argument
args = parser.parse_args()

start_data_processing(Path(args.config_file))
