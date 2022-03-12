"""
Class and supporting functions to run WRF within other scripts
and process WRF output data.


Known Issues/Wishlist:
- My username/password are currently hard-coded into rda_download(). I SHOULD CHAGE THIS!
- In determine_computer(), only my user name identifies magma -- should generalize this.
- Need to include in documentation:
    - A description of how to create the dirpath.yml file.
    - A description of how to customize the templates directory.
- I'm unhappy with the output to screen from rda_download(). Perhaps edit that and
check_file_status() as well.
- A better way to set the command aliai would be nice.

"""
import calendar
import concurrent.futures
import datetime
import dateutil
import netCDF4
import numpy as np
import os
import pandas as pd
import sys
import time
import wrf
import xarray as xr
import yaml

from pvlib.wrfcast import WRF
import optwrf.helper_functions as hf
import optwrf.util as util
from optwrf.helper_functions import determine_computer, read_last_line, print_last_3lines, \
    rda_download
from optwrf.regridding import wrf_era5_regrid_ncl, wrf_era5_regrid_xesmf, wrf_era5_regrid_pyresample, wrf_era5_error
from optwrf.wrfparams import ids2str
from optwrf.wrfparams import flexible_generate
from optwrf.data.fetch_data import fetch_yaml


class WRFModel:
    """
    This class provides a framework for running the WRF model

    """

    def __init__(self, param_ids, start_date, end_date, bc_data='ERA', bc_src='RDA',
                 n_domains=1, setup_yaml='dirpath.yml', wfp=False, verbose=True):
        self.param_ids = param_ids
        self.start_date = start_date
        self.end_date = end_date
        self.bc_data = bc_data
        self.bc_src = bc_src
        self.n_domains = n_domains
        self.wfp = wfp
        self.verbose = verbose

        # Format the forecast start/end and determine the total time.
        self.forecast_start = hf.format_date(start_date)
        self.forecast_end = hf.format_date(end_date)
        self.delt = self.forecast_end - self.forecast_start
        if self.verbose:
            print('Forecast starting on: {}'.format(self.forecast_start))
            print('Forecast ending on: {}'.format(self.forecast_end))

        # Ensure that parameters are in the correct format
        self.paramstr = ids2str(self.param_ids)
        if len(self.param_ids) == 6:
            self.param_ids = flexible_generate(generate_params=False, mp=self.param_ids[0],
                                               lw=self.param_ids[1], sw=self.param_ids[2],
                                               lsm=self.param_ids[3], pbl=self.param_ids[4], cu=self.param_ids[5])
            if self.verbose:
                print(f'Final parameters are: {self.param_ids}')

        # Determine which computer you are running on
        # to set directories and command aliai
        on_aws, on_cheyenne, on_magma = determine_computer()
        self.on_aws = on_aws
        self.on_cheyenne = on_cheyenne
        self.on_magma = on_magma

        # Set working and WRF model directory names
        dirs = fetch_yaml(setup_yaml)
        dirpaths = dirs.get('directory_paths')
        self.DIR_WRF_ROOT = dirpaths.get('DIR_WRF_ROOT')
        self.DIR_WPS = self.DIR_WRF_ROOT + 'WPS/'
        self.DIR_WRF = self.DIR_WRF_ROOT + 'WRF/'
        self.DIR_DATA_ROOT = dirpaths.get('DIR_DATA_ROOT')
        self.DIR_WPS_GEOG = self.DIR_DATA_ROOT + 'WPS_GEOG/'
        self.DIR_DATA = self.DIR_DATA_ROOT + 'data/' + str(self.bc_data) + '/'
        self.DIR_DATA_TMP = f'{self.DIR_DATA_ROOT}data/{self.forecast_start.strftime("%Y-%m-%d")}_{self.paramstr}/'
        self.DIR_MET4ENE = dirpaths.get('DIR_MET4ENE')
        self.DIR_WRFOUT = self.DIR_MET4ENE + 'wrfout/ARW/%s_' % \
                          (self.forecast_start.strftime('%Y-%m-%d')) + self.paramstr + '/'
        self.DIR_RUNWRF = self.DIR_MET4ENE + 'optwrf/optwrf/'
        self.DIR_TEMPLATES = dirpaths.get('DIR_TEMPLATES')
        self.DIR_ERA5_ROOT = dirpaths.get('DIR_ERA5_ROOT')
        self.FILE_WRFOUT_d01 = 'wrfout_d01' + '_' \
                                + self.forecast_start.strftime('%Y') + '-' \
                                + self.forecast_start.strftime('%m') + '-' \
                                + self.forecast_start.strftime('%d') + '_00:00:00'
        if self.n_domains > 1:
            self.FILE_WRFOUT_d02 = 'wrfout_d02' + '_' \
                                   + self.forecast_start.strftime('%Y') + '-' \
                                   + self.forecast_start.strftime('%m') + '-' \
                                   + self.forecast_start.strftime('%d') + '_00:00:00'
        if self.n_domains > 2:
            self.FILE_WRFOUT_d03 = 'wrfout_d03' + '_' \
                                   + self.forecast_start.strftime('%Y') + '-' \
                                   + self.forecast_start.strftime('%m') + '-' \
                                   + self.forecast_start.strftime('%d') + '_00:00:00'

        # Define linux command aliai
        self.CMD_LN = 'ln -sf %s %s'
        self.CMD_CP = 'cp %s %s'
        self.CMD_MV = 'mv %s %s'
        self.CMD_RM = 'rm %s'
        self.CMD_CHMOD = 'chmod -R %s %s'
        self.CMD_LINK_GRIB = f'{self.DIR_RUNWRF}link_grib.csh {self.DIR_DATA_TMP} {self.DIR_WRFOUT}'

        if self.on_cheyenne:
            self.CMD_GEOGRID = 'qsub ' + self.DIR_WRFOUT + 'rungeogrid.csh'
            self.CMD_UNGMETG = 'qsub ' + self.DIR_WRFOUT + 'runungmetg.csh'
            self.CMD_REAL = 'qsub ' + self.DIR_WRFOUT + 'runreal.csh'
            self.CMD_WRF = 'qsub ' + self.DIR_WRFOUT + 'runwrf.csh'
        elif self.on_aws:
            self.CMD_GEOGRID = './rungeogrid.csh'
            self.CMD_UNGMETG = './runungmetg.csh'
            self.CMD_REAL = './runreal.csh'
            self.CMD_WRF = './runwrf.csh'
        else:
            self.CMD_GEOGRID = 'sbatch --requeue ' + self.DIR_WRFOUT + 'rungeogrid.csh ' + self.DIR_WRFOUT
            self.CMD_UNGMETG = 'sbatch --requeue ' + self.DIR_WRFOUT + 'runungmetg.csh ' + self.DIR_WRFOUT
            self.CMD_REAL = 'sbatch --requeue ' + self.DIR_WRFOUT + 'runreal.csh ' + self.DIR_WRFOUT
            self.CMD_WRF = 'sbatch --requeue ' + self.DIR_WRFOUT + 'runwrf.csh ' + self.DIR_WRFOUT

    def runwrf_finish_check(self, program, nprocs=8):
        """
        Check if a specified WRF subprogram has finished running. Does this specifically by
        checking the first and the last rsl.out.* file created by each processor running
        either wrf.exe or real.exe via OpenMPI.

        ***NOTE: It's not currently possible for geogrid or metgrid to fail,
        because I don't know what failure message to look for in the log.

        :param program: string
            WRF or WPS subprogram name whose status is to be checked.
        :param nprocs: integer
            Number of processors that you are using to run real.exe and wrf.exe.
        :return: 'running' or 'complete' or 'failed' string
            Run status of the program.

        """
        if program == 'geogrid':
            msg = read_last_line(self.DIR_WRFOUT + 'geogrid.log')
            complete = 'Successful completion of program geogrid' in msg
            # Not sure what the correct failure message should be!
            failed = False
        elif program == 'metgrid':
            msg = read_last_line(self.DIR_WRFOUT + 'metgrid.log')
            complete = 'Successful completion of program metgrid' in msg
            # Not sure what the correct failure message should be!
            failed = False
        elif program == 'real':
            msg = read_last_line(self.DIR_WRFOUT + 'rsl.out.0000')
            complete = 'SUCCESS COMPLETE REAL' in msg
            failed = '-------------------------------------------' in msg
            if not complete and not failed:
                msg = read_last_line(self.DIR_WRFOUT + 'rsl.out.00' + str(nprocs - 1).zfill(2))
                failed = '-------------------------------------------' in msg
        elif program == 'wrf':
            msg = read_last_line(self.DIR_WRFOUT + 'rsl.out.0000')
            complete = 'SUCCESS COMPLETE WRF' in msg
            failed = '-------------------------------------------' in msg
            if not complete and not failed:
                msg = read_last_line(self.DIR_WRFOUT + 'rsl.out.00' + str(nprocs - 1).zfill(2))
                failed = '-------------------------------------------' in msg
        else:
            complete = False
            failed = False
        if failed:
            print(f'\nRunwrfError: {program} has failed. Last message was:\n{msg}')
            return 'failed'
        elif complete:
            return 'complete'
        else:
            return 'running'

    def get_bc_data(self):
        """
        Downloads boundary condition data from the RDA
        if it does not already exist in the expected data directory (self.DIR_DATA).
        Then, it creates a temporary data directory (self.DIR_DATA_TMP) and copies
        data from the central data directory to the temporary data directory.

        The justificaion for this approach is that the link_grib.csh script doesn't
        contain a good way of picking files out of many. Therefore, it is much
        easier to link all the files in the temporary data directory than to link
        indidivdual files out of the central data directory.

        NOTE Currently, only ERA5 data (ds633.0) and the old ERA-interim data (ds627.0) are supported!

        :return vtable_sfx: string
            WPS variable table suffix -- tells subsequent methods which boundary condidtion data is being used
            so that ungrib can successfully unpack data.

        """
        if self.bc_data == 'ERA5':
            # Reset the boundary condition data source to the CDS api
            self.bc_src = 'CDS'
            if self.on_cheyenne:
                # The following variables define the path where ERA is located within the Cheyenne RDA
                DATA_ROOT1 = '/gpfs/fs1/collections/rda/data/ds633.0/e5.oper.an.pl/'
                DATA_ROOT2 = '/gpfs/fs1/collections/rda/data/ds633.0/e5.oper.an.sfc/'
                print(f'{self.bc_data} is not ready for use on Cheyenne')
                raise NotImplementedError
            else:
                # Prefixes for the output file names
                pl_pfx = 'e5.oper.an.pl.'
                sfc_pfx = 'e5.oper.an.sfc.'
                # CDS pressure level and surface product names and type
                cds_pl_product = 'reanalysis-era5-pressure-levels'
                cds_sfc_product = 'reanalysis-era5-single-levels'
                cds_product_type = 'reanalysis'
                # Specify the spatial extent of the data you wish to download
                # (the ones below are for the Continential US)
                north_lat = 60
                south_lat = 20
                west_lon = -140
                east_lon = -50
                cds_area_str = f'{north_lat}/{west_lon}/{south_lat}/{east_lon}'
                cds_times = '00/to/23/by/1'
                cds_pls = [
                    '1', '2', '3',
                    '5', '7', '10',
                    '20', '30', '50',
                    '70', '100', '125',
                    '150', '175', '200',
                    '225', '250', '300',
                    '350', '400', '450',
                    '500', '550', '600',
                    '650', '700', '750',
                    '775', '800', '825',
                    '850', '875', '900',
                    '925', '950', '975',
                    '1000'
                ]
                cds_pl_vars = [
                    'geopotential',
                    'relative_humidity',
                    'specific_humidity',
                    'temperature',
                    'u_component_of_wind',
                    'v_component_of_wind'
                ]
                cds_sfc_vars = [
                    'surface_pressure',
                    'mean_sea_level_pressure',
                    'skin_temperature',
                    'sea_surface_temperature',
                    'sea_ice_cover',
                    '2m_temperature',
                    '2m_dewpoint_temperature',
                    '10m_u_component_of_wind',
                    '10m_v_component_of_wind',
                    'land_sea_mask',
                    'snow_depth',
                    'soil_temperature_level_1',
                    'soil_temperature_level_2',
                    'soil_temperature_level_3',
                    'soil_temperature_level_4',
                    'volumetric_soil_water_layer_1',
                    'volumetric_soil_water_layer_2',
                    'volumetric_soil_water_layer_3',
                    'volumetric_soil_water_layer_4'
                ]
            vtable_sfx = 'ERA-interim.pl'
        elif self.bc_data == 'ERA':
            if self.on_cheyenne:
                # The following variables define the path where ERA is located within the Cheyenne RDA
                DATA_ROOT1 = '/gpfs/fs1/collections/rda/data/ds627.0/ei.oper.an.pl/'
                DATA_ROOT2 = '/gpfs/fs1/collections/rda/data/ds627.0/ei.oper.an.sfc/'
            else:
                # The following define paths to the ERA data on the RDA site
                dspath = 'http://rda.ucar.edu/data/ds627.0/'
                DATA_ROOT1 = 'ei.oper.an.pl/'
                DATA_ROOT2 = 'ei.oper.an.sfc/'
            datpfx1 = 'ei.oper.an.pl.regn128sc.'
            datpfx2 = 'ei.oper.an.pl.regn128uv.'
            datpfx3 = 'ei.oper.an.sfc.regn128sc.'
            vtable_sfx = 'ERA-interim.pl'
        else:
            print(f'Currently {self.bc_data} is not supported; please use ERA or ERA5 for boundary condition data.')
            raise ValueError

        if self.verbose:
            print(f'Using {self.bc_data} data for boundary conditions')
            print(f'The corresponding Vtable is: {vtable_sfx}')
            print(f'--> Data Directory:\n{self.DIR_DATA}')

        # ----- Code shared by all boundary condition data begins here -----
        # If no data directory exists, create one
        if not os.path.exists(self.DIR_DATA):
            os.makedirs(self.DIR_DATA, 0o755)

        # Determine the forecast duration
        forecast_duration = self.forecast_end - self.forecast_start

        # Define the date list
        date_list = [(self.forecast_start + datetime.timedelta(days=x)) for x in range(forecast_duration.days + 1)]

        # Clean potential old temporary data directory (DIR_DATA_TMP) and remake the dir
        hf.remove_dir(self.DIR_DATA_TMP)
        try:
            os.makedirs(self.DIR_DATA_TMP, 0o755)
        except FileExistsError as e:
            if self.verbose:
                print(f'OptWRFWarning in get_bc_data: the data directory you just deleted and attempted to remake '
                      f'was likely remade by another thread:\n\t{e}')

        # Depending on what computer you are on...
        if self.on_cheyenne:
            # Copy desired data files from local RDA
            for date in date_list:
                year_mo = date.strftime('%Y') + date.strftime('%m')
                year_mo_day = date.strftime('%Y') + date.strftime('%m') + date.strftime('%d')
                cmd = self.CMD_CP % (DATA_ROOT1 + year_mo + '/' + datpfx1 + year_mo_day + '*', self.DIR_DATA_TMP)
                cmd = cmd + '; ' + self.CMD_CP % (DATA_ROOT1 + year_mo + '/'
                                                  + datpfx2 + year_mo_day + '*', self.DIR_DATA_TMP)
                cmd = cmd + '; ' + self.CMD_CP % (DATA_ROOT2 + year_mo + '/'
                                                  + datpfx3 + year_mo_day + '*', self.DIR_DATA_TMP)
                os.system(cmd)
        else:
            # Build the complete path to required files (filelist(s)),
            # and a list of the file names themselves (file_check)
            file_check = []
            if self.bc_src == 'RDA':
                # For the RDA, we download data every 6h for initialization,
                # and we build this filelist manually using the hrs list below.
                hrs = ['00', '06', '12', '18']
                filelist = []
                for date in date_list:
                    for hr in hrs:
                        year_mo = date.strftime('%Y') + date.strftime('%m')
                        year_mo_day_hr = date.strftime('%Y') + date.strftime('%m') + date.strftime('%d') + hr
                        filelist.append(DATA_ROOT1 + year_mo + '/' + datpfx1 + year_mo_day_hr)
                        filelist.append(DATA_ROOT1 + year_mo + '/' + datpfx2 + year_mo_day_hr)
                        filelist.append(DATA_ROOT2 + year_mo + '/' + datpfx3 + year_mo_day_hr)
                        file_check.append(datpfx1 + year_mo_day_hr)
                        file_check.append(datpfx2 + year_mo_day_hr)
                        file_check.append(datpfx3 + year_mo_day_hr)

            elif self.bc_src == 'CDS':
                # For the CDS API, we simply download one pressure levels file and one surface file
                # for each day. However, the command we will use to download the pressure level data
                # and the surfce data will be different, so we need three file
                pl_filelist = []
                sfc_filelist = []
                for date in date_list:
                    year_mo_day = date.strftime('%Y') + date.strftime('%m') + date.strftime('%d')
                    # Add the files to the lists
                    file_check.append(f'{pl_pfx}{year_mo_day}_{year_mo_day}.grb')
                    file_check.append(f'{sfc_pfx}{year_mo_day}_{year_mo_day}.grb')

            # Check to see if all these files already exist in the data directory
            data_exists = []
            for data_file in file_check:
                data_exists.append(os.path.exists(self.DIR_DATA + data_file))
            if self.verbose:
                print(f'This simulation requires {len(file_check)} files, '
                      f'{data_exists.count(True)} are already in your data directory.\n'
                      f'The files are:')
                [print(name) for name in file_check]

            if data_exists.count(True) == len(file_check):
                if self.verbose:
                    print('Boundary condition data was previously downloaded from RDA.')
            else:
                if self.bc_src == 'RDA':
                    # Download the data from the online RDA (requires password and connection)
                    success = rda_download(filelist, dspath)
                    if not success:
                        print(f'{self.bc_data} data was not successfully downloaded from RDA.')
                        raise RuntimeError
                elif self.bc_src == 'CDS':
                    # Download the data using the CDS API
                    for date in date_list:
                        year_mo_day = date.strftime('%Y') + date.strftime('%m') + date.strftime('%d')
                        dates_str = f'{year_mo_day}/{year_mo_day}'
                        pl_file_name = f'{pl_pfx}{year_mo_day}_{year_mo_day}.grb'
                        sfc_file_name = f'{sfc_pfx}{year_mo_day}_{year_mo_day}.grb'
                        # Download the pressure level data
                        util.get_data_cdsapi(cds_pl_product, cds_pl_vars,
                                             product_type=cds_product_type,
                                             fmt='grib',
                                             pressure_level=cds_pls,
                                             area=cds_area_str,
                                             date=dates_str,
                                             time=cds_times,
                                             output_file_name=pl_file_name)

                        # Download the surface data
                        util.get_data_cdsapi(cds_sfc_product, cds_sfc_vars,
                                             product_type=cds_product_type,
                                             fmt='grib',
                                             area=cds_area_str,
                                             date=dates_str,
                                             time=cds_times,
                                             output_file_name=sfc_file_name)
                else:
                    print(f'Boundary condidion data source {self.bc_data} is not supportted.')
                    raise NotImplementedError

                # Move the data files to the data directory
                for file in file_check:
                    os.system(self.CMD_MV % (file, self.DIR_DATA))

            # Link files in the data directory to the temporary data directory
            for file in file_check:
                cmd = self.CMD_LN % (self.DIR_DATA + file, self.DIR_DATA_TMP)
                os.system(cmd)

        return vtable_sfx

    def wrfdir_setup(self, vtable_sfx):
        """
        Sets up the WRF run directory by copying scripts, data files, and executables.

        :param vtable_sfx: string
            variable table suffix specific to the boundary condition data;
            required to run WPS.

        """
        # Make the simulation directory; delete the old one if it exists
        try:
            hf.remove_dir(self.DIR_WRFOUT)
            os.makedirs(self.DIR_WRFOUT, 0o755)
        except FileExistsError as e:
            print(f'OptWRFWarning in wrfdir_setup; skipping this simulaion.')
            print(f'\t{e}')
            return False

        # Link WRF tables, data, and executables.
        cmd = self.CMD_LN % (self.DIR_WRF + 'run/aerosol*', self.DIR_WRFOUT)
        cmd = cmd + '; ' + self.CMD_LN % (self.DIR_WRF + 'run/BROADBAND*', self.DIR_WRFOUT)
        cmd = cmd + '; ' + self.CMD_LN % (self.DIR_WRF + 'run/bulk*', self.DIR_WRFOUT)
        cmd = cmd + '; ' + self.CMD_LN % (self.DIR_WRF + 'run/CAM*', self.DIR_WRFOUT)
        cmd = cmd + '; ' + self.CMD_LN % (self.DIR_WRF + 'run/capacity*', self.DIR_WRFOUT)
        cmd = cmd + '; ' + self.CMD_LN % (self.DIR_WRF + 'run/CCN*', self.DIR_WRFOUT)
        cmd = cmd + '; ' + self.CMD_LN % (self.DIR_WRF + 'run/CLM*', self.DIR_WRFOUT)
        cmd = cmd + '; ' + self.CMD_LN % (self.DIR_WRF + 'run/co2*', self.DIR_WRFOUT)
        cmd = cmd + '; ' + self.CMD_LN % (self.DIR_WRF + 'run/coeff*', self.DIR_WRFOUT)
        cmd = cmd + '; ' + self.CMD_LN % (self.DIR_WRF + 'run/constants*', self.DIR_WRFOUT)
        cmd = cmd + '; ' + self.CMD_LN % (self.DIR_WRF + 'run/create*', self.DIR_WRFOUT)
        cmd = cmd + '; ' + self.CMD_LN % (self.DIR_WRF + 'run/ETAMPNEW*', self.DIR_WRFOUT)
        cmd = cmd + '; ' + self.CMD_LN % (self.DIR_WRF + 'run/GENPARM*', self.DIR_WRFOUT)
        cmd = cmd + '; ' + self.CMD_LN % (self.DIR_WRF + 'run/grib2map*', self.DIR_WRFOUT)
        cmd = cmd + '; ' + self.CMD_LN % (self.DIR_WRF + 'run/gribmap*', self.DIR_WRFOUT)
        cmd = cmd + '; ' + self.CMD_LN % (self.DIR_WRF + 'run/HLC*', self.DIR_WRFOUT)
        cmd = cmd + '; ' + self.CMD_LN % (self.DIR_WRF + 'run/ishmael*', self.DIR_WRFOUT)
        cmd = cmd + '; ' + self.CMD_LN % (self.DIR_WRF + 'run/kernels*', self.DIR_WRFOUT)
        cmd = cmd + '; ' + self.CMD_LN % (self.DIR_WRF + 'run/LANDUSE*', self.DIR_WRFOUT)
        cmd = cmd + '; ' + self.CMD_LN % (self.DIR_WRF + 'run/masses*', self.DIR_WRFOUT)
        cmd = cmd + '; ' + self.CMD_LN % (self.DIR_WRF + 'run/MPTABLE*', self.DIR_WRFOUT)
        cmd = cmd + '; ' + self.CMD_LN % (self.DIR_WRF + 'run/ozone*', self.DIR_WRFOUT)
        cmd = cmd + '; ' + self.CMD_LN % (self.DIR_WRF + 'run/p3_lookup*', self.DIR_WRFOUT)
        cmd = cmd + '; ' + self.CMD_LN % (self.DIR_WRF + 'run/RRTM*', self.DIR_WRFOUT)
        cmd = cmd + '; ' + self.CMD_LN % (self.DIR_WRF + 'run/SOILPARM*', self.DIR_WRFOUT)
        cmd = cmd + '; ' + self.CMD_LN % (self.DIR_WRF + 'run/termvels*', self.DIR_WRFOUT)
        cmd = cmd + '; ' + self.CMD_LN % (self.DIR_WRF + 'run/tr*', self.DIR_WRFOUT)
        cmd = cmd + '; ' + self.CMD_LN % (self.DIR_WRF + 'run/URBPARM*', self.DIR_WRFOUT)
        cmd = cmd + '; ' + self.CMD_LN % (self.DIR_WRF + 'run/VEGPARM*', self.DIR_WRFOUT)
        cmd = cmd + '; ' + self.CMD_LN % (self.DIR_WRF + 'run/*exe', self.DIR_WRFOUT)
        os.system(cmd)
        if self.verbose:
            print(f'--> WRFOUT Directory:\n{self.DIR_WRFOUT}')

        # Copy over namelists and submission scripts
        cmd = self.CMD_CP % (self.DIR_TEMPLATES + 'namelist.wps', self.DIR_WRFOUT)
        cmd = cmd + '; ' + self.CMD_CP % (self.DIR_TEMPLATES + 'namelist.input', self.DIR_WRFOUT )
        cmd = cmd + '; ' + self.CMD_CP % (self.DIR_TEMPLATES + 'template_rungeogrid.csh',
                                          self.DIR_WRFOUT + 'rungeogrid.csh')
        cmd = cmd + '; ' + self.CMD_CP % (self.DIR_TEMPLATES + 'template_runungmetg.csh',
                                          self.DIR_WRFOUT + 'runungmetg.csh')
        cmd = cmd + '; ' + self.CMD_CP % (self.DIR_TEMPLATES + 'template_runreal.csh',
                                          self.DIR_WRFOUT + 'runreal.csh')
        cmd = cmd + '; ' + self.CMD_CP % (self.DIR_TEMPLATES + 'template_runwrf.csh',
                                          self.DIR_WRFOUT + 'runwrf.csh')
        if self.wfp:
            cmd = cmd + '; ' + self.CMD_CP % (self.DIR_TEMPLATES + 'wind-turbine-1.tbl', self.DIR_WRFOUT)
            cmd = cmd + '; ' + self.CMD_CP % (self.DIR_TEMPLATES + 'windturbines*',
                                              self.DIR_WRFOUT + 'windturbines.txt')
        os.system(cmd)

        # Link the metgrid and geogrid dirs and executables as well as the correct variable table for the BC/IC data.
        cmd = self.CMD_LN % (self.DIR_WPS + 'geogrid', self.DIR_WRFOUT)
        cmd = cmd + '; ' + self.CMD_LN % (self.DIR_WPS + 'geogrid.exe', self.DIR_WRFOUT)
        cmd = cmd + '; ' + self.CMD_LN % (self.DIR_WPS + 'ungrib.exe', self.DIR_WRFOUT)
        cmd = cmd + '; ' + self.CMD_LN % (self.DIR_WPS + 'metgrid', self.DIR_WRFOUT)
        cmd = cmd + '; ' + self.CMD_LN % (self.DIR_WPS + 'metgrid.exe', self.DIR_WRFOUT)
        cmd = cmd + '; ' + self.CMD_LN % (self.DIR_WPS + 'ungrib/Variable_Tables/Vtable.'
                                          + vtable_sfx, self.DIR_WRFOUT + 'Vtable')
        os.system(cmd)

        # Link the regridding script
        cmd = self.CMD_LN % (self.DIR_RUNWRF + 'wrf2era_error.ncl', self.DIR_WRFOUT)
        os.system(cmd)
        return True

    def prepare_namelists(self):
        """
        Writes dates, the geographical data path, number of domains, runtime duration,
        and physics options to the WPS and/or WRF namelist files.

        """

        def read_namelist(namelist_file):
            """
            Opens a namelist file within a context manager.

            :param namelist_file: string
                Path to the namelist file you wish to open.
            :return NAMELIST: file object

            """
            with open(self.DIR_WRFOUT + namelist_file, 'r') as namelist:
                NAMELIST = namelist.read()
            return NAMELIST

        # Try to open WPS and WRF namelists as readonly,
        # and print an error & exit if you cannot.
        try:
            NAMELIST_WPS = read_namelist('namelist.wps')
            NAMELIST_WRF = read_namelist('namelist.input')
        except IOError as e:
            print(f'OptWRFWarning in prepare_namelists; skipping this simulaion.')
            print(f'\t{e}')
            return False

        # Write the start and end dates to the WPS Namelist
        wps_dates = ' start_date                     = '
        for i in range(0, self.n_domains):
            wps_dates = wps_dates + self.forecast_start.strftime("'%Y-%m-%d_%H:%M:%S', ")
        wps_dates = wps_dates + '\n end_date                     = '
        for i in range(0, self.n_domains):
            wps_dates = wps_dates + self.forecast_end.strftime("'%Y-%m-%d_%H:%M:%S', ")
        with open(self.DIR_WRFOUT + 'namelist.wps', 'w') as namelist:
            namelist.write(NAMELIST_WPS.replace('%DATES%', wps_dates))

        # Write the GEOG data path to the WPS Namelist
        NAMELIST_WPS = read_namelist('namelist.wps')
        geog_data = " geog_data_path = '" + self.DIR_WPS_GEOG + "'"
        with open(self.DIR_WRFOUT + 'namelist.wps', 'w') as namelist:
            namelist.write(NAMELIST_WPS.replace('%GEOG%', geog_data))

        # Write the number of domains to the WPS Namelist
        NAMELIST_WPS = read_namelist('namelist.wps')
        wps_domains = ' max_dom                             = ' + str(self.n_domains) + ','
        with open(self.DIR_WRFOUT + 'namelist.wps', 'w') as namelist:
            namelist.write(NAMELIST_WPS.replace('%DOMAIN%', wps_domains))
        if self.verbose:
            print('Done writing WPS namelist!')

        # Write the runtime info and start dates and times to the WRF Namelist
        wrf_runtime = ' run_days                            = ' + str(self.delt.days) + ',\n'
        wrf_runtime = wrf_runtime + ' run_hours                           = ' + '0' + ',\n'
        wrf_runtime = wrf_runtime + ' run_minutes                         = ' + '0' + ',\n'
        wrf_runtime = wrf_runtime + ' run_seconds                         = ' + '0' + ','
        with open(self.DIR_WRFOUT + 'namelist.input', 'w') as namelist:
            namelist.write(NAMELIST_WRF.replace('%RUNTIME%', wrf_runtime))

        NAMELIST_WRF = read_namelist('namelist.input')
        wrf_dates = ' start_year                          = '
        for i in range(0, self.n_domains):
            wrf_dates = wrf_dates + self.forecast_start.strftime('%Y, ')
        wrf_dates = wrf_dates + '\n start_month                         = '
        for i in range(0, self.n_domains):
            wrf_dates = wrf_dates + self.forecast_start.strftime('%m, ')
        wrf_dates = wrf_dates + '\n start_day                           = '
        for i in range(0, self.n_domains):
            wrf_dates = wrf_dates + self.forecast_start.strftime('%d, ')
        wrf_dates = wrf_dates + '\n start_hour                          = '
        for i in range(0, self.n_domains):
            wrf_dates = wrf_dates + self.forecast_start.strftime('%H, ')
        wrf_dates = wrf_dates + '\n start_minute                        = '
        for i in range(0, self.n_domains):
            wrf_dates = wrf_dates + '00, '
        wrf_dates = wrf_dates + '\n start_second                        = '
        for i in range(0, self.n_domains):
            wrf_dates = wrf_dates + '00, '
        wrf_dates = wrf_dates + '\n end_year                            = '
        for i in range(0, self.n_domains):
            wrf_dates = wrf_dates + self.forecast_end.strftime('%Y, ')
        wrf_dates = wrf_dates + '\n end_month                           = '
        for i in range(0, self.n_domains):
            wrf_dates = wrf_dates + self.forecast_end.strftime('%m, ')
        wrf_dates = wrf_dates + '\n end_day                             = '
        for i in range(0, self.n_domains):
            wrf_dates = wrf_dates + self.forecast_end.strftime('%d, ')
        wrf_dates = wrf_dates + '\n end_hour                            = '
        for i in range(0, self.n_domains):
            wrf_dates = wrf_dates + self.forecast_end.strftime('%H, ')
        wrf_dates = wrf_dates + '\n end_minute                          = '
        for i in range(0, self.n_domains):
            wrf_dates = wrf_dates + '00, '
        wrf_dates = wrf_dates + '\n end_second                          = '
        for i in range(0, self.n_domains):
            wrf_dates = wrf_dates + '00, '
        with open(self.DIR_WRFOUT + 'namelist.input', 'w') as namelist:
            namelist.write(NAMELIST_WRF.replace('%DATES%', wrf_dates))

        # Write the physics parametrization scheme info to the WRF Namelist
        NAMELIST_WRF = read_namelist('namelist.input')
        wrf_physics = ' mp_physics                          = '
        for i in range(0, self.n_domains):
            wrf_physics = wrf_physics + str(self.param_ids[0]) + ', '
        wrf_physics = wrf_physics + '\n ra_lw_physics                       = '
        for i in range(0, self.n_domains):
            wrf_physics = wrf_physics + str(self.param_ids[1]) + ', '
        wrf_physics = wrf_physics + '\n ra_sw_physics                       = '
        for i in range(0, self.n_domains):
            wrf_physics = wrf_physics + str(self.param_ids[2]) + ', '
        wrf_physics = wrf_physics + '\n sf_surface_physics                  = '
        for i in range(0, self.n_domains):
            wrf_physics = wrf_physics + str(self.param_ids[3]) + ', '
        wrf_physics = wrf_physics + '\n bl_pbl_physics                      = '
        for i in range(0, self.n_domains):
            wrf_physics = wrf_physics + str(self.param_ids[4]) + ', '
        wrf_physics = wrf_physics + '\n cu_physics                          = '
        wrf_physics = wrf_physics + str(self.param_ids[5]) + ', ' + (self.n_domains - 1) * '0, '
        wrf_physics = wrf_physics + '\n sf_sfclay_physics                   = '
        for i in range(0, self.n_domains):
            wrf_physics = wrf_physics + str(self.param_ids[6]) + ', '

        # The following namelist options are only set if certain parameter choices are selected
        if self.param_ids[6] in [1, 5, 7, 11]:
            wrf_physics = wrf_physics + '\n isfflx                              = 1, '
        if self.param_ids[6] in [1]:
            wrf_physics = wrf_physics + '\n ifsnow                              = 1, '
        if self.param_ids[1] in [1, 4] and self.param_ids[2] in [1, 4]:
            wrf_physics = wrf_physics + '\n icloud                              = 1, '
        if self.param_ids[5] in [5, 93]:
            wrf_physics = wrf_physics + '\n maxiens                             = 1,'
        if self.param_ids[5] in [93]:
            wrf_physics = wrf_physics + '\n maxens                              = 3,'
            wrf_physics = wrf_physics + '\n maxens2                             = 3,'
            wrf_physics = wrf_physics + '\n maxens3                             = 16,'
            wrf_physics = wrf_physics + '\n ensdim                              = 144,'
        with open(self.DIR_WRFOUT + 'namelist.input', 'w') as namelist:
            namelist.write(NAMELIST_WRF.replace('%PARAMS%', wrf_physics))

        # Write the number of domains to the namelist
        NAMELIST_WRF = read_namelist('namelist.input')
        wrf_domains = ' max_dom                             = ' + str(self.n_domains) + ','
        with open(self.DIR_WRFOUT + 'namelist.input', 'w') as namelist:
            namelist.write(NAMELIST_WRF.replace('%DOMAIN%', wrf_domains))
        if self.verbose:
            print('Done writing WRF namelist!\n')
        return True

    def run_wps(self, disable_timeout=False):
        """
        Runs the WRF preprocessing executables and confirms thier success.

        :return: boolean (True/False)
            If runwrf_finish_check for geogrid and metgrid
            returns 'complete' ('failed'), this function returns True (False).

        """
        # Run geogrid if necessary
        # Build the list of geogrid files
        geogridfiles = [f'geo_em.d{str(domain).zfill(2)}.nc' for domain in range(1, self.n_domains + 1)]
        # Check to see if the geogrid files exist in the expected directory
        geogridfilesexist = [os.path.exists(self.DIR_DATA_ROOT + 'data/domain/' + file) for file in geogridfiles]
        if geogridfilesexist.count(False) != 0:
            # Run geogrid
            os.system(self.CMD_GEOGRID)
            # Sleep until the geogrid.log file exists
            while not os.path.exists(self.DIR_WRFOUT + 'geogrid.log'):
                time.sleep(1)
            # Begin geogrid simulation clock
            startTime = datetime.datetime.now()
            startTimeInt = int(time.time())
            if self.verbose:
                print('Starting Geogrid at: ' + str(startTime))
                sys.stdout.flush()
            geogrid_sim = self.runwrf_finish_check('geogrid')
            while geogrid_sim != 'complete':
                if geogrid_sim == 'failed':
                    print_last_3lines(self.DIR_WRFOUT + 'geogrid.log')
                    return False
                elif (int(time.time()) - startTimeInt) < 600:
                    time.sleep(2)
                    geogrid_sim = self.runwrf_finish_check('geogrid')
                elif disable_timeout is True:
                    time.sleep(2)
                    geogrid_sim = self.runwrf_finish_check('geogrid')
                else:
                    print('TimeoutError in run_wps: Geogrid took more than 10min to run... exiting.')
                    return False
            elapsed = datetime.datetime.now() - startTime
            if self.verbose:
                print('Geogrid ran in: ' + hf.strfdelta(elapsed))
        else:
            # Link the existing met_em files to the runwrf directory
            if self.verbose:
                print('Geogrid was run previously. Linking geogrid file(s)...')
            for file in geogridfiles:
                os.system(self.CMD_LN % (self.DIR_DATA_ROOT + 'data/domain/' + file, self.DIR_WRFOUT + '.'))

        # Run ungrib and metgrid if necessary; start by checking for required met_em files
        hrs = ['00', '03', '06', '09', '12', '15', '18', '21']
        # Determine the forecast duration
        forecast_duration = self.forecast_end - self.forecast_start
        # Build the list of required met_em files
        metfilelist = []
        for ii in range(forecast_duration.days + 1):
            day = self.forecast_start + datetime.timedelta(days=ii)
            for jj in range(1, self.n_domains + 1):
                domain = str(jj).zfill(2)
                if day == self.forecast_end:
                    metfilelist.append(f'met_em.d{domain}.{day.strftime("%Y-%m-%d")}_00:00:00.nc')
                else:
                    for hr in hrs:
                        metfilelist.append(f'met_em.d{domain}.{day.strftime("%Y-%m-%d")}_{hr}:00:00.nc')
        metfileexist = [os.path.exists(self.DIR_DATA + 'met_em/' + file) for file in metfilelist]
        if metfileexist.count(False) != 0:
            # Run ungrib and metgrid; start by linking the grib files
            sys.stdout.flush()
            os.system(self.CMD_LINK_GRIB)
            os.system(self.CMD_UNGMETG)
            # Sleep until the metgrid.log file exists
            while not os.path.exists(self.DIR_WRFOUT + 'metgrid.log'):
                time.sleep(1)
            # Begin geogrid simulation clock
            startTime = datetime.datetime.now()
            startTimeInt = int(time.time())
            if self.verbose:
                print('Starting Ungrib and Metgrid at: ' + str(startTime))
                sys.stdout.flush()
            metgrid_sim = self.runwrf_finish_check('metgrid')
            while metgrid_sim != 'complete':
                if metgrid_sim == 'failed':
                    print_last_3lines(self.DIR_WRFOUT + 'metgrid.log')
                    return False
                elif (int(time.time()) - startTimeInt) < 600:
                    time.sleep(2)
                    metgrid_sim = self.runwrf_finish_check('metgrid')
                elif disable_timeout is True:
                    time.sleep(2)
                    metgrid_sim = self.runwrf_finish_check('metgrid')
                else:
                    print('TimeoutError in run_wps: Ungrib and Metgrid took more than 10min to run... exiting.')
                    return False
            elapsed = datetime.datetime.now() - startTime
            if self.verbose:
                print('Ungrib and Metgrid ran in: ' + hf.strfdelta(elapsed))
        else:
            # Link the existing met_em files to the runwrf directory
            if self.verbose:
                print('Metgrid was run previously. Linking met_em files...')
            for file in metfilelist:
                os.system(self.CMD_LN % (self.DIR_DATA + 'met_em/' + file, self.DIR_WRFOUT + '.'))

        # Remove the temporary data directory after WPS has run
        hf.remove_dir(self.DIR_DATA_TMP)
        return True

    def run_real(self, disable_timeout=False):
        """
        Runs real.exe and checks to see if it was successful.

        :return: boolean (True/False)
            If runwrf_finish_check for real returns 'complete' ('failed'),
            this function returns True (False).

        """
        os.system(self.CMD_REAL)
        # Sleep until rsl.out.0000 file exists
        while not os.path.exists(self.DIR_WRFOUT + 'rsl.out.0000'):
            time.sleep(1)
        # Begin geogrid simulation clock
        startTime = datetime.datetime.now()
        startTimeInt = int(time.time())
        if self.verbose:
            print('Starting Real at: ' + str(startTime))
            sys.stdout.flush()
        real_sim = self.runwrf_finish_check('real')
        while real_sim != 'complete':
            if real_sim == 'failed':
                print_last_3lines(self.DIR_WRFOUT + 'rsl.out.0000')
                return False
            elif (int(time.time()) - startTimeInt) < 600:
                time.sleep(2)
                real_sim = self.runwrf_finish_check('real')
            elif disable_timeout is True:
                time.sleep(2)
                real_sim = self.runwrf_finish_check('real')
            else:
                print('TimeoutError in run_real: Real took more than 10min to run... exiting.')
                return False
        elapsed = datetime.datetime.now() - startTime
        if self.verbose:
            print('Real ran in: ' + hf.strfdelta(elapsed) + ' seconds')
        # Remove rsl.* files
        os.system(self.CMD_RM % (self.DIR_WRFOUT + 'rsl.*'))
        return True

    def run_wrf(self, disable_timeout=False, timeout_hours=8, save_wps_files=True):
        """
        Runs wrf.exe and checks to see if it was successful.

        :param disable_timeout: boolean (True/False)
            desribing if timeout of this function is allowed.
            Note that this parameter only breaks you out of this
            method - it does not kill WRF jobs that are already running.
        :param timeout_hours: integer
            defining the number of hours this method will wait before
            returning a failure (False) flag.
        :param save_wps_files: boolean (True/False)
            which tells the program whether or not to save and move the geo_em
            and met_em files to a permanent location. This is set to False by
            default because it only needs to be done once per domain, per
            boundary conditions, per date and is best done before
            optimize_wrf_physics is run.
        :return: boolean (True/False)
            If runwrf_finish_check for wrf returns 'complete' ('failed'),
            this function returns True (False).
        :return elapsed: string
            specifying the amount of time it took for the WRF simulation to run.

        """
        wrf_runtime = 3600 * timeout_hours
        os.system(self.CMD_WRF)
        # Sleep until rsl.out.0000 file exists
        while not os.path.exists(self.DIR_WRFOUT + 'rsl.out.0000'):
            time.sleep(5)
        # Begin wrf simulation clock
        startTime = datetime.datetime.now()
        startTimeInt = int(time.time())
        if self.verbose:
            print('Starting WRF at: ' + str(startTime))
            sys.stdout.flush()
        wrf_sim = self.runwrf_finish_check('wrf')
        while wrf_sim != 'complete':
            if wrf_sim == 'failed':
                print_last_3lines(self.DIR_WRFOUT + 'rsl.out.0000')
                elapsed = datetime.datetime.now() - startTime
                return False, hf.strfdelta(elapsed)
            elif (int(time.time()) - startTimeInt) < wrf_runtime:
                time.sleep(10)
                wrf_sim = self.runwrf_finish_check('wrf')
            elif disable_timeout is True:
                time.sleep(10)
                wrf_sim = self.runwrf_finish_check('wrf')
            else:
                print(f'TimeoutError in run_wrf at {datetime.datetime.now()}: '
                      f'WRF took more than {timeout_hours} hrs to run... exiting.')
                elapsed = datetime.datetime.now() - startTime
                return False, hf.strfdelta(elapsed)
        elapsed = datetime.datetime.now() - startTime
        if self.verbose:
            print('WRF finished running at: ' + str(datetime.datetime.now()))
            print('WRF ran in: ' + hf.strfdelta(elapsed))

        # Rename the wrfout files.
        # for n in range(1, self.n_domains + 1):
        #     os.system(self.CMD_MV % (self.DIR_WRFOUT + 'wrfout_d0' + str(n) + '_'
        #                              + self.forecast_start.strftime('%Y') + '-'
        #                              + self.forecast_start.strftime('%m') + '-'
        #                              + self.forecast_start.strftime('%d') + '_00:00:00',
        #                              self.DIR_WRFOUT + 'wrfout_d0' + str(n) + '.nc'))

        if save_wps_files:
            self.archive_wps()

        return True, hf.strfdelta(elapsed)

    def process_wrfout_data(self):
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
        wrfout_file = self.wrfout_file_name(domain=self.n_domains)
        datapath = self.DIR_WRFOUT + wrfout_file

        try:
            # Read in the wrfout file using the netCDF4.Dataset method
            netcdf_data = netCDF4.Dataset(datapath)
        except FileNotFoundError as e:
            # This means that WRF probably either failed or timed out.
            print(f'OptWRFWarning in process_wrfout_data: missing wrfout data file {datapath}\n'
                  f'WRF probably failed or timed out -- skipping this simulation.\n'
                  f'To force this to run, rename the wrfout file in {self.DIR_WRFOUT} to wrfout_d01.nc\n'
                  f'\t{e}')
            return False

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
                with xr.set_options(keep_attrs=True):
                    try:
                        met_data = xr.merge([met_data, var])
                    except ValueError as e:
                        print(f'OptWRFWarning in process_wrfout_data:\n'
                              f'there is something strange going on in: {self.DIR_WRFOUT};\n'
                              f'skipping this simulation\n'
                              f'\t{e}')
                        return False

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

        # Fix a bug in how wrfout data is read in -- attributes must be strings to be written to NetCDF
        # Unfortunately, this causes the attribute to be less useful for post processing...
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

        # Drop extra coordinates from the dataset
        met_data = xr.Dataset.reset_coords(met_data,
                                           ['wspd_wdir', 'XLONG', 'XLAT', 'XTIME', 'level'], drop=True)

        # Slice the last time from the wrfout data to remove duplicates
        met_data = met_data.isel(Time=slice(0, -1))

        # Write the processed data to a wrfout NetCDF file
        new_filename = self.DIR_WRFOUT + 'wrfout_processed_d01.nc'
        try:
            met_data.to_netcdf(path=new_filename)
        except KeyError as e:
            print(f'OptWRFWarning in process_wrfout_data\n{new_filename} not created;\n'
                  f'skipping this sumulation.'
                  f'\t{e}')
            return False

        return True

    def process_wrfout_flexible(self, query_variables, wrfout_file=None, 
                                domain=1, start=None, end=None, 
                                outfile_prefix='processed_', delete_original=False, 
                                save_file=False):
        """
        Processes any wrfout file, i.e., this function extracts specified query_variables from the
        specified wrfout file.

        This function makes use of the wrf module maintained by NCAR, which reproduces some of the funcionality
        of NCL in Python. Specifically, the _wrf2xarray() function uses the wrf.getvar() function to extract
        variables from the NetCDF file. All you need to do in this function is specify those variables either
            a) as they appear in the wrfout file, or
            b) by the wrf-python diagnostic variable name
            (https://wrf-python.readthedocs.io/en/latest/user_api/generated/wrf.getvar.html#wrf.getvar).
        Here's an example:

            query_variables = [
                'U',                # x-wind component
                'V',                # y-wind component
                'W',                # z-wind component
                'height_agl',       # Height above ground level
                'wspd',             # Wind speed
                'wdir',             # Wind direction
                'UST',              # U* IN SIMILARITY THEORY (friction velocity)
                'HFX_FORCE',        # SCM ideal surface sensible heat flux
                'PBLH',             # PBL Height
                'EL_PBL',           # Length scale from PBL
                'theta',            # Potential Temperature
                'theta_e',          # Equivalent Potential Temperature
                'tv',               # Virtual Temperature
            ]

        Some of these (U, V, W, UST, HFX_FORCE, PBLH, and EL_PBL) are the variables names in the wrfout file,
        while the others (height_agl, wspd, wdir, theta, theta_e, and tv) are variables calculated by wrf.getvar().
        Note that the variables available in the wrfout file will depend on your choice of physics parameterizations,
        while the ones available in wrf.getvar() do not.
        """
        if wrfout_file is None:
            # Determine the wrfout file name (i.e., based on the domain)
            wrfout_file = self.wrfout_file_name(domain=domain)

        # Absolute path to wrfout data file
        full_wrfout_path = self.DIR_WRFOUT + wrfout_file

        # Read in the wrfout file using the netCDF4.Dataset method (I think you can also do this with an xarray method)
        wrf_nc = netCDF4.Dataset(full_wrfout_path)

        # Create an xarray.Dataset from the wrf qurery_variables.
        wrf_ds = util._wrf2xarray(wrf_nc, query_variables)

        # Slice the wrfout data if start and end times ares specified
        if start and end is not None:
            wrf_ds = wrf_ds.sel(Time=slice(start, end))

        # Delete the original file if specified:
        if delete_original:
            os.system(self.CMD_RM % (full_wrfout_path))

        # Save the output file if specified.
        if save_file:
            # Write the processed data to a wrfout NetCDF file
            new_file_path = self.DIR_WRFOUT + outfile_prefix + wrfout_file
            wrf_ds.to_netcdf(path=new_file_path)

        return wrf_ds

    def process_era5_data(self):
        """
        Downloads ERA5 data from the Research Data Archive if it doesn't already exist in self.DIR_ERA5_ROOT,
        and processes the data -- reduces the size of the ERA5 files using ncks and
        calculates the wind power density at 100m and the GHI -- and writes
        these variables to a montly ERA5 NetCDF data file named ERA5_EastUS_WPD-GHI_YYYY-MM.nc.

        Unfortunately, the ERA5 surface solar radiation downward (ssrd) data is provided in incredibly
        inconvenient temporal windows, so to build a montly file, we must download three ssrd files
        and two wind files (U and V wind components). For example, the following filelist would be
        built for January 2011:

        filelist = ['e5.oper.an.sfc/201101/
                        e5.oper.an.sfc.228_246_100u.ll025sc.2011010100_2011013123.nc',
                    'e5.oper.an.sfc/201101/
                        e5.oper.an.sfc.228_247_100v.ll025sc.2011010100_2011013123.nc',
                    'e5.oper.fc.sfc.accumu/201012/
                        e5.oper.fc.sfc.accumu.128_169_ssrd.ll025sc.2010121606_2011010106.nc',
                    'e5.oper.fc.sfc.accumu/201101/
                        e5.oper.fc.sfc.accumu.128_169_ssrd.ll025sc.2011010106_2011011606.nc',
                    'e5.oper.fc.sfc.accumu/201101/
                        e5.oper.fc.sfc.accumu.128_169_ssrd.ll025sc.2011011606_2011020106.nc']

        which means there are three separate directories on RDA that files must be downloaded from.

        ***NOTE that this method currently only supports simulations within a single month
        i.e., YYYY-MM-01 00:00:00 - YYYY-MM-<end day> 23:00:00. Otherwise, wrf_era5_diff()
        will fail. Times are in UTC.

        ***NOTE that this method does not currently support running on Cheyenne;
        it's about halfway there...

        """
        # Process the ERA5 data file unless it already exists in wrfsim.DIR_ERA5_ROOT
        processed_era_file = self.DIR_ERA5_ROOT + 'ERA5_EastUS_WPD-GHI_' \
                             + self.forecast_start.strftime('%Y') + '-' \
                             + self.forecast_start.strftime('%m') + '.nc'
        if not os.path.exists(processed_era_file):
            if self.verbose:
                print(f'Processing ERA5 data for {self.forecast_start.strftime("%m")} '
                      f'{self.forecast_start.strftime("%Y")}...')
            # Define some convenient file suffixes
            last_month = self.forecast_start + dateutil.relativedelta.relativedelta(months=-1)
            next_month = self.forecast_start + dateutil.relativedelta.relativedelta(months=+1)
            year_mo = self.forecast_start.strftime('%Y') + self.forecast_start.strftime('%m')
            # If we are running a simulation in January, the year_lastmo file suffix will have a different year
            if last_month.month == 12:
                last_year = self.forecast_start + dateutil.relativedelta.relativedelta(years=-1)
                year_lastmo = last_year.strftime('%Y') + last_month.strftime('%m')
            else:
                year_lastmo = self.forecast_start.strftime('%Y') + last_month.strftime('%m')
            # If we are running a simulation in December, the year_nextmo file suffix will have a different year
            if next_month.month == 1:
                next_year = self.forecast_start + dateutil.relativedelta.relativedelta(years=+1)
                year_nextmo = next_year.strftime('%Y') + next_month.strftime('%m')
            else:
                year_nextmo = self.forecast_start.strftime('%Y') + next_month.strftime('%m')
            # Determine the last day of the month
            mo_len = calendar.monthrange(self.forecast_start.year, self.forecast_start.month)[1]
            # Finally, create all four necessary file date suffixes
            date_suffix_01_end = year_mo + '0100_' + year_mo + str(mo_len) + '23.nc'
            date_suffix_lastmo_16_01 = year_lastmo + '1606_' + year_mo + '0106.nc'
            date_suffix_01_16 = year_mo + '0106_' + year_mo + '1606.nc'
            date_suffix_16_01 = year_mo + '1606_' + year_nextmo + '0106.nc'

            # Download ERA5 data from RDA if it does not already exist in the expected place
            if self.on_cheyenne:
                self.DIR_ERA5_ROOT = '/gpfs/fs1/collections/rda/data/ds633.0/'
                DATA_ROOT1 = self.DIR_ERA5_ROOT + 'e5.oper.an.sfc/' + year_mo + '/'
                DATA_ROOT2 = 'e5.oper.fc.sfc.accumu/' + year_lastmo + '/'
                DATA_ROOT3 = self.DIR_ERA5_ROOT + 'e5.oper.fc.sfc.accumu/' + year_mo + '/'
            else:
                # Define the expected absolute paths to ERA data files
                erafile_100u = self.DIR_ERA5_ROOT + 'EastUS_e5.oper.an.sfc.228_246_100u.ll025sc.' + date_suffix_01_end
                erafile_100v = self.DIR_ERA5_ROOT + 'EastUS_e5.oper.an.sfc.228_247_100v.ll025sc.' + date_suffix_01_end
                erafile_ssrd1 = self.DIR_ERA5_ROOT + 'EastUS_e5.oper.fc.sfc.accumu.128_169_ssrd.ll025sc.' + date_suffix_lastmo_16_01
                erafile_ssrd2 = self.DIR_ERA5_ROOT + 'EastUS_e5.oper.fc.sfc.accumu.128_169_ssrd.ll025sc.' + date_suffix_01_16
                erafile_ssrd3 = self.DIR_ERA5_ROOT + 'EastUS_e5.oper.fc.sfc.accumu.128_169_ssrd.ll025sc.' + date_suffix_16_01
                local_filelist = [erafile_100u, erafile_100v, erafile_ssrd1, erafile_ssrd2, erafile_ssrd3]
                local_filenames = ['EastUS_e5.oper.an.sfc.228_246_100u.ll025sc.' + date_suffix_01_end,
                                   'EastUS_e5.oper.an.sfc.228_247_100v.ll025sc.' + date_suffix_01_end,
                                   'EastUS_e5.oper.fc.sfc.accumu.128_169_ssrd.ll025sc.' + date_suffix_lastmo_16_01,
                                   'EastUS_e5.oper.fc.sfc.accumu.128_169_ssrd.ll025sc.' + date_suffix_01_16,
                                   'EastUS_e5.oper.fc.sfc.accumu.128_169_ssrd.ll025sc.' + date_suffix_16_01]

                # Download data from RDA if necessary
                if [os.path.exists(file) for file in local_filelist].count(False) != 0:
                    # Define the rda file prefixes for the wind data
                    rda_datpfxs_sfc = ['e5.oper.an.sfc.228_246_100u.ll025sc.',
                                       'e5.oper.an.sfc.228_247_100v.ll025sc.']
                    # Define the rda file prefix for the ssrfd data
                    rda_datpfxs_sfc_accumu = ['e5.oper.fc.sfc.accumu.128_169_ssrd.ll025sc.']

                    # Make the ERA5 data directory if it does not exist
                    if not os.path.exists(self.DIR_ERA5_ROOT):
                        os.makedirs(self.DIR_ERA5_ROOT)

                    # Define paths to the required data on the RDA site
                    dspath = 'http://rda.ucar.edu/data/ds633.0/'
                    DATA_ROOT1 = 'e5.oper.an.sfc/' + year_mo + '/'
                    DATA_ROOT2 = 'e5.oper.fc.sfc.accumu/' + year_lastmo + '/'
                    DATA_ROOT3 = 'e5.oper.fc.sfc.accumu/' + year_mo + '/'

                    # Build the file list to be downloaded from the RDA
                    filelist = []
                    rda_filelist = []
                    for rda_datpfx in rda_datpfxs_sfc:
                        filelist.append(DATA_ROOT1 + rda_datpfx + date_suffix_01_end)
                        rda_filelist.append(rda_datpfx + date_suffix_01_end)

                    for rda_datpfx in rda_datpfxs_sfc_accumu:
                        filelist.append(DATA_ROOT2 + rda_datpfx + date_suffix_lastmo_16_01)
                        filelist.append(DATA_ROOT3 + rda_datpfx + date_suffix_01_16)
                        filelist.append(DATA_ROOT3 + rda_datpfx + date_suffix_16_01)
                        rda_filelist.append(rda_datpfx + date_suffix_lastmo_16_01)
                        rda_filelist.append(rda_datpfx + date_suffix_01_16)
                        rda_filelist.append(rda_datpfx + date_suffix_16_01)
                    if self.verbose:
                        print(filelist)

                    # Download the data from the RDA (requires password and connection)
                    success = rda_download(filelist, dspath)
                    if not success:
                        print(f'ERA5 benchmark data was not successfully downloaded from RDA.')
                        raise RuntimeError

                    # Run ncks to reduce the size of the files
                    for rda_file, local_file in zip(rda_filelist, local_filenames):
                        CMD_REDUCE = 'ncks -d longitude,264.,296. -d latitude,28.,52. %s %s' % \
                                     (rda_file, local_file)
                        if self.verbose:
                            print(f'Running the following from the command line:\n{CMD_REDUCE}')
                            os.system(CMD_REDUCE)

                    # Move the files into the ERA5 data directory
                    for file in local_filenames:
                        cmd = self.CMD_MV % (file, self.DIR_ERA5_ROOT)
                        os.system(cmd)

                    # Remove the raw ERA5 files
                    for file in rda_filelist:
                        cmd = self.CMD_RM % file
                        os.system(cmd)

            # Read in the wind files using the xarray open_dataset method.
            # Note that the context managers help with tear down and
            # hopefully keeps other threads from getting locked out of the ERA5 files.
            with xr.open_dataset(erafile_100u) as ds1:
                era_100u = ds1.load()
            with xr.open_dataset(erafile_100v) as ds2:
                era_100v = ds2.load()
            era_100wind = xr.merge([era_100u, era_100v])
            era_100wind = era_100wind.drop('utc_date')
            era_100wind = era_100wind.rename({'time': 'Time'})

            # Read in the ssrd files using the xarray open_dataset method
            with xr.open_dataset(erafile_ssrd1) as ds3:
                era_ssrd1 = ds3.load()
            with xr.open_dataset(erafile_ssrd2) as ds4:
                era_ssrd2 = ds4.load()
            with xr.open_dataset(erafile_ssrd3) as ds5:
                era_ssrd3 = ds5.load()
            era_ssrd_raw = xr.concat([era_ssrd1, era_ssrd2, era_ssrd3], 'forecast_initial_time')

            # Calculate the 100m wind speed
            wind_speed100 = np.sqrt(era_100wind['VAR_100U'] ** 2 + era_100wind['VAR_100V'] ** 2)
            era_100wind['wspd_100'] = wind_speed100

            # Calculate wind power density (W * m -2)
            air_density = 1000
            wpd = 0.5 * air_density * wind_speed100 ** 3
            era_100wind['WPD'] = wpd

            # Format the era_ssrd_raw dataset
            era_ssrd = era_ssrd_raw.drop_dims(['forecast_initial_time', 'forecast_hour'])

            first = True
            for timestr in era_ssrd_raw.forecast_initial_time:
                ssrd_slice = era_ssrd_raw.sel(forecast_initial_time=timestr.dt.strftime('%Y-%m-%d %H'))
                ssrd_slice = ssrd_slice.assign_coords(forecast_hour=pd.date_range(start=timestr.values, freq='H',
                                                                                  periods=(
                                                                                      len(ssrd_slice.forecast_hour))))
                ssrd_slice = ssrd_slice.rename({'forecast_hour': 'Time'})
                ssrd_slice = ssrd_slice.reset_coords('forecast_initial_time', drop=True)
                if first is True:
                    era_ssrd['SSRD'] = ssrd_slice['SSRD']
                    first = False
                else:
                    era_ssrd = xr.concat([era_ssrd, ssrd_slice], 'Time')
            era_ssrd = era_ssrd.drop('utc_date')

            # Convert SSRD to GHI
            ghi = era_ssrd.SSRD / 3600
            era_ssrd['GHI'] = ghi

            # Combine the wind power density and ghi datasets
            era_out = xr.merge([era_100wind, era_ssrd])

            # Slice the dataset to only one month (UTC)
            first_hour = self.forecast_start.strftime('%Y') + '-' + self.forecast_start.strftime('%m') \
                         + '-01 00:00:00'
            last_hour = self.forecast_start.strftime('%Y') + '-' + self.forecast_start.strftime('%m') \
                        + '-' + str(mo_len) + ' 23:00:00'
            era_out = era_out.sel(Time=slice(first_hour, last_hour))

            # Write the processed data back to a NetCDF file
            era_out.to_netcdf(path=processed_era_file)

    def wrf_era5_diff(self, method='ncl'):
        """
        Computes the difference between the wrf simulation and ERA5
        reanalysis using NCL, xESMF, or PyResample.

        This function calls sub-functions that read the previously-processed ERA5 and wrfout files,
        regrids the wrfout global horizontal irradiance (GHI) and wind
        power density (WPD) to match that of the ERA5 data, and then computes
        the difference across the entire d01 WRF domain for every time period.

        :param method: str
            Identifying the regridding method ('ncl', 'xesmf', and 'pyresample' are supported).
        :return error: list
            Sum of the absolute error accumulated in each grid cell
            during all time periods in the WRF simulation.

        """

        # Create a wrapper function to calculate the error for the non-NCL methods
        def calculate_error_wrapper(wrfdat, eradat):
            # Calculate the error between the WRF simulation and the ERA5 reanalysis
            wrfdat = wrf_era5_error(wrfdat, eradat)
            # Calculate the total error
            return [0, float(wrfdat['total_ghi_error'].sum().values), float(wrfdat['total_wpd_error'].sum().values)]

        # Regrid WRF to the ERA5 grid using NCL, xesmf, or pyresample
        input_year = self.forecast_start.strftime('%Y')
        input_month = self.forecast_start.strftime('%m')
        input_day = self.forecast_start.strftime('%d')
        if method == 'ncl':
            error = wrf_era5_regrid_ncl(input_year, input_month, input_day, self.paramstr,
                                        wrfdir=self.DIR_WRFOUT, eradir=self.DIR_ERA5_ROOT)
        elif method == 'xesmf':
            wrfdata, eradata = wrf_era5_regrid_xesmf(input_year, input_month,
                                                     wrfdir=self.DIR_WRFOUT, eradir=self.DIR_ERA5_ROOT)
            error = calculate_error_wrapper(wrfdata, eradata)
        elif method == 'pyresample':
            wrfdata, eradata = wrf_era5_regrid_pyresample(input_year, input_month,
                                                          wrfdir=self.DIR_WRFOUT, eradir=self.DIR_ERA5_ROOT)
            error = calculate_error_wrapper(wrfdata, eradata)
        else:
            print(f'Invalid regridding method: {method}. Only xesmf and pyresample are currently supported.')
            raise NameError

        if self.verbose:
            print(f'!!! Physics options set {self.paramstr} has total\n'
                  f'\tghi error {error[1]} and wpd error {error[2]} kW m-2 day-1')

        return error

    def archive_wps(self):
        # Move the geo_em file(s) to a permanent location
        os.system(self.CMD_MV % (self.DIR_WRFOUT + 'geo_em.*', self.DIR_DATA_ROOT + 'data/domain/'))

        # Move the met_em files to a permanent location
        os.system(self.CMD_MV % (self.DIR_WRFOUT + 'met_em.*', self.DIR_DATA + 'met_em/'))

    def wrfout_file_name(self, domain=1):
        """
        Returns the full path to the wrfout file based on the domain. 
        """

        if domain == 1:
            wrfout_file = self.FILE_WRFOUT_d01
        elif domain == 2:
            wrfout_file = self.FILE_WRFOUT_d02
        elif domain == 3:
            wrfout_file = self.FILE_WRFOUT_d03
        else:
            print(f'Domain {domain} is not a valid option. Choose 1 - 3')
            raise ValueError
        
        return wrfout_file


def run_all(wrf_sim, disable_timeout=True, verbose=False, save_wps_files=False):
    """
    Using the input physics parameters, date, boundary condition, and domain data,
    this function runs the WRF model.

    :param wrf_sim: `WRFModel` object
        containing all the necessary information for running the WRF model.
    :param disable_timeout: boolean (default = False)
        telling runwrf if subprogram timeouts are allowed or not.
    :param verbose: boolean (default = False)
        instructing the program to print everything or just key information to the screen.
    :return success, runtime: bool, str
        indicating if the simulation finished running successfully and how long it took.
    """
    if verbose:
        print('- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -')
        print(f'\nRunning: {wrf_sim.param_ids} from {wrf_sim.forecast_start} to {wrf_sim.forecast_end}')

    # Check to see if WRFModel instance exists; if not, run the WRF model.
    wrfout_file_path = wrf_sim.DIR_WRFOUT + 'wrfout_d01.nc'
    orig_wrfout_file_path = wrf_sim.DIR_WRFOUT + 'wrfout_d01_' \
                       + wrf_sim.forecast_start.strftime('%Y') + '-' \
                       + wrf_sim.forecast_start.strftime('%m') + '-' \
                       + wrf_sim.forecast_start.strftime('%d') + '_00:00:00'
    if [os.path.exists(file) for file in [wrfout_file_path, orig_wrfout_file_path]].count(True) == 0:
        # Next, get boundary condition data for the simulation
        # ERA is the only supported data type right now.
        vtable_sfx = wrf_sim.get_bc_data()

        # Setup the working directory to run the simulation
        success = wrf_sim.wrfdir_setup(vtable_sfx)

        # Prepare the namelists
        if success:
            success = wrf_sim.prepare_namelists()

        # Run WPS
        if success:
            success = wrf_sim.run_wps(disable_timeout)
            if verbose:
                print(f'WPS ran successfully? {success}')

        # Run REAL
        if success:
            success = wrf_sim.run_real(disable_timeout)
            if verbose:
                print(f'Real ran successfully? {success}')

        # RUN WRF
        if success:
            success, runtime = wrf_sim.run_wrf(disable_timeout, save_wps_files=save_wps_files)
            if verbose:
                print(f'WRF ran successfully? {success}')
        else:
            runtime = '00h 00m 00s'
    else:
        success = True
        runtime = '00h 00m 00s'
    
    return success, runtime


def run_multiple(wrf_sims, disable_timeout=True, verbose=False, save_wps_files=False):
    """
    Runs the simulations specified by the wrf_sims argument.

    :param wrf_sim: `WRFModel` object
        containing all the necessary information for running the WRF model.
    :param disable_timeout: boolean (default = False)
        telling runwrf if subprogram timeouts are allowed or not.
    :param verbose: boolean (default = False)
        instructing the program to print everything or just key information to the screen.

    """
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Start running all the fitness functions that need to be calculated
        try:
            sim_threads = []
            for sim in wrf_sims:
                # Execute a new thread to run the WRF simulation
                sim_threads.append(executor.submit(run_all, sim, disable_timeout=disable_timeout,
                                   verbose=verbose, save_wps_files=save_wps_files))

            # Get the results from the thread pool executor
            success_matrix = []
            runtime_matrix = []
            for thread in sim_threads:
                try:
                    success_value, runtime_value = thread.result()
                except AttributeError:
                    success_value = None
                    runtime_value = None
                success_matrix.append(success_value)
                runtime_matrix.append(runtime_value)

        except KeyboardInterrupt:
            # cancel() returns False if it's already done and True if was able to cancel it;
            # we don't need that return value, so we ignore it with the underscore.
            for future in sim_threads:
                _ = future.cancel()
    for ii in range(0, len(success_matrix)):
        print(f'Success: {success_matrix[ii]}, Runtime: {runtime_matrix[ii]}')
