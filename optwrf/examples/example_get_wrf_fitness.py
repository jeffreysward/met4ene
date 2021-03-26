"""
Get WRF Fitness
===============

This example lets you manually determine the fitness for any physics option set on any date
(provided that it's within the ERA5 date range).
"""

import optwrf.optimize_wrf_physics as owp


# Specify desired physics options set below
param_ids = [19, 4, 4, 7, 8, 99]

# Specify the desired start date below
start_date = 'Jul 8 2011'
end_date = 'Jul 9 2011'

# Run get wrf fitness function
fitness, ghi_mean_error, wpd_mean_error, runtime = owp.get_wrf_fitness(param_ids, start_date, end_date,
                                                                       method='wind_only',
                                                                       bc_data='ERA',
                                                                       n_domains=1,
                                                                       disable_timeout=True,
                                                                       verbose=True)
print(f'==========================================================================')
print(f'Physics Options Set: {param_ids}\tStart Date: {start_date}')
print(f'Fitness: {fitness}\tGHI Error: {ghi_mean_error}\tWPD Error: {wpd_mean_error}\tSim Runtime: {runtime}')
