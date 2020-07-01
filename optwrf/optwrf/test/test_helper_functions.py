"""
Test wrfparams functionality

"""

import datetime
import pandas as pd
from optwrf.helper_functions import date2season, daylight_frac


def test_date2season():
    season = date2season(pd.Timestamp(datetime.datetime.now()))
    print(f'Whatever it looks like outside... It is {season}!')
    assert type(season) is str


def test_daylight_frac():
    frac = daylight_frac('Jul 1, 2020')
    print(f'The daylight fraction is: {frac}')
    assert 0 <= frac <= 1
