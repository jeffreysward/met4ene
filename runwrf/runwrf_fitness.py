from datetime import datetime
from os import chdir, getcwd, makedirs, system, path, environ
from shutil import rmtree
from sys import exit
from time import time
import time as tm
import os
import requests
from wrfparams import flexible_generate, write_param_csv
import runwrf as rw


# Set parameters here that should be set automatically eventually
remove_DIR_DATA = False


def wrf_fitness(start_date='Jan 15 2011', end_date='Jan 16 2011', in_yaml='params.yml', generate_params=True,
                bc_data='ERA', MAX_DOMAINS=1, template_dir=None,
                mp=None, lw=None, sw=None, lsm=None, pbl=None, cu=None):

    # Format the forecast start/end and determine the total time.
    forecast_start = datetime.strptime(start_date, '%b %d %Y')
    forecast_end = datetime.strptime(end_date, '%b %d %Y')
    delt = forecast_end - forecast_start
    print('Forecast starting on: {}'.format(forecast_start))
    print('Forecast ending on: {}'.format(forecast_end))

    # Generate a parameter combination of the 6 core parameters if the user has specified this option.
    # Otherwise, use specified input parameters and use defaults for the remaining paramters.
    param_ids, paramstr = flexible_generate(generate_params, mp, lw, sw, lsm, pbl, cu, in_yaml='params.yml')

    # Write parameter combinations to CSV
    # (if you would like to restart this, you must manually delete this CSV)
    write_param_csv(param_ids)

    # Next, get boundary condition data for the simulation
    # ERA is the only supported data type right now.
    vtable_sfx = rw.get_bc_data(paramstr, bc_data, template_dir, forecast_start, delt, remove_DIR_DATA)

    # Setup the working directory to run the simulation
    rw.wrfdir_setup(paramstr, forecast_start, bc_data, template_dir, vtable_sfx)

    # Prepare the namelist
    rw.prepare_namelists(paramstr, param_ids, forecast_start, forecast_end, delt,
                         bc_data, template_dir, MAX_DOMAINS)

    # RUN WPS
    rw.run_wps(paramstr, forecast_start, bc_data, template_dir)

    # RUN REAL
    rw.run_real(paramstr, forecast_start, bc_data, template_dir)

    # RUN WRF
    rw.run_wrf(paramstr, forecast_start, bc_data, template_dir, MAX_DOMAINS)

    # Compute the error between WRF run and ERA5 dataset
    rw.wrf_era5_diff(paramstr, forecast_start, bc_data, template_dir)
