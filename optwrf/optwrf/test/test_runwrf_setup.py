"""
Tests the runwrf functions before WRF has been run

There is no test for optwrf.runwrf.run_real() or optwrf.runwrf.run_wrf() because
these programs are all computationally expensive, and I don't want them in this
test suite. To test if REAL and WRF are running correctly,
I should probably make a separate test, but right now, I have been
using runwrf_fromCL.py for this purpose.

I can't really think of a good way to test determine_computer without having
to call the function over and over again in subsequent tests,
so I'm just going to omit it for now.

Some of the tests will only be useful if you're on a machine with the WRF
source code downloaded (i.e., Magma, Cheyenne, or AWS). Otherwise, the test
will automatically pass.

"""

import os

from optwrf.runwrf import WRFModel
from optwrf.runwrf import determine_computer
import optwrf.helper_functions as hf

param_ids = [10, 1, 1, 2, 2, 3, 2]
start_date = 'Dec 31, 2011'
end_date = 'Jan 1, 2012'
on_aws, on_cheyenne, on_magma = determine_computer()


def test_format_date():
    """Checks the function that ensures consistency in the input date format."""
    date = hf.format_date(start_date)
    print(f'Starting forecast at {date}')
    assert date is not None


def test_WRFModel():
    """Checks that the WRFModel method works correctly. The assert statements assume
    that you are using dirpth.yml not one made for a local machine. Should probably
    change this at some point..."""
    wrf_sim = WRFModel(param_ids, start_date, end_date)
    assert wrf_sim.DIR_WRF == '/home/jas983/models/wrf/WRF/'
    assert wrf_sim.DIR_WPS_GEOG == '/share/mzhang/jas983/wrf_data/WPS_GEOG/'
    assert wrf_sim.DIR_RUNWRF == '/share/mzhang/jas983/wrf_data/met4ene/optwrf/optwrf/'
    assert wrf_sim.start_date == start_date


def test_get_bc_data(setup_yaml='mac_dirpath.yml'):
    """Checks if WRF boundary condition data can be downloaded from the RDA.
    This definitely works best if done on Magma using setup_yaml='dirpath.yml',
    but if you do want to run it on your local machine make sure that you change
    setup_yaml='local_dirpath.yml', where local_dirpath.yml is a yaml file where
    you specify root directory paths. Note: this test only works on linux."""
    if on_magma:
        wrf_sim = WRFModel(param_ids, start_date, end_date)
    else:
        print(f'WARNING: this test requires you to manually provide setup_yaml!\n'
              f'You have specified {setup_yaml}.')
        wrf_sim = WRFModel(param_ids, start_date, end_date, setup_yaml=setup_yaml)
    vtable_sfx = wrf_sim.get_bc_data()
    print(f'The following data files are in {wrf_sim.DIR_DATA_TMP}:\n')
    [print(name) for name in os.listdir(wrf_sim.DIR_DATA_TMP)]
    assert vtable_sfx == 'ERA-interim.pl'
    assert len([name for name in os.listdir(wrf_sim.DIR_DATA_TMP)]) > 0


def test_wrfdir_setup():
    """If on AWS, Cheyenne, or Magma, tests that the WRF directory can be setup correclty."""
    if [on_aws, on_cheyenne, on_magma].count(True) is 0:
        print('\n!!!Not running test_wrfdir_setup -- switch to Magma, Cheyenne, or AWS.')
        return
    wrf_sim = WRFModel(param_ids, start_date, end_date)
    vtable_sfx = wrf_sim.get_bc_data()
    wrf_sim.wrfdir_setup(vtable_sfx)
    assert os.path.exists(wrf_sim.DIR_RUNWRF + 'wrf2era_error.ncl') == 1


def test_prepare_namelists():
    """If on AWS, Cheyenne, or Magma, tests that the template namelists can be edited
    to reflect the desired configuration for the current WRF model run."""
    if [on_aws, on_cheyenne, on_magma].count(True) is 0:
        print('\n!!!Not running test_prepare_namelists -- switch to Magma, Cheyenne, or AWS.')
        return
    wrf_sim = WRFModel(param_ids, start_date, end_date)
    vtable_sfx = wrf_sim.get_bc_data()
    wrf_sim.wrfdir_setup(vtable_sfx)
    wrf_sim.prepare_namelists()
    assert 0 == 0


def test_run_wps():
    """If on AWS, Cheyenne, or Magma, tests that WPS runs successfully."""
    if [on_aws, on_cheyenne, on_magma].count(True) is 0:
        print('\n!!!Not running test_run_wps -- switch to Magma, Cheyenne, or AWS.')
        return
    wrf_sim = WRFModel(param_ids, start_date, end_date)
    vtable_sfx = wrf_sim.get_bc_data()
    wrf_sim.wrfdir_setup(vtable_sfx)
    wrf_sim.prepare_namelists()
    success = wrf_sim.run_wps()
    lastmetfile = f'met_em.d{str(wrf_sim.n_domains).zfill(2)}.{wrf_sim.forecast_end.strftime("%Y-%m-%d")}_00:00:00.nc'
    assert success is True
    assert os.path.exists(wrf_sim.DIR_WRFOUT + lastmetfile)
