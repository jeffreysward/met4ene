"""
A set of functions that accomplish WRF regridding or error calculation
using different methods.


Known Issues/Wishlist:

"""
import os
import time

import numpy as np
import pyresample as prs
import scipy
import xarray as xr
import xesmf as xe

from optwrf.helper_functions import read_last_3lines, print_last_3lines, read_last_line


def wrf_era5_regrid_ncl(in_yr, in_mo, in_da, paramstr, wrfdir='./', eradir='/share/mzhang/jas983/wrf_data/data/ERA5/',
                        recalculate=False):
    """
    CONSIDER MOVING THIS WITHIN THE WRFModel METHOD?

    Converts (regrids) the WRF grid to the ERA5 grid and calculates the total absolute error
    between the global horizonal irradiance (GHI) and wind power density (WPD) in kW -m -2.

    This function is really just a python wrapper for the NCL script i.e., this function calls
    the NCL script wrf2era_error.ncl which calculates the errors in GHI and WPD using conservative
    regridding and then writes these values to a CSV file read by this script.

    This obviously not the most elegant solution to this problem, but the sad reality is that,
    currently, no python packages exist that interface well with esmpy in a HPC environment.
    The promising new packages is xESMF, but it doesn't work with python's concurrent.futures
    module currently (see wrf_era5_regrid_xesmf).

    :param in_yr: string
        defining the year that's passed to NCL in the form YYYY / %Y (e.g., 2010, 2011, 2012, ...).
    :param in_mo: string
        defining the month that's passed to NCL in the form MM / %m (e.g., 01, 02, 03, ..., 12).
    :param in_da: string
        defining the day that's passed to NCL in the form DD / %d (e.g., 01, 02, 03, ..., 31).
    :param paramstr: string
        containing the six major physics parameterization ids to aid with naming convention.
        Same as WRFModel.paramstr.
    :param wrfdir: string
        defining the location of the wrfout directory. Same as WRFModel.DIR_WRFOUT.
    :param eradir: string
        defining the location of the ERA5 data directory.
    :param recalculate: boolean (True/False)
        controling if the regridding function should be perfomed anew if the error_file already exists.
    :return error: list
        Sum of the absolute error in GHI (index=1) and WPD (index=2) accumulated in each grid cell
        during all time periods in the WRF simulation. The zeroth index is a placeholder.

    """
    # Check to see if the regridding function has been run before
    error_file = wrfdir + 'mae_wrfyera_' + paramstr + '.csv'
    if not os.path.exists(error_file) or recalculate:
        # Run the NCL script that computes the error between the WRF run and the ERA5 surface analysis
        CMD_REGRID = 'ncl -Q in_yr=%s in_mo=%s in_da=%s \'WRFdir="%s"\' \'ERAdir="%s"\' \'paramstr="%s"\' ' \
                     '%swrf2era_error.ncl' % \
                     (in_yr, in_mo, in_da, wrfdir, eradir, paramstr, wrfdir)
        # Include a random amount of sleep time to ensure staggering of regridding tasks in a restart run.
        # I added this in an effort to subvert using too much memory on the Magma login node (only 30GB available).
        # time.sleep(random.randint(300, 1800))
        os.system(CMD_REGRID)

        # Extract the total error after the script has run
        startTimeInt = int(time.time())
        while not os.path.exists(error_file):
            log_message = read_last_3lines('log.regrid')
            if 'fatal' in log_message:
                print('NCLError in wrf_era5_regrid_ncl: NCL has failed with the following message:')
                print_last_3lines('log.regrid')
                print('Returning large error values.')
                mae = [0, 6.022 * 10 ** 23, 6.022 * 10 ** 23]
                return mae
            elif (int(time.time()) - startTimeInt) < 600:
                print('TimeoutError in wrf2era_error.ncl: took more than 10min to run... Returning large error values.')
                mae = [0, 6.022 * 10 ** 23, 6.022 * 10 ** 23]
                return mae
            else:
                time.sleep(1)
    mae = read_last_line(error_file)
    mae = mae.split(',')
    mae[-1] = mae[-1].strip()
    try:
        error = [float(i) for i in mae]
    except ValueError:
        error = [0, 6.022 * 10 ** 23, 6.022 * 10 ** 23]

    return error


def wrf_era5_regrid_xesmf(wrfdir='./', wrffile='wrfout_processed_d01_2011-12-13_19mp4lw4sw7lsm8pbl99cu.nc',
                          eradir='/share/mzhang/jas983/wrf_data/data/ERA5/', erafile='ERA5_EastUS_WPD-GHI_2011-12.nc',
                          keep_weights=False):
    """
    CONSIDER MOVING THIS WITHIN THE WRFModel METHOD?

    Converts (regrids) the WRF grid to the ERA5 grid and calculates the total absolute error
    between the global horizonal irradiance (GHI) and wind power density (WPD) in kW -m -2.

    :param wrfdir:
    :param wrffile:
    :param eradir:
    :param erafile:
    :param keep_weights:
    :return:

    """

    # The following function is an ad-hoc fix that changes out-of-original-grid values from zero to NaN.
    def add_matrix_NaNs(regrid):
        X = regrid.weights
        M = scipy.sparse.csr_matrix(X)
        num_nonzeros = np.diff(M.indptr)
        M[num_nonzeros == 0, 0] = np.NaN
        regrid.weights = scipy.sparse.coo_matrix(M)
        return regrid

    # WRF file containing source grid
    # The following block allows the function to succeed even if the wrffile is not found.
    # I think I did this so that this function wouldn't create problems in optimize_wrf_physics.py,
    # but I don't think this function was ever used there, so it should probably be changed.
    try:
        wrfdata = xr.open_dataset(wrfdir + wrffile)
    except FileNotFoundError:
        print(f'ERROR: The wrfout file {wrfdir + wrffile} does not exist. Check that your path.'
              f'\nThis function will not fail!')
        wrfdata = None
        eradata = None
        return wrfdata, eradata

    # Get wrf variable(s) to regrid
    # Read in and convert GHI from W m-2 to kW m-2
    ghi = wrfdata.ghi
    ghi = ghi / 1000

    # Read in WPD, convert from W m-2 to kW m-2
    wpd = wrfdata.wpd
    wpd = wpd / 1000

    # ERA data file(s)
    # Should change/remove this try/except clause also.
    try:
        eradata = xr.open_dataset(eradir + erafile)
    except FileNotFoundError:
        print(f'ERROR: The era5 file {eradir + erafile} does not exist. Check that your path.'
              f'\nThis function will not fail!')
        eradata = None
        return wrfdata, eradata

    # Get variables to compare with regridded WRF variables.
    eradata = eradata.rename({'longitude': 'lon', 'latitude': 'lat'})

    # Read in ERA_GHI, convert from W m-2 to kW m-2
    era_ghi = eradata.GHI
    era_ghi = era_ghi / 1000

    # Read in ERA_WPD, convert from W m-2 to kW m-2
    era_wpd = eradata.WPD
    era_wpd = era_wpd / 1000

    # Write these back to the xarray dataset
    eradata['ghi'] = era_ghi
    eradata['wpd'] = era_wpd

    # Do the regridding ('conservative' donesn't currently work)
    regridder = xe.Regridder(wrfdata, eradata, 'bilinear')
    print(f'The file name is: {regridder.filename} and reuse_weights is: {regridder.reuse_weights}')
    regridder = add_matrix_NaNs(regridder)
    wrf_ghi_regrid = regridder(ghi)
    wrf_wpd_regrid = regridder(wpd)

    # Add the regridded variables to the WRF xarray dataset
    wrfdata['ghi_regrid'] = wrf_ghi_regrid
    wrfdata['wpd_regrid'] = wrf_wpd_regrid

    # Clean up regridding files if specified
    if not keep_weights:
        try:
            regridder.clean_weight_file()
        except AttributeError:
            pass

    return wrfdata, eradata


def wrf_era5_regrid_pyresample(in_yr, in_mo, wrfdir='./', eradir='/share/mzhang/jas983/wrf_data/data/ERA5/'):
    """
    CONSIDER MOVING THIS WITHIN THE WRFModel METHOD?

    Converts (regrids) the WRF grid to the ERA5 grid and calculates the total absolute error
    between the global horizonal irradiance (GHI) and wind power density (WPD) in kW -m -2.

    :param in_yr:
    :param in_mo:
    :param wrfdir:
    :param eradir:
    :return:

    """
    #
    def prs_nearest_regrid(data, var, source_def, target_def, target_lat, target_lon):
        first = True
        for timestr in data.Time:
            # Select the time slice from xarray
            data_slice = data[var].sel(Time=timestr.dt.strftime('%Y-%m-%d %H'))
            # Regrid with a nearest neighbor algorithm
            regridded_data_slice = prs.kd_tree.resample_nearest(source_def, data_slice.values,
                                                                target_def, radius_of_influence=25000, fill_value=None)
            # Put result into an xarray DataArray
            regridded_data_slice_da = xr.DataArray(regridded_data_slice, dims=('lat', 'lon'),
                                                   coords={'lat': target_lat, 'lon': target_lon})
            # Transform the latitude coordinate back to [0-360]
            regridded_data_slice_da.coords['lon'] = (regridded_data_slice_da.coords['lon'] % 360)
            # Add a time dimension
            regridded_data_slice_da.coords['Time'] = timestr.values
            regridded_data_slice_da = regridded_data_slice_da.expand_dims('Time')
            if first is True:
                regridded_data = regridded_data_slice_da
                first = False
            else:
                regridded_data = xr.concat([regridded_data, regridded_data_slice_da], 'Time')

        return regridded_data

    # WRF file containing source grid
    wrffile = 'wrfout_processed_d01.nc'
    try:
        wrfdata = xr.open_dataset(wrfdir + wrffile)
    except FileNotFoundError:
        print(f'The wrfout file {wrfdir + wrffile} does not exist. Check that your path.')
        wrfdata = None
        eradata = None
        return wrfdata, eradata

    # Get wrf variable(s) to regrid
    # Read in and convert GHI from W m-2 to kW m-2
    wrfdata['ghi'] = wrfdata.ghi / 1000

    # Read in WPD, convert from W m-2 to kW m-2
    wrfdata['wpd'] = wrfdata.wpd / 1000

    # ERA data file(s)
    erafile = f'ERA5_EastUS_WPD-GHI_{str(in_yr).zfill(4)}-{str(in_mo).zfill(2)}.nc'
    try:
        eradata = xr.open_dataset(eradir + erafile)
    except FileNotFoundError:
        print(f'The wrfout file {eradir + erafile} does not exist. Check that your path.')
        eradata = None
        return wrfdata, eradata

    # Get variables to compare with regridded WRF variables.
    eradata = eradata.rename({'longitude': 'lon', 'latitude': 'lat'})

    # Read in ERA_GHI, convert from W m-2 to kW m-2
    era_ghi = eradata.GHI
    era_ghi = era_ghi / 1000

    # Read in ERA_WPD, convert from W m-2 to kW m-2
    era_wpd = eradata.WPD
    era_wpd = era_wpd / 1000

    # Write these back to the xarray dataset
    eradata['ghi'] = era_ghi
    eradata['wpd'] = era_wpd

    # Sort the ERA data for pyresammple
    eradata = eradata.sortby('lat', ascending=True)

    # Create grid definitions for pyresample
    # SwathDefinition() require that lons and lats be in a specific format (taken care of by check_and_wrap())
    # and that they have the same shape (taken care of by np.meshgrid())
    era_lon, era_lat = prs.utils.check_and_wrap(eradata.lon.values, eradata.lat.values)
    era_lon2d, era_lat2d = np.meshgrid(era_lon, era_lat)
    # Create the definition for the target (ERA5 lat/lon) grid
    era_def = prs.geometry.SwathDefinition(lons=era_lon2d, lats=era_lat2d)
    # Preprocess and create the definition for the source (WRF Lambert Conformal) grid
    wrf_lon, wrf_lat = prs.utils.check_and_wrap(wrfdata.lon.values, wrfdata.lat.values)
    wrf_def = prs.geometry.SwathDefinition(lons=wrf_lon, lats=wrf_lat)

    # Do the regridding
    wrf_ghi_regrid = prs_nearest_regrid(wrfdata, 'ghi', wrf_def, era_def, era_lat, era_lon)
    wrf_wpd_regrid = prs_nearest_regrid(wrfdata, 'wpd', wrf_def, era_def, era_lat, era_lon)

    # Add the regridded variables to the WRF xarray dataset
    wrfdata['ghi_regrid'] = wrf_ghi_regrid
    wrfdata['wpd_regrid'] = wrf_wpd_regrid

    return wrfdata, eradata


def wrf_era5_error(wrfdata, eradata):
    """

    :param wrfdata: xarray.DataSet
    :param eradata: xarray.DataSet
    :return wrfdata: xarray.DataSet

    """
    # Compute the error (absolute difference) between WRF and ERA5 data
    # Note that only times from the WRF file will remain in *error variables.
    wrfdata['ghi_error'] = abs(wrfdata.ghi_regrid - eradata.ghi)
    wrfdata['wpd_error'] = abs(wrfdata.wpd_regrid - eradata.wpd)

    # Sum all the hours in the wrfdata to get the total errors.
    # To get around an xrray nan bug, fill all nan with -1.
    # Since we applied abs(), all the values in our errors are >= 0
    ghi_error_nonan = wrfdata.ghi_error.fillna(-1)
    total_ghi_error = ghi_error_nonan.sum(dim='Time')
    wrfdata['total_ghi_error'] = total_ghi_error.where(total_ghi_error > 0)
    wpd_error_nonan = wrfdata.wpd_error.fillna(-1)
    total_wpd_error = wpd_error_nonan.sum(dim='Time')
    wrfdata['total_wpd_error'] = total_wpd_error.where(total_wpd_error > 0)

    return wrfdata