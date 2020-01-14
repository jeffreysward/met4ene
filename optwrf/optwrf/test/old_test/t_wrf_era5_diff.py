import unittest
import wrfga
import datetime
import random
from wrfparams import ids2str, write_param_csv
import runwrf as rw

param_ids = [0, 3, 7, 7, 5, 2, 1]
start_date='Jan 15 2011'
bc_data='ERA'
template_dir=None
forecast_start = datetime.datetime.strptime(start_date, '%b %d %Y')
paramstr = ids2str(param_ids)


fitness = rw.wrf_era5_diff(paramstr, forecast_start, bc_data, template_dir)

