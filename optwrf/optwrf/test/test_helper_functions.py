"""
Test wrfparams functionality

"""

import datetime
import pandas as pd
from optwrf.helper_functions import date2season


def test_date2season():
    season = date2season(pd.Timestamp(datetime.datetime.now()))
    print(f'Whatever it looks like outside... It is {season[0]}!')
    assert type(season[0]) is str
