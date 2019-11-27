import pandas as pd
from pvlib import pvsystem
from pvlib.pvsystem import PVSystem


# Set the module parameters
module_parameters = {'pdc0': 1500, 'gamma_pdc': -0.004}
system = PVSystem(module_parameters=module_parameters)
print(system.module_parameters)

# Change the reference temperature
system.module_parameters['temp_ref'] = 0
pdc = system.pvwatts_dc(1000, 30)
print(f'The DC power output is {pdc} kW.')

# 20 deg tilt, south-facing
system = PVSystem(surface_tilt=40, surface_azimuth=180)
print(f'The system has a {system.surface_tilt} '
      f'degree tilt angle and a {system.surface_azimuth} degree azimuth angle')

