"""
This example walks through the calculation of the fitness function correction factor (alpha).
To get this value, I find the population mean in GHI and wind power density using
WRF simulations data from the year 2011. These simulations were run in 1-month intervals,
so there is a sample mean for each month.

Last updated by Jeff Sward 02/19/2020

"""

from optwrf.runwrf import WRFModel
import optwrf.helper_functions as hf
import os
import sys

# Define the parameters and start/end dates for the 'default' simulation
param_ids = [10, 1, 1, 2, 2, 3, 2]
start_dates = ['Jan 1 2011', 'Feb 1 2011', 'Mar 1 2011', 'Apr 1 2011',
               'May 1 2011', 'Jun 1 2011', 'Jul 1 2011', 'Aug 1 2011',
               'Sep 1 2011', 'Oct 1 2011', 'Nov 1 2011', 'Dec 1 2011']
end_dates = ['Feb 1 2011', 'Mar 1 2011', 'Apr 1 2011', 'May 1 2011',
             'Jun 1 2011', 'Jul 1 2011', 'Aug 1 2011', 'Sep 1 2011',
             'Oct 1 2011', 'Nov 1 2011', 'Dec 1 2011', 'Jan 1 2012']

# Postprocess all the wrfout files if necessary
print('Starting wrfout file processing...')
for start_date, end_date in zip(start_dates, end_dates):
    wrf_sim = WRFModel(param_ids, start_date, end_date)
    processed_wrfout_file = wrf_sim.DIR_WRFOUT + 'default_all_2011/wrfout_processed_d01.nc'
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

# Calculate the monthly error for both GHI and WPD.
# This is the total error summed across all grid cells and across all hours of the month
total_monthly_ghi_error = []
total_monthly_wpd_error = []
print('Calculating difference between WRF and ERA5...')
for start_date, end_date in zip(start_dates, end_dates):
    wrf_sim = WRFModel(param_ids, start_date, end_date)
    error = wrf_sim.wrf_era5_diff()
    total_monthly_ghi_error.append(error[1])
    total_monthly_wpd_error.append(error[2])
    sys.stdout.flush()
print('!Done!')

# Calculate the annual daily mean error for both GHI and WPD
print('Calulating the annual means...')
total_annual_ghi_error = sum(total_monthly_ghi_error)
daily_mean_ghi_error = total_annual_ghi_error / 365
total_annual_wpd_error = sum(total_monthly_wpd_error)
daily_mean_wpd_error = total_annual_wpd_error / 365
print(f'The annual daily mean GHI error is: {daily_mean_ghi_error} kW m-2')
print(f'The annual daily mean WPD error is: {daily_mean_wpd_error} kW m-2')

# Calculate the annual mean daylight fraction
daylight_factors = []
for jday in range(1, 366):
    daylight_factors.append(hf.daylight_frac(jday))
mean_daylight_factor = sum(daylight_factors) / len(daylight_factors)

# Calculate the correction factor
alpha = (daily_mean_ghi_error / mean_daylight_factor) / daily_mean_wpd_error
print(f'The fitness function correction factor is {alpha}.')
