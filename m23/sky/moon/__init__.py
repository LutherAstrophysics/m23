import datetime
import decimal
import math
from typing import Union

import ephem
import numpy as np

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


def angle_of_elevation(
    date, object="M23"
):  # Returns the angle of elevation of the interested sky object with its uncertainty
    # date parameter is provided in a tuple/list (year, month,day,hour,minute,second)
    # The date and time is given in UTC
    yr, mo, dy, hour, minute, sec = date

    long = 91.79  # This is the longitude of Decorah where we do our observations
    Lat = 43.3017  # This is the latitude of Decorah where we do our observations

    if object == "M23":
        RA = (17 / 24 + 58 / (60 * 24) + 16 / (3600 * 24)) * 360
        DEC = -(19 + 1 / 60 + 7 / 3600)
    elif object == "NGC2286":
        RA = (6 / 24 + 48 / (60 * 24) + 44 / (3600 * 24)) * 360
        DEC = -(3 + 10 / 60 + 8 / 3600)
    elif object == "NGC129":
        RA = (0 / 24 + 31 / (60 * 24) + 14 / (3600 * 24)) * 360
        DEC = 60 + 20 / 60 + 12 / 3600
    elif object == "NGC7380":
        RA = (22 / 24 + 48 / (60 * 24) + 14 / (3600 * 24)) * 360
        DEC = 58 + 14 / 60 + 51 / 3600
    else:
        raise Exception("Invalid object")

    angle_list = np.zeros(31)
    for n in range(31):
        # The following code is all done to find the local sidereal time
        minu = minute - 15 + 30 / len(angle_list) * (n + 1)
        # Varying the time splits the 30 minutes into n chunks.

        JDo = (
            367 * (yr)
            - np.floor(7 * (yr + np.floor((mo + 9) / 12)) / 4)
            + np.floor((275 * mo) / 9)
            + dy
            + 1721013.5
        )
        # Calculates the julian date
        tuti = (JDo - 2451545.0) / 36525
        # The number of julian centuries since the epoch J2000

        GSToo = (
            100.4606184
            + 36000.77005361 * tuti
            + 0.00039 * tuti**2
            - 2.6 * 10 ** (-8) * tuti**3
        ) % 360  # GST at the beginning of the dy of interest

        GST = (GSToo + 0.25068447733746215 * (hour * 60 + minu + sec / 60)) % 360

        LST = (GST - long) % 360

        # We now have the RA and DEC of our zenith at the current time. We can use
        # simple spherical trig to calculate the angular separation between the
        # cluster/object and our zenith

        zAngle = np.degrees(
            np.arccos(
                np.sin(DEC * np.pi / 180) * np.sin(Lat * np.pi / 180)
                + np.cos(DEC * np.pi / 180)
                * np.cos(Lat * np.pi / 180)
                * np.cos((LST - RA) * np.pi / 180)
            )
        )
        altAngle = 90 - zAngle
        angle_list[n] = altAngle

    angle_of_elevation_unc = np.std(angle_list)

    uncertainty = round(angle_of_elevation_unc, 1)

    if uncertainty >= 10:
        AE = np.round(np.mean(angle_list), -1)
    elif uncertainty >= 1:
        AE = np.round(np.mean(angle_list))
    elif uncertainty >= 0.1:
        AE = np.round(np.mean(angle_list), 1)
    elif uncertainty >= 0.01:
        AE = np.round(np.mean(angle_list), 2)

    return (AE, uncertainty)


def get_moon_DE_and_RA(
    date,
):  # Returns the declination and right ascension of the moon for the given date and time in UTC
    # date parameter is given as a string 'year/month/day hh:mm:ss'

    observer = ephem.Observer()  # Decorah's latitude and longitude
    observer.lat = "43.3017"
    observer.lon = "91.79"

    # Royal Greenwich Observatory
    # observer.lat = '51.4769'
    # observer.lon = '0.0005'

    observer.date = date
    moon = ephem.Moon()

    moon.compute(observer)  # Gets the moon's RA and DE

    ra = moon.ra * 12 / ephem.pi  # Right ascension in hours
    dec = moon.dec * 180 / ephem.pi  # Declination in degrees

    return (dec, ra)


def moon_distance(
    moon_DE, moon_RA
):  # Returns the angle distance between the moon and our m23 cluster
    # Note that DE is in degrees, RA is in hours
    # To convert RA to degrees, multiply by 15

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
