"""
This example walks through the calculation of the fitness function correction factor (alpha).
To get this value, I find the population mean in GHI and wind power density using
WRF simulations data from the year 2011. These simulations were run in 1-month intervals,
so there is a sample mean for each month.

Last updated by Jeff Sward 02/19/2020

"""

from optwrf.runwrf import WRFModel
import os
import sys

# Define the parameters and start/end dates for the 'default' simulation
param_ids = [10, 1, 1, 2, 2, 3, 2]
start_dates = ['Dec 1 2011']
end_dates = ['Jan 1 2012']

# Postprocess all the wrfout files if necessary
print('Starting wrfout file processing...')
for start_date, end_date in zip(start_dates, end_dates):
    wrf_sim = WRFModel(param_ids, start_date, end_date)
    processed_wrfout_file = wrf_sim.DIR_WRFOUT + 'wrfout_processed_d01.nc'
    if not os.path.exists(processed_wrfout_file):
        wrfout_file = wrf_sim.DIR_WRFOUT + 'wrfout_d01.nc'
        if not os.path.exists(wrfout_file):
            print(f'\nYour have an incorrect wrfout file path:\n{wrfout_file}.')
            raise FileNotFoundError
        wrf_sim.process_wrfout_data()
    sys.stdout.flush()
print('!Done!')

# Process all the ERA5 data if necessary
print('Starting ERA5 file processing...')
for start_date, end_date in zip(start_dates, end_dates):
    wrf_sim = WRFModel(param_ids, start_date, end_date)
    ERA5_ROOT = '/share/mzhang/jas983/wrf_data/data/ERA5/'
    processed_era_file = ERA5_ROOT + 'ERA5_EastUS_WPD-GHI_' \
                         + wrf_sim.forecast_start.strftime('%Y') + '-' \
                         + wrf_sim.forecast_start.strftime('%m') + '.nc'
    if not os.path.exists(processed_era_file):
        wrf_sim.process_era5_data()
    sys.stdout.flush()
print('!Done!')

# Calculate the monthly MAE for both GHI and WPD
mean_ghi = []
mean_wpd = []
print('Calculating difference between WRF and ERA5...')
for start_date, end_date in zip(start_dates, end_dates):
    wrf_sim = WRFModel(param_ids, start_date, end_date)
    mae = wrf_sim.wrf_era5_diff()
    mean_ghi.append(mae[1])
    mean_wpd.append(mae[2])
    sys.stdout.flush()
print('!Done!')

# Calculate the annual mean MAE for both GHI and WPD
pmean_ghi = 0
pmean_wpd = 0
print('Calulating the annual means...')
for start_date, end_date, ghi, wpd in zip(start_dates, end_dates, mean_ghi, mean_wpd):
    wrf_sim = WRFModel(param_ids, start_date, end_date)
    n_days = (wrf_sim.forecast_end - wrf_sim.forecast_start).days
    n_hours = 24 * n_days
    print(f'Month {wrf_sim.forecast_start.month} has {n_days} days and {n_hours} hours.')
    print(f'The GHI is {ghi}, and the WPD is {wpd}\n')
    pmean_ghi = pmean_ghi + n_hours / 8760 * ghi
    pmean_wpd = pmean_wpd + n_hours / 8760 * wpd
    sys.stdout.flush()
print('!Done!')
print(f'The annual mean GHI error is: {pmean_ghi} kW m-2')
print(f'The annual mean WPD error is: {pmean_wpd} kW m-2')

# Calculate the correction factor
alpha = pmean_ghi / pmean_wpd
print(f'The fitness function correction factor is {alpha}.')
