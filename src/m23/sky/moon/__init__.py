import datetime
import decimal
import math
from typing import Union

import ephem
import numpy as np

dec = decimal.Decimal

# Most of the code for Moon `position` and `phase` was taken from
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
    WaningCrescent = "Waning_Crescent"


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
        7: MoonPositions.WaningCrescent,
    }[int(index) & 7]


def get_moon_DE_and_RA(
    date: datetime.datetime,
):  # Returns the declination and right ascension of the moon for the given date and time in UTC
    # date parameter is given as a string 'year/month/day hh:mm:ss'

    observer = ephem.Observer()  # Decorah's latitude and longitude
    observer.lat = "43.3017"  # North is considered +ve
    observer.lon = "-91.79"  # West is considered -ve

    observer.date = date
    moon = ephem.Moon()

    moon.compute(observer)  # Gets the moon's RA and DE

    ra = moon.ra * 12 / ephem.pi  # Right ascension in hours
    dec = moon.dec * 180 / ephem.pi  # Declination in degrees

    return (dec, ra)


def moon_distance(
    date: datetime.datetime,
):
    """
    Returns the angle distance (in degrees) between the moon and our m23 cluster
    Note that the date is UTC date
    """

    # Note that DE is in degrees, RA is in hours
    # To convert RA to degrees, multiply by 15
    moon_DE, moon_RA = get_moon_DE_and_RA(date)

    # M23 declination and right ascension
    cluster_RA = 269.5667
    cluster_DE = -19.0186

    moon_alpha = moon_DE * np.pi / 180  # Moon declination in radians
    moon_beta = moon_RA * 15 * np.pi / 180  # Moon right ascension in radians

    cluster_alpha = cluster_DE * np.pi / 180  # Cluster declination in radians
    cluster_beta = cluster_RA * np.pi / 180  # Cluster right ascension in radians

    beta_difference = np.abs(moon_beta - cluster_beta)

    angle_cos = np.sin(moon_alpha) * np.sin(cluster_alpha) + np.cos(moon_alpha) * np.cos(
        cluster_alpha
    ) * np.cos(beta_difference)
    angle = np.arccos(angle_cos)  # Angle in radians between the two objects

    return angle * 180 / np.pi
