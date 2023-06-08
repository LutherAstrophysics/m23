import datetime
import decimal
import math
from typing import Union

dec = decimal.Decimal

# Most of this code was taken from
# https://gist.github.com/miklb/ed145757971096565723


class MoonPositions:
    # Underscores instead of spaces are used for ease with csv processing
    NewMoon = "New_Moon"
    WaxingCrescent = "Waxing_Crescent"
    FirstQuarter = "First_Quarter"
    WaxingGibbous = "Waxing_Gibbous"
    FullMoon = "Full_Moon"
    WaningGibbous = "Waning_Gibbous"
    LastQuarter = "Last_Quarter"
    WaningCresce = "Waning_Crescent"


def position(now=None):
    """
     Returns a decimal representation for the phase of the moon
    Takes into account waning and waxing. Full moon is about 0.5
    """
    if now is None:
        now = datetime.datetime.now()

    diff = now - datetime.datetime(2001, 1, 1)
    days = dec(diff.days) + (dec(diff.seconds) / dec(86400))
    lunations = dec("0.20439731") + (days * dec("0.03386319269"))

    return lunations % dec(1)


def phase(d: Union[datetime.date, datetime.datetime]):
    """
    Returns the phase (in str) of the moon in the given date
    """
    pos = position(d)
    index = (pos * dec(8)) + dec("0.5")
    index = math.floor(index)
    return {
        0: MoonPositions.NewMoon,
        1: MoonPositions.WaxingCrescent,
        2: MoonPositions.FirstQuarter,
        3: MoonPositions.WaxingGibbous,
        4: MoonPositions.FullMoon,
        5: MoonPositions.WaningGibbous,
        6: MoonPositions.LastQuarter,
        7: MoonPositions.WaningCresce,
    }[int(index) & 7]
