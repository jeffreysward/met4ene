"""
Tests the runwrf functions after WRF has been run

There is no test for run_wps(), run_real(), or run_wrf() because these
programs are all computationally expensive and I don't want them in this
test suite. To test if WPS, REAL, and WRF are running correctly,
I should probably make a separate test, but right now, I have been
using runwrf_fromCL.py for this purpose.

"""

import os
from optwrf.runwrf import WRFModel
from optwrf.runwrf import determine_computer


param_ids = [10, 1, 1, 2, 2, 3, 2]
start_date = 'Jan 15 2011'
end_date = 'Jan 16 2011'
on_aws, on_cheyenne, on_magma = determine_computer()


def test_process_wrfout_data():
    wrf_sim = WRFModel(param_ids, start_date, end_date)
    wrfout_file = wrf_sim.DIR_WRFOUT + 'wrfout_d01.nc'
    if not os.path.exists(wrfout_file):
        print(f'\nYour have an incorrect wrfout file path:\n{wrfout_file}.')
        raise FileNotFoundError
    wrf_sim.process_wrfout_data()
    processed_wrfout_file = wrf_sim.DIR_WRFOUT + 'wrfout_processed_d01.nc'
    assert os.path.exists(processed_wrfout_file) == 1


def test_process_era5_data():
    if [on_aws, on_cheyenne, on_magma].count(True) is 0:
        print('\n!!!Not running test_process_era5_data -- switch to Magma, Cheyenne, or AWS.')
        return
    wrf_sim = WRFModel(param_ids, start_date, end_date)
    wrf_sim.process_era5_data()
    ERA5_ROOT = '/share/mzhang/jas983/wrf_data/data/ERA5/'
    processed_era_file = ERA5_ROOT + 'ERA5_EastUS_WPD-GHI_' \
                         + wrf_sim.forecast_start.strftime('%Y') + '-' \
                         + wrf_sim.forecast_start.strftime('%m') + '.nc'
    assert os.path.exists(processed_era_file) == 1


def test_wrf_era5_diff():
    if [on_aws, on_cheyenne, on_magma].count(True) is 0:
        print('\n!!!Not running test_wrf_era5_diff -- switch to Magma, Cheyenne, or AWS.')
        return
    wrf_sim = WRFModel(param_ids, start_date, end_date)
    processed_wrfout_file = wrf_sim.DIR_WRFOUT + 'wrfout_processed_d01.nc'
    ERA5_ROOT = '/share/mzhang/jas983/wrf_data/data/ERA5/'
    processed_era_file = ERA5_ROOT + 'ERA5_EastUS_WPD-GHI_' \
                         + wrf_sim.forecast_start.strftime('%Y') + '-' \
                         + wrf_sim.forecast_start.strftime('%m') + '.nc'

    if not os.path.exists(processed_wrfout_file):
        wrf_sim.process_wrfout_data()
    if not os.path.exists(processed_era_file):
        wrf_sim.process_era5_data()
    total_error = wrf_sim.wrf_era5_diff()
    assert total_error >= 0
