import sys

if "../../" not in sys.path:
    sys.path.insert(0, "../../")

import numpy as np
from normalize import normalizeLogFiles

refFileName = r"C:\Data Processing\RefImage\ref_revised_71.txt"

logFileNames = [
    rf"C:\Data Processing\xxx\exp-old\Log Files Combined\log-file-{number}.txt"
    for number in ["0-10", "10-20", "20-30", "30-40", "40-50", "50-60"]
]

saveAs = r"C:\Data Processing\xxx\exp-old\Flux Logs Combined"
