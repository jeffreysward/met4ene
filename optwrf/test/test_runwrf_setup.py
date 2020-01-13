import pytest
import os
from optwrf.runwrf import WRFModel
from optwrf.runwrf import determine_computer


param_ids = [10, 1, 1, 2, 2, 3, 2]
start_date = 'Jan 15 2011'
end_date = 'Jan 16 2011'
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
    assert wrf_sim.DIR_RUNWRF == '/share/mzhang/jas983/wrf_data/met4ene/runwrf/'
    assert wrf_sim.start_date == start_date


def test_get_bc_data():
    # I use this first one when testing on my local machines.
    # wrf_sim = WRFModel(param_ids, start_date, end_date, setup_yaml='linux_dirpath.yml')
    # I use this second one when testing on Magma.
    wrf_sim = WRFModel(param_ids, start_date, end_date)
    vtable_sfx = wrf_sim.get_bc_data()
    assert vtable_sfx == 'ERA-interim.pl'


# The next set of tests will only be useful if you're on a machine with the WRF source code downloaded (i.e., Magma,
# Cheyenne, or AWS). Otherwise, the test will automatically pass. 
def test_wrfdir_setup():
    if not [on_aws, on_cheyenne, on_magma]:
        print('\n!!!Not running test_wrfdir_setup -- switch to Magma, Cheyenne, or AWS.')
        return
    wrf_sim = WRFModel(param_ids, start_date, end_date)
    vtable_sfx = wrf_sim.get_bc_data()
    wrf_sim.wrfdir_setup(vtable_sfx)
    assert os.path.exists(wrf_sim.DIR_RUNWRF + 'wrf2era_error.ncl') == 1


def test_prepare_namelists():
    if not [on_aws, on_cheyenne, on_magma]:
        print('\n!!!Not running test_prepare_namelists -- switch to Magma, Cheyenne, or AWS.')
        return
    wrf_sim = WRFModel(param_ids, start_date, end_date)
    vtable_sfx = wrf_sim.get_bc_data()
    wrf_sim.wrfdir_setup(vtable_sfx)
    wrf_sim.prepare_namelists()
    assert 0 == 0
