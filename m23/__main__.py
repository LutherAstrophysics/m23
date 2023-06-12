import argparse
import sys
from pathlib import Path

from m23.processor import (
    create_nights_csv,
    generate_masterflat,
    renormalize,
    start_data_processing,
)


def process(args):
    """
    This is a subcommand that handles data processing for one or more nights
    based on the configuration file path provided
    """
    config_file: Path = args.config_file
    if not config_file.exists():
        sys.stdout.write(f"Provided file {config_file} doesn't exist\n")
        return
    if not config_file.is_file():
        sys.stdout.write("Invalid configuration file provided\n")
        return
    start_data_processing(config_file.absolute())


def norm(args):
    """
    This is a subcommand that handles renormalization for one or more nights
    based on the configuration file path provided
    """
    config_file: Path = args.config_file
    if not config_file.exists():
        sys.stdout.write(f"Provided file {config_file} doesn't exist\n")
        return
    if not config_file.is_file():
        sys.stdout.write("Invalid configuration file provided\n")
        return
    renormalize(config_file.absolute())


def mf(args):
    """
    This is a subcommand that handles generating masterflat for a night from
    the flat images taken for the night
    """
    config_file: Path = args.config_file
    if not config_file.exists():
        sys.stdout.write(f"Provided file {config_file} doesn't exist\n")
        return
    if not config_file.is_file():
        sys.stdout.write("Invalid configuration file provided\n")
        return
    generate_masterflat(config_file.absolute())


def csv(args):
    """
    This is a subcommand that generates the csv file which holds the stars' flux
    values for a year, this will be later used to get the data onto our server
    """
    config_file: Path = args.config_file
    if not config_file.exists():
        sys.stdout.write(f"Provided file {config_file} doesn't exist\n")
        return
    if not config_file.is_file():
        sys.stdout.write("Invalid configuration file provided\n")
        return
    create_nights_csv(config_file.absolute())


parser = argparse.ArgumentParser(prog="M23 Data processor", epilog="Made in Rapti")
subparsers = parser.add_subparsers()

# We are dividing our command line function into subcommands
# The first subcommand is `process` denoting a full fledged data processing for night(s)
process_parser = subparsers.add_parser("process", help="Process raw data for one or more nights")
process_parser.add_argument(
    "config_file", type=Path, help="Path to toml configuration file for data processing"
)  # positional argument
# Adding a default value so we later know which subcommand was invoked
process_parser.set_defaults(func=process)

# Renormalize parser
norm_parser = subparsers.add_parser(
    "norm", help="Normalize log files combined for one or more nights"
)
norm_parser.add_argument(
    "config_file", type=Path, help="Path to toml configuration file for renormalization"
)  # positional argument
# Adding a default value so we later know which subcommand was invoked
norm_parser.set_defaults(func=norm)

# Masterflat generator parser
mf_parser = subparsers.add_parser("mf", help="Generate masterflat for a night from its raw flats")
mf_parser.add_argument(
    "config_file",
    type=Path,
    help="Path to toml configuration file for master flat generation",
)  # positional argument
# Adding a default value so we later know which subcommand was invoked
mf_parser.set_defaults(func=mf)

# CSV generator parser
csv_parser = subparsers.add_parser("csv", help="Generate csv flux file for a given year")
csv_parser.add_argument(
    "config_file", type=Path, help="Path to toml configuration file for csv generation"
)  # positional argument
# Adding a default value so we later know which subcommand was invoked
csv_parser.set_defaults(func=csv)

args = parser.parse_args()
if hasattr(args, "func"):
    args.func(args)
else:
    parser.parse_args(["-h"])
