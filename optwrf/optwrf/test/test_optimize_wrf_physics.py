"""
Tests the optimize_wrf_physics functions

"""

from optwrf.optimize_wrf_physics import get_wrf_fitness
from optwrf.runwrf import determine_computer

param_ids = [10, 1, 1, 2, 2, 3, 2]
start_date = 'Jan 01 2011'
end_date = 'Jan 02 2011'
on_aws, on_cheyenne, on_magma = determine_computer()


def test_get_wrf_fitness():
    if [on_aws, on_cheyenne, on_magma].count(True) is 0:
        print('\n!!!Not running test_wrf_era5_diff -- switch to Magma, Cheyenne, or AWS!!!')
        return
    fitness = get_wrf_fitness(param_ids, start_date, end_date)
    assert fitness >= 0