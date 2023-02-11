import argparse

from m23 import process

parser = argparse.ArgumentParser(
    prog="M23 Data processor", description="Created by trouts", epilog="Made in Rapti"
)

parser.add_argument("config_file")  # positional argument
args = parser.parse_args()

process(args.config_file)
