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
