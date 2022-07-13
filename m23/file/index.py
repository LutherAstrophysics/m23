import re

def getLinesWithNumbersFromFile(fileName):
    with open(fileName, "r") as fd:
            allLines = [line.strip() for line in fd.readlines()]
            return list(
                filter(
                    lambda line: re.search("\d+", line) and not re.search("[a-zA-Z]", line),
                    allLines,
                )
            )
        