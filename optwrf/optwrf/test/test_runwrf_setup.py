"""
Tests the runwrf functions

There is no test for run_wps(), run_real(), or run_wrf() because these
programs are all computationally expensive and I don't want them in this
test suite. To test if WPS, REAL, and WRF are running correctly,
I should probably make a separate test, but right now, I have been
using runwrf_fromCL for this purpose.

"""

import os
from optwrf.runwrf import WRFModel
from optwrf.runwrf import determine_computer


param_ids = [10, 1, 1, 2, 2, 3, 2]
start_date = 'Jan 01 2011'
end_date = 'Jan 02 2011'
on_aws, on_cheyenne, on_magma = determine_computer()


# I can't really think of a good way to test determine_computer without having to call the function over and over again
# in subsequesnt tests, so I'm just going to omit it for now.
def test_determine_computer():
    on_aws, on_cheyenne, on_magma = determine_computer()
    print(f'On AWS???: {on_aws}\nOn Cheyenne???: {on_cheyenne}\nOn Magma???: {on_magma}')


def test_WRFModel():
    wrf_sim = WRFModel(param_ids, start_date, end_date)
    assert wrf_sim.DIR_WRF == '/home/jas983/models/wrf/WRF/'
    assert wrf_sim.DIR_WPS_GEOG == '/share/mzhang/jas983/wrf_data/WPS_GEOG/'
    assert wrf_sim.DIR_RUNWRF == '/share/mzhang/jas983/wrf_data/met4ene/optwrf/optwrf/'
    assert wrf_sim.start_date == start_date


def test_get_bc_data():
    if on_magma:
        wrf_sim = WRFModel(param_ids, start_date, end_date)
    else:
        # I use this first one when testing on my local machines.
        print(f'WARNING: this test requires you to manually provide setup_yaml!')
        wrf_sim = WRFModel(param_ids, start_date, end_date, setup_yaml='linux_dirpath.yml')
    vtable_sfx = wrf_sim.get_bc_data()
    assert vtable_sfx == 'ERA-interim.pl'


# The next set of tests will only be useful if you're on a machine with the WRF source code downloaded (i.e., Magma,
# Cheyenne, or AWS). Otherwise, the test will automatically pass. 
def test_wrfdir_setup():
    if [on_aws, on_cheyenne, on_magma].count(True) is 0:
        print('\n!!!Not running test_wrfdir_setup -- switch to Magma, Cheyenne, or AWS.')
        return
    wrf_sim = WRFModel(param_ids, start_date, end_date)
    vtable_sfx = wrf_sim.get_bc_data()
    wrf_sim.wrfdir_setup(vtable_sfx)
    assert os.path.exists(wrf_sim.DIR_RUNWRF + 'wrf2era_error.ncl') == 1


def test_prepare_namelists():
    if [on_aws, on_cheyenne, on_magma].count(True) is 0:
        print('\n!!!Not running test_prepare_namelists -- switch to Magma, Cheyenne, or AWS.')
        return
    wrf_sim = WRFModel(param_ids, start_date, end_date)
    vtable_sfx = wrf_sim.get_bc_data()
    wrf_sim.wrfdir_setup(vtable_sfx)
    wrf_sim.prepare_namelists()
    assert 0 == 0


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


