# Built-in python modules
import os
import inspect
# Scientific python add-ons
import numpy as np
import pandas as pd
# Plotting packages
import matplotlib.pyplot as plt
import matplotlib as mpl
# Finally, import the pvlib library
import pvlib


# LOAD TMY DATA
# Find the absolute file path to your pvlib installation
pvlib_abspath = os.path.dirname(os.path.abspath(inspect.getfile(pvlib)))

# absolute path to a data file
datapath = os.path.join(pvlib_abspath, 'data', '703165TY.csv')

# read tmy data with year values coerced to a single year
tmy_data, meta = pvlib.iotools.tmy.read_tmy3(datapath, coerce_year=2015)
tmy_data.index.name = 'Time'

# TMY data seems to be given as hourly data with time stamp at the end
# shift the index 30 Minutes back for calculation of sun positions
tmy_data = tmy_data.shift(freq='-30Min')['2015']


# CALCULATE MODEL INTERMEDIATES
surface_tilt = 30
surface_azimuth = 180 # pvlib uses 0=North, 90=East, 180=South, 270=West convention
albedo = 0.2
# Create pvlib Location() object based on TMY meta data
sand_point = pvlib.location.Location(meta['latitude'], meta['longitude'], tz='US/Alaska',
                                     altitude=meta['altitude'], name=meta['Name'].replace('"',''))
# Solar position
solpos = pvlib.solarposition.get_solarposition(tmy_data.index, sand_point.latitude, sand_point.longitude)
# The extraradiation function returns a simple numpy array
# instead of a nice pandas series.
dni_extra = pvlib.irradiance.get_extra_radiation(tmy_data.index)
dni_extra = pd.Series(dni_extra, index=tmy_data.index)
# Airmass
airmass = pvlib.atmosphere.get_relative_airmass(solpos['apparent_zenith'])
# POA sky diffuse
poa_sky_diffuse = pvlib.irradiance.haydavies(surface_tilt, surface_azimuth,
                                             tmy_data['DHI'], tmy_data['DNI'], dni_extra,
                                             solpos['apparent_zenith'], solpos['azimuth'])
# POA ground diffuse
poa_ground_diffuse = pvlib.irradiance.get_ground_diffuse(surface_tilt, tmy_data['GHI'], albedo=albedo)
# AOI
aoi = pvlib.irradiance.aoi(surface_tilt, surface_azimuth, solpos['apparent_zenith'], solpos['azimuth'])
# POA total irradiance
poa_irrad = pvlib.irradiance.poa_components(aoi, tmy_data['DNI'], poa_sky_diffuse, poa_ground_diffuse)
# Cell and module temperature
params = pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS['sapm']['open_rack_glass_glass']
pvtemps = pvlib.temperature.sapm_cell(poa_irrad['poa_global'], tmy_data['DryBulb'], tmy_data['Wspd'], **params)


# CALCULATE DC POWER OUTPUT USING SAPM
# Get module data
sandia_modules = pvlib.pvsystem.retrieve_sam(name='SandiaMod')
sandia_module = sandia_modules.Canadian_Solar_CS5P_220M___2009_
# Calculate the effective irradiance
effective_irradiance = pvlib.pvsystem.sapm_effective_irradiance(poa_irrad.poa_direct, poa_irrad.poa_diffuse, airmass, aoi, sandia_module)
# Run SAPM
sapm_out = pvlib.pvsystem.sapm(effective_irradiance, pvtemps, sandia_module)
# sapm_out[['p_mp']].plot()
# plt.ylabel('DC Power (W)')
# plt.show()