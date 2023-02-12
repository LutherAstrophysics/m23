import argparse
import sys
from pathlib import Path

from m23 import start_data_processing
from m23.processor import renormalize


def process(args):
    """
    This is a subcommand that handles data processing for one or more nights
    based on the configuration file path provided
    """
    config_file: Path = args.config_file
    if not config_file.exists():
        sys.stdout.write("Provided file doesn't exist\n")
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
        sys.stdout.write("Provided file doesn't exist\n")
        return
    if not config_file.is_file():
        sys.stdout.write("Invalid configuration file provided\n")
        return
    renormalize(config_file.absolute())


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


args = parser.parse_args()
if hasattr(args, "func"):
    args.func(args)
else:
    parser.parse_args(["-h"])
