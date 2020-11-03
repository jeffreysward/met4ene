"""
Test wrfparams functionality

"""

import datetime
import os
import pandas as pd
from optwrf.helper_functions import date2season, daylight_frac, gen_daily_sims_csv

param_ids = [19, 4, 4, 7, 8, 99, 1]


def test_date2season():
    season = date2season(pd.Timestamp(datetime.datetime.now()))
    print(f'Whatever it looks like outside... It is {season}!')
    assert type(season) is str


def test_daylight_frac():
    frac = daylight_frac('Jul 1, 2020')
    print(f'The daylight fraction is: {frac}')
    assert 0 <= frac <= 1


def test_gen_daily_sims_csv():
    csv_path = '/Users/swardy9230/Box Sync/01_Research/01_Renewable_Analysis/' \
               'WRF_Solar_and_Wind/met4ene/optwrf/examples/19mp4lw4sw7lsm8pbl99cu_2011_sims.csv'
    gen_daily_sims_csv(param_ids, start='Jan 01 2011', end='Jan 01 2012', csv_name=csv_path)

    assert os.path.exists(csv_path) is True
