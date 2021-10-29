"""
A set of functions that post-process WRF output data for a
variety of applications.


Known Issues/Wishlist:

"""
import netCDF4
import os
import wrf
import xarray as xr
from pvlib.wrfcast import WRF

from optwrf.util import _wrf2xarray

def calc_wpd(wind_speed, air_density=1000):
    """
    Calculates the wind power density per square meter

    :param wind_speed:
    :param air_density:
    :return: wpd
    """

    wpd = 0.5 * air_density * wind_speed ** 3
    return wpd


def process_wrfout_manual(DIR_WRFOUT, wrfout_file, start=None, end=None, save_file=True):
    """
    Processes the wrfout file -- calculates GHI and wind power denity (WPD) and writes these variables
    to wrfout_processed_d01.nc data file to be used by the regridding script (wrf2era_error.ncl) in
    wrf_era5_diff().

    This function makes use of two different packages that are not endogeneous to optwrf. The first is
    pvlib.wrfcast, which is a module for processing WRF output data that I have customized based on the
    pvlib.forecast model. The purpose of this is to eventually be able to use this method to calculate
    PV output from systems installed at any arbitrary location within your WRF model domain (this
    is not yet implemented). I have use this wrfcast module to calculate the GHI from WRF output data
    The second package is the wrf module maintained by NCAR, which reproduces some of the funcionality
    of NCL in Python. I use this to interpolate the wind speed to 100m.

    With the help of these two packages, the remaineder of the function claculates the WPD, formats the
    data to be easily compatible with other functions, and writes the data to a NetCDF file.

    """

    # Absolute path to wrfout data file
    datapath = DIR_WRFOUT + wrfout_file

    # Read in the wrfout file using the netCDF4.Dataset method (I think you can also do this with an xarray method)
    netcdf_data = netCDF4.Dataset(datapath)

    # Create an xarray.Dataset from the wrf qurery_variables.
    query_variables = [
        'T2',
        'CLDFRA',
        'COSZEN',
        'SWDDNI',
        'SWDDIF',
        'height_agl',
        'wspd',
        'wdir',
        'rh',
        'pressure',
        'geopotential',
    ]

    met_data = _wrf2xarray(netcdf_data, query_variables)

    variables = {
        'XLAT': 'XLAT',
        'XLONG': 'XLONG',
        'T2': 'temp_air',
        'CLDFRA': 'cloud_fraction',
        'COSZEN': 'cos_zenith',
        'SWDDNI': 'dni',
        'SWDDIF': 'dhi',
        'height_agl': 'height_agl',
        'wspd': 'wspd',
        'wdir': 'wdir',
        'rh': 'rel_humidity',
        'pressure': 'pressure',
        'geopt': 'geopotential',
    }

    # Rename the variables
    met_data = xr.Dataset.rename(met_data, variables)

    # Convert air temp from kelvin to celsius and calculate global horizontal irradiance
    # using the WRF forecast model methods from pvlib package
    fm = WRF()
    met_data['temp_air'] = fm.kelvin_to_celsius(met_data['temp_air'])
    met_data['ghi'] = fm.dni_and_dhi_to_ghi(met_data['dni'], met_data['dhi'], met_data['cos_zenith'])

    #  Interpolate wind speeds to 100m height
    met_data['wind_speed100'] = wrf.interplevel(met_data['wspd'], met_data['height_agl'], 100)

    # Calculate the wind power density
    met_data['wpd'] = calc_wpd(met_data['wind_speed100'])

    # Drop unnecessary coordinates
    met_data = xr.Dataset.reset_coords(met_data, ['XTIME', 'level'], drop=True)

    # Slice the wrfout data if start and end times ares specified
    if start and end is not None:
        met_data = met_data.sel(Time=slice(start, end))

    # Save the output file if specified.
    if save_file:
        # Write the processed data to a wrfout NetCDF file
        new_filename = DIR_WRFOUT + 'processed_' + wrfout_file
        met_data.to_netcdf(path=new_filename)
    else:
        return met_data
