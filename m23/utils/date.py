from datetime import datetime


def get_closet_date(base_date: str, list_of_dates: str, format: str):
    """
    From the list of dates, chooses a date that is closest to
    a particular date.

    param base_date : The base date from which to evaluate distance of other dates
    param list_of_dates : Dates to choose from
    format: The string format in which dates are present
    return : an item from list_of_dates
    """

    # Raise error is the list_of_dates is empty
    if len(list_of_dates) == 0:
        raise ValueError("No dates to choose from")

    def make_datetime(x: str):
        return datetime.strptime(x, format)

    base_datetime = make_datetime(base_date)
    list_of_datetimes = list(map(make_datetime, list_of_dates))

    list_of_datetimes.sort(key=lambda x: abs((base_datetime - x)).days)
    return list_of_datetimes[0].strftime(format)


raw_data_name_format = "%B %d, %Y"
