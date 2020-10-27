"""
A set of functions that post-process WRF output data for a
variety of applications.


Known Issues/Wishlist:

"""
import netCDF4
import wrf
import xarray as xr
from pvlib.wrfcast import WRF


def process_wrfout_data_manual(DIR_WRFOUT, wrfout_file, save_file=True):
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
        'U10',
        'V10',
        'CLDFRA',
        'COSZEN',
        'SWDDNI',
        'SWDDIF'
    ]

    first = True
    for key in query_variables:
        var = wrf.getvar(netcdf_data, key, timeidx=wrf.ALL_TIMES)
        if first:
            met_data = var
            first = False
        else:
            met_data = xr.merge([met_data, var])

    variables = {
        'times': 'Times',
        'XLAT': 'lat',
        'XLONG': 'lon',
        'T2': 'temp_air',
        'U10': 'wind_speed_u',
        'V10': 'wind_speed_v',
        'CLDFRA': 'cloud_fraction',
        'COSZEN': 'cos_zenith',
        'SWDDNI': 'dni',
        'SWDDIF': 'dhi'
    }

    met_data = xr.Dataset.rename(met_data, variables)
    met_data = xr.Dataset.reset_coords(met_data, ['XTIME'], drop=True)
    # met_data = xr.Dataset.set_coords(met_data, ['Times'])
    # met_data = xr.Dataset.reset_coords(met_data, ['Times'], drop=True)

    # Process the data using the WRF forecast model methods from pvlib package
    fm = WRF()
    # met_data = fm.process_data(met_data)
    wind_speed10 = fm.uv_to_speed(met_data)
    temp_air = fm.kelvin_to_celsius(met_data['temp_air'])
    ghi = fm.dni_and_dhi_to_ghi(met_data['dni'], met_data['dhi'], met_data['cos_zenith'])

    # Process the data using the wrf-python package
    height = wrf.getvar(netcdf_data, "height_agl", wrf.ALL_TIMES, units='m')
    wspd = wrf.getvar(netcdf_data, 'wspd_wdir', wrf.ALL_TIMES, units='m s-1')[0, :]

    #  Interpolate wind speeds to 100m height
    wind_speed100 = wrf.interplevel(wspd, height, 100)

    # Calculate wind power per square meter
    air_density = 1000
    wpd = 0.5 * air_density * wind_speed100 ** 3

    met_data['ghi'] = ghi
    met_data['wind_speed10'] = wind_speed10
    met_data['wind_speed100'] = wind_speed100
    met_data['wpd'] = wpd
    met_data['temp_air'] = temp_air

    # Fix a bug in how wrfout data is read in -- attributes must be strings to be written to NetCDF
    for var in met_data.data_vars:
        try:
            met_data[var].attrs['projection'] = str(met_data[var].attrs['projection'])
        except KeyError:
            pass

    # Fix another bug that creates a conflict in the 'coordinates' attribute
    for var in met_data.data_vars:
        try:
            del met_data[var].attrs['coordinates']
        except KeyError:
            pass

    # Slice the last time from the wrfout data to remove duplicates
    met_data = met_data.isel(Time=slice(0, -1))

    if save_file:
        # Write the processed data to a wrfout NetCDF file
        new_filename = DIR_WRFOUT + 'wrfout_processed_d01.nc'
        met_data.to_netcdf(path=new_filename)
    else:
        return met_data