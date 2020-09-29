"""
Process ERA5 Data
=================

This example lets you manually process the ERA5 data. I created this because
restarting OptWRF is difficult (high-memory) unless all files have been created previously.
"""

from optwrf.runwrf import WRFModel


# Specify desired physics options set below
param_ids = [8, 7, 3, 1, 1, 10, 1]

# Specify the desired start date below
start_date = 'Dec 11  2011'
end_date = 'Dec 12 2011'

# Run get wrf fitness function
wrf_sim = WRFModel(param_ids, start_date, end_date, verbose=True)
wrf_sim.process_era5_data()
