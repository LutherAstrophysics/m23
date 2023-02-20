import re
from pathlib import WindowsPath


def getLinesWithNumbersFromFile(fileName):
    with open(fileName, "r") as fd:
        allLines = [line.strip() for line in fd.readlines()]
        return list(
            filter(
                lambda line: re.search("\d+", line) and not re.search("[a-zA-Z]", line),
                allLines,
            )
        )


def formatWindowsPath(p: WindowsPath):
    # The anchor trickery was need to remove windows backward slash
    return "/".join([p.drive] + list(p.parts[1:]))


def is_string_float(string: str) -> bool:
    """
    Checks is the string is a float value.

    Example:
    is_string_float('1.1') -> True
    is_string_float('10a') -> False
    is_string_float('10') -> True
    is_string_float('1.1 .  ') -> True
    is_string_float('    1.7    ') -> True
    """
    try:
        float(string)
        return True
    except:
        return False
