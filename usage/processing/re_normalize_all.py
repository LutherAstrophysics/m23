# This file makes it easier to call re_normalize on a bunch of nights

# Please don't modify this file
# Copy the contents of this to my_renormalize_all.py in the same folder
# that this is in. Then run the script.
# This way this file can stay as a reference and don't need to be re-committed
# to git everytime someone call this for different night.

from re_normalize import re_normalize

default_reference_file = "C:/Data Processing/RefImage/ref_revised_71.txt"

# To normalize takes a tuple of the followings:
#   1. folder where the data is stored
#   2. Start image index : integer
#   3. Last image index : integer
#   4. Ref file location

# Note that you might have to use forward slash instead of backward for file path (in windows as well)

# You can do this for multiple nights by adding more tuples to the following list.
to_normalize = [
    ("C:/Data Processing/2019 Python Processed/July 23, 2019", 2, 79, default_reference_file),
]

for night in to_normalize:
    re_normalize(*night)
