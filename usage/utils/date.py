###
### Boilerplate
import sys

if "../../" not in sys.path:
    sys.path.insert(0, "../../")

from m23.utils import get_closet_date

print(
    get_closet_date(
        "April 18, 2019",
        ["April 2, 2018", "July 24, 2019", "June 12, 2019", "March 12, 2019"],
        "%B %d, %Y",
    )
)
