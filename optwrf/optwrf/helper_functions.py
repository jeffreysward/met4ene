"""
Functions that support other optwrf modules.


Known Issues/Wishlist:

"""

import datetime
import math
from shutil import rmtree
import string


def remove_dir(directory, verbose=False):
    """
    This function utilized an exception clause to delete a directory.

    :param directory: string
        complete path to the directory to be removed.
    :param verbose: boolean (default=False)
        determining whether or not to print lots of model information to the screen.

    """

    try:
        rmtree(directory)
    except OSError as e:
        if verbose:
            print("OSError in remove_dir: %s - %s." % (e.filename, e.strerror))


def strfdelta(tdelta, fmt='{H:02}h {M:02}m {S:02}s', inputtype='timedelta'):
    """
    Convert a datetime.timedelta object or a regular number to a custom-
    formatted string, just like the stftime() method does for datetime.datetime
    objects.

    :param tdelta: datetime.timedelta object
        defining the difference in time that you would like to format.
    :param fmt: string
        allows custom formatting to be specified.  Fields can include
        seconds, minutes, hours, days, and weeks.  Each field is optional.

        Some examples:
            '{D:02}d {H:02}h {M:02}m {S:02}s' --> '05d 08h 04m 02s'
            '{H:02}:{M:02}:{S:02}'            --> '01:44:33' (default)
            '{W}w {D}d {H}:{M:02}:{S:02}'     --> '4w 5d 8:04:02'
            '{D:2}d {H:2}:{M:02}:{S:02}'      --> ' 5d  8:04:02'
            '{H}h {S}s'                       --> '72h 800s'.
    :param inputtype: string (default=timedelta)
        allowsing tdelta to be a regular number instead of the default,
        which is a datetime.timedelta object.  Valid inputtype strings:
            's', 'seconds',
            'm', 'minutes',
            'h', 'hours',
            'd', 'days',
            'w', 'weeks'.
    :return string
        formated to specification.

    """
    # Convert tdelta to integer seconds.
    if inputtype == 'timedelta':
        remainder = int(tdelta.total_seconds())
    elif inputtype in ['s', 'seconds']:
        remainder = int(tdelta)
    elif inputtype in ['m', 'minutes']:
        remainder = int(tdelta)*60
    elif inputtype in ['h', 'hours']:
        remainder = int(tdelta)*3600
    elif inputtype in ['d', 'days']:
        remainder = int(tdelta)*86400
    elif inputtype in ['w', 'weeks']:
        remainder = int(tdelta)*604800

    f = string.Formatter()
    desired_fields = [field_tuple[1] for field_tuple in f.parse(fmt)]
    possible_fields = ('W', 'D', 'H', 'M', 'S')
    constants = {'W': 604800, 'D': 86400, 'H': 3600, 'M': 60, 'S': 1}
    values = {}
    for field in possible_fields:
        if field in desired_fields and field in constants:
            values[field], remainder = divmod(remainder, constants[field])
    return f.format(fmt, **values)


def date2season(date):
    """
    Takes a timestamp and returns the corresponding season. Seasons are
    defined simply by month:
        Winter  Dec - Feb
        Spring  Mar - May
        Summer  Jun - Aug
        Fall    Sep - Nov

    :param date: timestamps
    :return seasons: list of strings
        corresponding to the season of the input date.

    """
    mo = date.month
    if mo in [12, 1, 2]:
        season = 'winter'
    elif mo in [3, 4, 5]:
        season = 'spring'
    elif mo in [6, 7, 8]:
        season = 'summer'
    elif mo in [9, 10, 11]:
        season = 'fall'
    else:
        print(f'{mo} is not a correct month code (1 - 12).')
        raise ValueError

    return season


def daylight(day, latitude=40):
    """
    This function calculates the number of daylight hours given jullian day of the year, and the latitude.
    For the optwrf work, I have set the default latitude to the 40th parallel since that cuts through
    the center of the domain.

    :param day: integer corresponding to jullian day of the year
    :param latitude: in degrees North
    :return daylightamount: float giving the numer of daylight hours

    """
    P = math.asin(0.39795 * math.cos(0.2163108 + 2 * math.atan(0.9671396 * math.tan(.00860 * (day - 186)))))
    pi = math.pi
    daylightamount = 24 - (24 / pi) * math.acos((math.sin(0.8333 * pi / 180) +
                                                 math.sin(latitude * pi / 180) * math.sin(P))
                                                / (math.cos(latitude * pi / 180) * math.cos(P)))
    return daylightamount


def daylight_frac(day, latitude=40):
    """
    Calculates the daylight fraction, i.e., the fraction created by dividing the number of daylight hours
    by the longest day of the year at a given latitude.

    :param day: integer corresponding to jullian day of the year
    :param latitude: in degrees North
    :return frac: nondimensional fraction of the daylight hours on the day vs the longest day

    """
    # Ensure that the day is a Julian day integer.
    if type(day) is int:
        if day > 365:
            print('The Julian day variable must be between 1 - 365')
            raise ValueError
        jday = day
    elif type(day) is str:
        dt = format_date(day)
        tt = dt.timetuple()
        jday = tt.tm_yday
    else:
        print(f'Day: ({day}) has an incorrect type: ({type(day)}).\nPlease input an int or str.')
        raise TypeError

    # Calculate the daylight amount
    daylightamount = daylight(jday, latitude)
    # Calculate the longest day
    daylengths = [daylight(d, latitude) for d in range(1, 366)]
    longestday = max(daylengths)
    # Calculate the daylight fraction
    frac = daylightamount/longestday
    return frac


def format_date(in_date):
    """
    Formats an input date so that it can be correctly written to the namelist.

    :param in_date : string
        string specifying the date
    :return: datetime64 array specifying the date

    """
    for fmt in ('%b %d %Y', '%B %d %Y', '%b %d, %Y', '%B %d, %Y',
                '%m-%d-%Y', '%m.%d.%Y', '%m/%d/%Y',
                '%b %d %Y %H', '%B %d %Y %H', '%b %d, %Y %H', '%B %d, %Y %H',
                '%m-%d-%Y %H', '%m.%d.%Y %H', '%m/%d/%Y %H'):
        try:
            return datetime.datetime.strptime(in_date, fmt)
        except ValueError:
            pass
    raise ValueError('No valid date format found; please use a common US format (e.g., Jan 01, 2011 00)')
