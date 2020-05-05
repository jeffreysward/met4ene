"""
Functions that simplify running in a linux environment.


Known Issues/Wishlist:

"""

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
