import pytest
from runwrf import WRFModel
from runwrf import determine_computer


def test_determine_computer():
    on_aws, on_cheyenne, on_magma = determine_computer()
    print(f'On AWS???: {on_aws}\nOn Cheyenne???: {on_cheyenne}\nOn Magma???: {on_magma}')


def test_WRFModel():
    param_ids = [10, 1, 1, 2, 2, 3, 2]
    start_date = 'Jan 15 2011'
    end_date = 'Jan 16 2011'
    wrf_sim = WRFModel(param_ids, start_date, end_date)
    assert wrf_sim.end_date == end_date
