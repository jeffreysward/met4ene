from datetime import datetime
from wrfparams import ids2str, write_param_csv
import runwrf as rw


def get_wrf_fitness(param_ids, start_date='Jan 15 2011', end_date='Jan 16 2011',
                    bc_data='ERA', MAX_DOMAINS=1, template_dir=None):

    # Format the forecast start/end and determine the total time.
    forecast_start = datetime.strptime(start_date, '%b %d %Y')
    forecast_end = datetime.strptime(end_date, '%b %d %Y')
    delt = forecast_end - forecast_start
    print('Forecast starting on: {}'.format(forecast_start))
    print('Forecast ending on: {}'.format(forecast_end))
    paramstr = ids2str(param_ids)

    # Next, get boundary condition data for the simulation
    # ERA is the only supported data type right now.
    vtable_sfx = rw.get_bc_data(paramstr, bc_data, template_dir, forecast_start, delt)

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

    # Compute the error between WRF run and ERA5 dataset and return fitness
    fitness = rw.wrf_era5_diff(paramstr, forecast_start, bc_data, template_dir)

    # Write parameter combinations to CSV
    # (if you would like to restart this, you must manually delete this CSV)
    write_param_csv(param_ids, fitness)
    return fitness
