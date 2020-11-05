"""
Test wrfparams functionality

"""

import datetime
import os
import pandas as pd
from optwrf.helper_functions import date2season, daylight_frac, gen_daily_sims_csv

param_ids1 = [19, 4, 4, 7, 8, 99, 1]  # Best params chosen by optwrf
csv_filename1 = '19mp4lw4sw7lsm8pbl99cu_2011_sims.csv'
param_ids2 = [8, 4, 1, 7, 8, 1, 1]  # Second best params chosen by optwrf
csv_filename2 = '8mp4lw1sw7lsm8pbl1cu_2011_sims.csv'
param_ids3 = [13, 4, 4, 7, 8, 99, 1]  # Third best params chosen by optwrf
csv_filename3 = '13mp4lw4sw7lsm8pbl99cu_2011_sims.csv'
param_ids4 = [19, 4, 1, 7, 8, 99, 1]  # Fourth best params chosen by optwrf
csv_filename4 = '19mp4lw1sw7lsm8pbl99cu_2011_sims.csv'
param_ids5 = [19, 4, 3, 7, 8, 1, 1]  # Fifth best params chosen by optwrf
csv_filename5 = '19mp4lw3sw7lsm8pbl1cu_2011_sims.csv'
param_ids_ncar1 = [8, 4, 4, 2, 2, 6, 2]
csv_filename_ncar1 = '8mp4lw4sw2lsm2pbl6cu_2011_sims.csv'
param_ids_ncar2 = [8, 4, 4, 2, 1, 3, 1]
csv_filename_ncar2 = '8mp4lw4sw2lsm1pbl3cu_2011_sims.csv'
param_ids_ncar3 = [4, 4, 2, 2, 2, 1, 2]
csv_filename_ncar3 = '4mp4lw2sw2lsm2pbl1cu_2011_sims.csv'
param_ids_ncar4 = [6, 3, 3, 2, 1, 1, 1]
csv_filename_ncar4 = '6mp3lw3sw1lsm1pbl1cu_2011_sims.csv'


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
               'WRF_Solar_and_Wind/met4ene/optwrf/examples/'
    full_path = csv_path + csv_filename_ncar4
    gen_daily_sims_csv(param_ids_ncar4, start='Jan 01 2011', end='Jan 01 2012', csv_name=full_path)

    assert os.path.exists(csv_path) is True
