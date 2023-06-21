import datetime
from typing import Tuple

import numpy as np


def angle_of_elevation(date: datetime.datetime, object="M23") -> Tuple[float, float]:
    """
    Returns the angle of elevation of the interested sky object with its
    uncertainty The date and time is given in UTC.

    param: date: datetime of observation
    param: object: the name of the object you're interested. Default: M23

    return: tuple of the angle of elevation and the uncertainty of measurement
    """
    yr, mo, dy = date.year, date.month, date.day
    hour, minute, sec = date.hour, date.minute, date.second

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
    else:
        AE = np.mean(angle_list)

    return (AE, uncertainty)
