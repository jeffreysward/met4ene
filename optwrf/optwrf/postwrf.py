"""
A set of functions that post-process WRF output data for a
variety of applications.


Known Issues/Wishlist:

"""
import netCDF4
import wrf
import xarray as xr
from pvlib.wrfcast import WRF


def get_wspd_wdir(netcdf_data, key):
    """
    Formats the wind speed and wind direction so it can be merged into
    an xarray Dataset with all the other variables extracted using getvar
    :param netcdf_data:
    :param key:
    :return:
    """
    var = wrf.getvar(netcdf_data, key, wrf.ALL_TIMES)
    var = xr.DataArray.reset_coords(var, ['wspd_wdir'], drop=True)
    var.name = key
    return var


def _wrf2xarray(netcdf_data, query_variables):
    """
    Gets data from the netcdf wrfout file and uses wrf-python
    to create an xarray Dataset.

    Parameters
    ----------
    data: netcdf
        Data returned from UNIDATA NCSS query, or from your local forecast.
    query_variables: list
        The variables requested.
    start: Timestamp
        The start time
    end: Timestamp
        The end time

    Returns
    -------
    xarray.Dataset
    """
    first = True
    for key in query_variables:
        if key in ['wspd', 'wdir']:
            var = get_wspd_wdir(netcdf_data, key)
        else:
            var = wrf.getvar(netcdf_data, key, timeidx=wrf.ALL_TIMES)
        if first:
            data = var
            first = False
        else:
            with xr.set_options(keep_attrs=True):
                try:
                    data = xr.merge([data, var])
                except ValueError:
                    data = data.drop_vars('Time')
                    data = xr.merge([data, var])

    # Get global attributes from the NetCDF Dataset
    wrfattrs_names = netcdf_data.ncattrs()
    wrfattrs = wrf.extract_global_attrs(netcdf_data, wrfattrs_names)
    data = data.assign_attrs(wrfattrs)

    # Fix a bug in how wrfout data is read in -- attributes must be strings to be written to NetCDF
    for var in data.data_vars:
        try:
            data[var].attrs['projection'] = str(data[var].attrs['projection'])
        except KeyError:
            pass

    # Fix another bug that creates a conflict in the 'coordinates' attribute
    for var in data.data_vars:
        try:
            del data[var].attrs['coordinates']
        except KeyError:
            pass

    return data


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

    This method makes use of two different packages that are not endogeneous to optwrf. The first is
    pvlib.wrfcast, which is a module for processing WRF output data that I have customized based on the
    pvlib.forecast model. The purpose of this is to eventually be able to use this method to calculate
    PV output from systems installed at any arbitrary location within your WRF model domain (this
    is not yet implemented). I have use this wrfcast module to calculate the GHI from WRF output data
    The second package is the wrf module maintained by NCAR, which reproduces some of the funcionality
    of NCL in Python. I use this to interpolate the wind speed to 100m.

    With the help of these two packages, the remaineder of the methods claculates the WPD, formats the
    data to be easily compatible with other methods, and writes the data to a NetCDF file.

    """

    # Absolute path to wrfout data file
    datapath = DIR_WRFOUT + wrfout_file

    # Read in the wrfout file using the netCDF4.Dataset method (I think you can also do this with an xarray method)
    netcdf_data = netCDF4.Dataset(datapath)

    # Create an xarray.Dataset from the wrf qurery_variables.
    query_variables = [
        'times',
        'T2',
        'CLDFRA',
        'COSZEN',
        'SWDDNI',
        'SWDDIF',
        'height_agl',
        'wspd',
        'wdir',
    ]

    met_data = _wrf2xarray(netcdf_data, query_variables)

    variables = {
        'times': 'Times',
        'XLAT': 'lat',
        'XLONG': 'lon',
        'T2': 'temp_air',
        'CLDFRA': 'cloud_fraction',
        'COSZEN': 'cos_zenith',
        'SWDDNI': 'dni',
        'SWDDIF': 'dhi',
        'height_agl': 'height_agl',
        'wspd': 'wspd',
        'wdir': 'wdir',
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
        new_filename = DIR_WRFOUT + 'wrfout_processed_d01.nc'
        met_data.to_netcdf(path=new_filename)
    else:
        return met_data
