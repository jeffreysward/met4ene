import pytest
from runwrf import WRFModel
from runwrf import determine_computer


param_ids = [10, 1, 1, 2, 2, 3, 2]
start_date = 'Jan 15 2011'
end_date = 'Jan 16 2011'


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
    wrf_sim = WRFModel(param_ids, start_date, end_date, setup_yaml='mac_dirpath.yml')
    vtable_sfx = wrf_sim.get_bc_data()
    assert vtable_sfx == 'ERA-interim.pl'
