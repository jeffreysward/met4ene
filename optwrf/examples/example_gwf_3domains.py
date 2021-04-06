"""
Get WRF Fitness
===============

This example lets you manually determine the fitness for any physics option set on any date
(provided that it's within the ERA5 date range).
"""

import optwrf.optimize_wrf_physics as owp


# Specify desired physics options set below
param_ids = [28, 4, 4, 2, 5, 1]

# Specify the desired start date below
start_date = 'Jul 10 2011'
end_date = 'Jul 11 2011'

# Run get wrf fitness function
fitness, ghi_mean_error, wpd_mean_error, runtime = owp.get_wrf_fitness(param_ids, start_date, end_date,
                                                                       method='wind_only',
                                                                       bc_data='ERA5',
                                                                       n_domains=3,
                                                                       wfp=True,
                                                                       disable_timeout=True,
                                                                       verbose=True)
print(f'==========================================================================')
print(f'Physics Options Set: {param_ids}\tStart Date: {start_date}')
print(f'Fitness: {fitness}\tGHI Error: {ghi_mean_error}\tWPD Error: {wpd_mean_error}\tSim Runtime: {runtime}')
