"""
Functions that support other optwrf modules.


Known Issues/Wishlist:

"""

import csv
import datetime
import math
import os
import sys
from shutil import rmtree
import string

import requests


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
                '%Y-%m-%d', '%Y.%m.%d', '%Y/%m/%d',
                '%b %d %Y %H', '%B %d %Y %H', '%b %d, %Y %H', '%B %d, %Y %H',
                '%m-%d-%Y %H', '%m.%d.%Y %H', '%m/%d/%Y %H'):
        try:
            return datetime.datetime.strptime(in_date, fmt)
        except ValueError:
            pass
    raise ValueError('No valid date format found; please use a common US format (e.g., Jan 01, 2011 00)')


def determine_computer():
    """
    Determines which computer you are currently working on.
    WARNING: this only works for me on magma.

    :return on_aws: boolean
        True if working on the mzhang AWS account where the group name is 'ec2-user'
    :return on_cheyenne: boolean
        True if working on the NCAR Cheyenne super computer where the group name is 'ncar'
    :return on_magma: boolean
        True if working on Jeff Sward's account on the Cornell Magma cluster where the group name is 'pug-jas983'

    """
    if 'GROUP' in os.environ:
        # Determine if we are on Cheyenne
        if os.environ['GROUP'] == 'ncar':
            on_cheyenne = True
            on_aws = False
            on_magma = False
        # Determine if we are on AWS
        elif os.environ['GROUP'] == 'ec2-user':
            on_cheyenne = False
            on_aws = True
            on_magma = False
        elif os.environ['GROUP'] == 'pug-jas983':
            on_cheyenne = False
            on_aws = False
            on_magma = True
        else:
            on_cheyenne = False
            on_aws = False
            on_magma = False
    else:
        on_cheyenne = False
        on_aws = False
        on_magma = False
    return on_aws, on_cheyenne, on_magma


def read_last_line(file_name):
    """
    Reads the last line of a file.

    :param file_name: string
        Complete path of the file that you would like read.
    :return last_line: string
        Last line of the input file.

    """
    try:
        with open(file_name, mode='r') as infile:
            lines = infile.readlines()
    except IOError:
        last_line = 'IOEror in read_last_line: this file does not exist.'
        return last_line
    try:
        last_line = lines[-1]
    except IndexError:
        last_line = 'IndexError in read_last_line: no last line appears to exist in this file.'
    return last_line


def read_2nd2_last_line(file_name):
    """
    Reads the second to last line of a file.

    :param file_name: string
        Complete path of the file that you would like read.
    :return: second2_last_line: string
        Second to last line of the input file.

    """
    try:
        with open(file_name, mode='r') as infile:
            lines = infile.readlines()
    except IOError:
        second2_last_line = 'IOError in read_2nd2_last_line: this file does not currently exist.'
        return second2_last_line
    try:
        second2_last_line = lines[-2]
    except IndexError:
        second2_last_line = 'IndexError in read_2nd2_last_line: ' \
                            'there do not appear to be at least two lines in this file.'
    return second2_last_line


def read_last_3lines(file_name):
    """
    Reads the last three lines of a file.

    :param file_name: string
        Complete path of the file that you would like print.
    :return: last_3lines: string
        Last three lines of the input file.

    """
    try:
        with open(file_name, mode='r') as infile:
            lines = infile.readlines()
    except IOError:
        last_3lines = 'IOError in print_last_3lines: this file does not currently exist.'
        return last_3lines
    try:
        txt = lines[-4:-1]
        last_3lines = '\n'.join(txt)
    except IndexError:
        last_3lines = 'IndexError in print_last_3lines: there do not appear to be at least three lines in this file.'
        return last_3lines
    return last_3lines


def print_last_3lines(file_name):
    """
    Prints the last three lines of a file.

    :param file_name: string
        Complete path of the file that you would like print.

    """
    try:
        with open(file_name, mode='r') as infile:
            lines = infile.readlines()
    except IOError:
        print('IOError in print_last_3lines: this file does not currently exist.')
        return
    try:
        txt = lines[-4:-1]
        print('\n'.join(txt))
    except IndexError:
        print('IndexError in print_last_3lines: there do not appear to be at least three lines in this file.')
        return


def rda_download(filelist, dspath):
    """
    Logs into the NCAR research data archive (RDA)
    and downloads specified files.

    NOTE: My username/password are currently hard-coded into this function.
    I SHOULD CHAGE THIS!

    :param filelist: list of strings
        List of all the files that you would like downloaded from the RDA.
    :param dspath : string
        Full path to file on the RDA. You can obtain this from
    :return: a boolean (True/False) success flag.

    """
    # Specify login information and url for RDA
    pswd = 'mkjmJ17'
    url = 'https://rda.ucar.edu/cgi-bin/login'
    values = {'email': 'jas983@cornell.edu', 'passwd': pswd, 'action': 'login'}

    # RDA user authentication
    ret = requests.post(url, data=values)
    if ret.status_code != 200:
        print('Bad Authentication for RDA')
        print(ret.text)
        return False

    # Download files from RDA server
    print('Downloading data from RDA...')
    for datafile in filelist:
        filename = dspath + datafile
        file_base = os.path.basename(datafile)
        # print('Downloading', file_base)
        req = requests.get(filename, cookies=ret.cookies, allow_redirects=True, stream=True)
        try:
            filesize = int(req.headers['Content-length'])
        except KeyError as e:
            print(f'KeyError in rda_download: {e}\nCHECK YOUR RDA FILE NAMES!!!')
            return False
        with open(file_base, 'wb') as outfile:
            chunk_size = 1048576
            for chunk in req.iter_content(chunk_size=chunk_size):
                outfile.write(chunk)
        #         if chunk_size < filesize:
        #             check_file_status(file_base, filesize)
        check_file_status(file_base, filesize)
    print('Done downloading data from RDA!')
    return True


def check_file_status(filepath, filesize):
    """
    Checks the file status during a download from the internet.

    This is currently not implemented because I don't
    like the way it prints information to the command line.

    :param filepath: string
        Path to remote data file
    :param filesize : int
        Size of the file as found by req.headers['Content-length']

    """
    sys.stdout.write('\r')
    sys.stdout.flush()
    size = int(os.stat(filepath).st_size)
    percent_complete = (size / filesize) * 100
    sys.stdout.write(f'{filepath}: {percent_complete}%\n')
    sys.stdout.flush()


def gen_daily_sims_csv(param_ids, start='Jan 01 2011', end='Jan 01 2012', csv_name='annual_sims.csv'):

    # Define the file header
    header = ['start_date', 'mp_physics', 'ra_lw_physics', 'ra_sw_physics',
              'sf_surface_physics', 'bl_pbl_physics', 'cu_physics', 'sfclay_physics']
    # Create a list of dates based on the start and end dates provided
    start_date = format_date(start)
    end_date = format_date(end)
    date_list = [start_date + datetime.timedelta(days=x) for x in range(0, (end_date-start_date).days)]
    with open(csv_name, 'w') as csvfile:
        # Write the header to the CSV file
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(header)
        # Write each row to the CSV file
        for date in date_list:
            csv_data = [date.strftime('%b %d %Y'), param_ids[0], param_ids[1], param_ids[2],
                        param_ids[3], param_ids[4], param_ids[5], param_ids[6]]
            csv_writer.writerow(csv_data)
