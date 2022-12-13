# Instead of modifying this file, use this as a reference
# and create your own copy of the file in this directory
# named my_renormalize_generator*, or in the experiment folder
# Those files will be gitignored and will help us keep our git
# history clean

import pprint

from analyze_flux_logs_combined import analyze_year

year = 2018
folder_location = "C:/Data Processing/2018 Python Processed"
year_to_analyze = "F:/Data Processing/Summer 2018 M23"
default_reference_file = "C:/Data Processing/RefImage/ref_revised_71.txt"


result = analyze_year(year_to_analyze, print_result=False)

for i in range(len(result)):
    result[i] = (
        f"{folder_location}/{result[i][0]}, {year}",
        result[i][1],
        result[i][2],
        default_reference_file,
    )
pp = pprint.PrettyPrinter(width=100, compact=True)
pp.pprint(result)
