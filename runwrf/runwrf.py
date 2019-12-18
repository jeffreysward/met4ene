"""
Overview: This module provides methods which support running WRF withing other scripts.
The following functions are available.

- read_last_line()

- read_2nd2_last_line()

- runwrf_finish_check()

- rda_download()

- check_file_status()

- determine_computer()

- dirsandcommand_aliai()

- get_bc_data()

- wrfdir_setup()

- prepare_namelists()

- run_wps()

- run_real()

- run_wrf()

- wrf_era5_diff()
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
Known Issues/Wishlist:
- The section of code that downloads ERA5 data is WRONG! It does not yet carry out
the ncks step; I did it manually previously and haven't added it into this module yet.
- There should be a better way (e.g., make a Class) to set the directories and command
aliai than to have the same function called in every other function.
- I'm unhappy with the output to screen from rda_download(). Perhaps edit that and
check_file_status() as well.

"""

import sys
import os
import requests
import time
import datetime
import yaml
import linuxhelper as lh
from wrfparams import ids2str


class WRFModel:
    """
    This class provides a framework for running the WRF model
    """

    def __init__(self, param_ids, start_date, end_date, bc_data='ERA',
                 n_domains=1, template_dir=None, setup_yaml='dirpath.yml'):
        self.param_ids = param_ids
        self.start_date = start_date
        self.end_date = end_date
        self.bc_data = bc_data
        self.n_domains = n_domains
        self.template_dir = template_dir

        # Format the forecast start/end and determine the total time.
        self.forecast_start = datetime.datetime.strptime(self.start_date, '%b %d %Y')
        self.forecast_end = datetime.datetime.strptime(self.end_date, '%b %d %Y')
        self.delt = self.forecast_end - self.forecast_start
        print('Forecast starting on: {}'.format(self.forecast_start))
        print('Forecast ending on: {}'.format(self.forecast_end))
        self.paramstr = ids2str(self.param_ids)

        # Determine which computer you are running on
        # to set directories and command aliai
        on_aws, on_cheyenne, on_magma = determine_computer()
        self.on_aws = on_aws
        self.on_cheyenne = on_cheyenne
        self.on_magma = on_magma

        # Set working and WRF model directory names
        with open(setup_yaml, 'r') as dirpath_file:
            try:
                dirs = yaml.safe_load(dirpath_file)
            except yaml.YAMLError as exc:
                print(exc)
        dirpaths = dirs.get('directory_paths')
        self.DIR_WRF_ROOT = dirpaths.get('DIR_WRF_ROOT')
        self.DIR_WPS = self.DIR_WRF_ROOT + 'WPS/'
        self.DIR_WRF = self.DIR_WRF_ROOT + 'WRF/'
        self.DIR_DATA_ROOT = dirpaths.get('DIR_DATA_ROOT')
        self.DIR_WPS_GEOG = self.DIR_DATA_ROOT + 'WPS_GEOG/'
        self.DIR_DATA = self.DIR_DATA_ROOT + 'data/' + str(self.bc_data) + '/'
        self.DIR_MET4ENE = dirpaths.get('DIR_MET4ENE')
        self.DIR_WRFOUT = self.DIR_MET4ENE + 'wrfout/ARW/%s_' % \
                          (self.forecast_start.strftime('%Y-%m-%d')) + self.paramstr + '/'
        self.DIR_RUNWRF = self.DIR_MET4ENE + 'runwrf/'

        # if self.on_cheyenne:
        #     self.DIR_WRF_ROOT = '/glade/u/home/wrfhelp/PRE_COMPILED_CODE/%s/'
        #     self.DIR_WPS = self.DIR_WRF_ROOT % 'WPSV4.1_intel_serial_large-file'
        #     self.DIR_WRF = self.DIR_WRF_ROOT % 'WRFV4.1_intel_dmpar'
        #     self.DIR_WPS_GEOG = '/glade/u/home/wrfhelp/WPS_GEOG/'
        #     self.DIR_DATA = '/glade/scratch/sward/data/' + str(self.bc_data) + '/%s_' % \
        #                     (self.forecast_start.strftime('%Y-%m-%d')) + self.paramstr + '/'
        #     self.DIR_WRFOUT = '/glade/scratch/sward/met4ene/wrfout/%s_' + self.paramstr % \
        #                       (self.forecast_start.strftime('%Y-%m-%d')) + self.paramstr + '/'
        #     self.DIR_RUNWRF = '/glade/scratch/sward/met4ene/runwrf/'
        # elif self.on_aws:
        #     self.DIR_WRF_ROOT = '/home/ec2-user/environment/Build_WRF/'
        #     self.DIR_WPS = '/home/ec2-user/environment/Build_WRF/WPS/'
        #     self.DIR_WRF = '/home/ec2-user/environment/Build_WRF/WRF/'
        #     self.DIR_WPS_GEOG = '/home/ec2-user/environment/data/WPS_GEOG'
        #     self.DIR_DATA = '/home/ec2-user/environment/data/' + str(self.bc_data) + '/%s_' % \
        #                     (self.forecast_start.strftime('%Y-%m-%d')) + self.paramstr + '/'
        #     self.DIR_WRFOUT = '/home/ec2-user/environment/met4ene/wrfout/ARW/%s_' % \
        #                       (self.forecast_start.strftime('%Y-%m-%d')) + self.paramstr + '/'
        #     self.DIR_RUNWRF = '/home/ec2-user/environment/met4ene/runwrf/'
        # elif self.on_magma:
        #     self.DIR_WRF_ROOT = '/home/jas983/models/wrf/'
        #     self.DIR_WPS = '/home/jas983/models/wrf/WPS/'
        #     self.DIR_WRF = '/home/jas983/models/wrf/WRF/'
        #     self.DIR_WPS_GEOG = '/share/mzhang/jas983/wrf_data/WPS_GEOG'
        #     self.DIR_DATA = '/share/mzhang/jas983/wrf_data/data/' + str(self.bc_data) + '/'
        #     self.DIR_WRFOUT = '/share/mzhang/jas983/wrf_data/met4ene/wrfout/ARW/%s_' % \
        #                       (self.forecast_start.strftime('%Y-%m-%d')) + self.paramstr + '/'
        #     self.DIR_RUNWRF = '/share/mzhang/jas983/wrf_data/met4ene/runwrf/'
        # else:
        #     self.DIR_WRF_ROOT = '/home/jas983/models/wrf/'
        #     self.DIR_WPS = '/home/jas983/models/wrf/WPS/'
        #     self.DIR_WRF = '/home/jas983/models/wrf/WRF/'
        #     self.DIR_WPS_GEOG = '/share/mzhang/jas983/wrf_data/WPS_GEOG'
        #     self.DIR_DATA = '/share/mzhang/jas983/wrf_data/data/' + str(self.bc_data) + '/'
        #     self.DIR_WRFOUT = '/share/mzhang/jas983/wrf_data/met4ene/wrfout/ARW/%s_' % \
        #                       (self.forecast_start.strftime('%Y-%m-%d')) + self.paramstr + '/'
        #     self.DIR_RUNWRF = '/share/mzhang/jas983/wrf_data/met4ene/runwrf/'

        # Define a directory containing:
        # a) namelist.wps and namelist.input templates
        # b) batch submission template csh scripts for running geogrid, ungrib & metgrid, and real & wrf.
        if self.template_dir is not None:
            self.DIR_TEMPLATES = self.template_dir + '/'
        else:
            if self.on_cheyenne:
                self.DIR_TEMPLATES = '/glade/scratch/sward/met4ene/templates/ncartemplates/'
            elif self.on_aws:
                self.DIR_TEMPLATES = '/home/ec2-user/environment/met4ene/templates/awstemplates/'
            else:
                self.DIR_TEMPLATES = '/share/mzhang/jas983/wrf_data/met4ene/templates/magma2templates/'

        # Define linux command aliai
        self.CMD_LN = 'ln -sf %s %s'
        self.CMD_CP = 'cp %s %s'
        self.CMD_MV = 'mv %s %s'
        self.CMD_CHMOD = 'chmod -R %s %s'
        self.CMD_LINK_GRIB = './link_grib.csh ' + self.DIR_DATA + '* ' + self.DIR_WRFOUT
        if self.on_cheyenne:
            self.CMD_GEOGRID = 'qsub ' + self.DIR_WRFOUT + 'template_rungeogrid.csh'
            self.CMD_UNGMETG = 'qsub ' + self.DIR_WRFOUT + 'template_runungmetg.csh'
            self.CMD_REAL = 'qsub ' + self.DIR_WRFOUT + 'template_runreal.csh'
            self.CMD_WRF = 'qsub ' + self.DIR_WRFOUT + 'template_runwrf.csh'
        elif self.on_aws:
            self.CMD_GEOGRID = './template_rungeogrid.csh'
            self.CMD_UNGMETG = './template_runungmetg.csh'
            self.CMD_REAL = './template_runreal.csh'
            self.CMD_WRF = './template_runwrf.csh'
        else:
            self.CMD_GEOGRID = 'sbatch ' + self.DIR_WRFOUT + 'template_rungeogrid.csh ' + self.DIR_WRFOUT
            self.CMD_UNGMETG = 'sbatch ' + self.DIR_WRFOUT + 'template_runungmetg.csh ' + self.DIR_WRFOUT
            self.CMD_REAL = 'sbatch ' + self.DIR_WRFOUT + 'template_runreal.csh ' + self.DIR_WRFOUT
            self.CMD_WRF = 'sbatch ' + self.DIR_WRFOUT + 'template_runwrf.csh ' + self.DIR_WRFOUT

    def set_directory_paths(self, in_yaml='dirpath.yml'):
        """
        Called within the __init__ method to set the directory paths
        based upon the input yaml file.

        :param in_yaml:
        :return:
        """


    def runwrf_finish_check(self, program):
        """
        Check if a specified WRF subprogram has finished running.

        :param program:
        :return:
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
        elif program == 'wrf':
            msg = read_last_line(self.DIR_WRFOUT + 'rsl.out.0000')
            complete = 'SUCCESS COMPLETE WRF' in msg
            failed = '-------------------------------------------' in msg
        else:
            complete = False
            failed = False
        if failed:
            print(f'ERROR: {program} has failed. Last message was:\n{msg}')
            return 'failed'
        elif complete:
            return 'complete'
        else:
            return 'running'

    def get_bc_data(self):
        """
        Download boundry condition data from the RDA
        if it does not already exist in the expected data directory.

        :return:
        """
        if self.bc_data == 'ERA':
            if self.on_cheyenne:
                DATA_ROOT1 = '/gpfs/fs1/collections/rda/data/ds627.0/ei.oper.an.pl/'
                DATA_ROOT1 = DATA_ROOT1 + self.forecast_start.strftime('%Y') + self.forecast_start.strftime('%m') + '/'
                DATA_ROOT2 = '/gpfs/fs1/collections/rda/data/ds627.0/ei.oper.an.sfc/'
                DATA_ROOT2 = DATA_ROOT2 + self.forecast_start.strftime('%Y') + self.forecast_start.strftime('%m') + '/'
            else:
                # The following define paths to the required data on the RDA site
                dspath = 'http://rda.ucar.edu/data/ds627.0/'
                DATA_ROOT1 = 'ei.oper.an.pl/' + self.forecast_start.strftime('%Y') \
                             + self.forecast_start.strftime('%m') + '/'
                DATA_ROOT2 = 'ei.oper.an.sfc/' + self.forecast_start.strftime('%Y') \
                             + self.forecast_start.strftime('%m') + '/'
            datpfx1 = 'ei.oper.an.pl.regn128sc.'
            datpfx2 = 'ei.oper.an.pl.regn128uv.'
            datpfx3 = 'ei.oper.an.sfc.regn128sc.'
            vtable_sfx = 'ERA-interim.pl'
        else:
            vtable_sfx = self.bc_data
        print('Using {} data for boundary condidions'.format(self.bc_data))
        print('The corresponding Vtable is: {}\n'.format(vtable_sfx))

        # If no data directory exists, create one
        if not os.path.exists(self.DIR_DATA):
            os.makedirs(self.DIR_DATA, 0o755)
        i = int(self.forecast_start.day)
        n = int(self.forecast_start.day) + int(self.delt.days)
        if self.on_cheyenne:
            # Copy desired data files from RDA
            # THIS ONLY WORKS IF YOU WANT TO RUN WITHIN A SINGLE MONTH!
            while i <= n:
                cmd = self.CMD_CP % (DATA_ROOT1 + datpfx1 + self.forecast_start.strftime('%Y')
                                + self.forecast_start.strftime('%m') + str(i) + '*', self.DIR_DATA)
                cmd = cmd + '; ' + self.CMD_CP % (DATA_ROOT1 + datpfx2 + self.forecast_start.strftime('%Y')
                                             + self.forecast_start.strftime('%m') + str(i) + '*', self.DIR_DATA)
                cmd = cmd + '; ' + self.CMD_CP % (DATA_ROOT2 + datpfx3 + self.forecast_start.strftime('%Y')
                                             + self.forecast_start.strftime('%m') + str(i) + '*', self.DIR_DATA)
                os.system(cmd)
                i += 1
        else:
            # Build the file list required for the WRF run.
            hrs = ['00', '06', '12', '18']
            filelist = []
            file_check = []
            while i <= n:
                for hr in hrs:
                    filelist.append(DATA_ROOT1 + datpfx1 + self.forecast_start.strftime('%Y')
                                    + self.forecast_start.strftime('%m') + str(i) + hr)
                    filelist.append(DATA_ROOT1 + datpfx2 + self.forecast_start.strftime('%Y')
                                    + self.forecast_start.strftime('%m') + str(i) + hr)
                    filelist.append(DATA_ROOT2 + datpfx3 + self.forecast_start.strftime('%Y')
                                    + self.forecast_start.strftime('%m') + str(i) + hr)
                    file_check.append(datpfx1 + self.forecast_start.strftime('%Y')
                                      + self.forecast_start.strftime('%m') + str(i) + hr)
                    file_check.append(datpfx2 + self.forecast_start.strftime('%Y')
                                      + self.forecast_start.strftime('%m') + str(i) + hr)
                    file_check.append(datpfx3 + self.forecast_start.strftime('%Y')
                                      + self.forecast_start.strftime('%m') + str(i) + hr)
                i += 1

            # Check to see if all these files already exist in the data directory
            data_exists = []
            for data_file in file_check:
                data_exists.append(os.path.exists(self.DIR_DATA + data_file))
            if data_exists.count(True) is len(file_check):
                print('Boundary condition data was previously downloaded from RDA.')
                return vtable_sfx
            else:
                # Download the data from the RDA
                rda_download(filelist, dspath)
                # Move the data files to the data directory
                cmd = self.CMD_MV % (datpfx1 + '*', self.DIR_DATA)
                cmd = cmd + '; ' + self.CMD_MV % (datpfx2 + '*', self.DIR_DATA)
                cmd = cmd + '; ' + self.CMD_MV % (datpfx3 + '*', self.DIR_DATA)
                os.system(cmd)
        return vtable_sfx

    def wrfdir_setup(self, vtable_sfx):
        """
        Sets up the WRF run directory by copying scripts, data files, and executables.

        :param vtable_sfx:
        :return:
        """

        # Clean potential old simulation dir, remake the dir, and enter it.
        lh.remove_dir(self.DIR_WRFOUT)
        os.makedirs(self.DIR_WRFOUT, 0o755)

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
        print(f'Your WRFOUT directory is:\n{self.DIR_WRFOUT}')

        # Copy over namelists and submission scripts
        if self.on_cheyenne:
            cmd = self.CMD_CP % (self.DIR_TEMPLATES + 'template_rungeogrid.csh', self.DIR_WRFOUT)
            cmd = cmd + '; ' + self.CMD_CP % (self.DIR_TEMPLATES + 'template_runungmetg.csh', self.DIR_WRFOUT)
            cmd = cmd + '; ' + self.CMD_CP % (self.DIR_TEMPLATES + 'template_runreal.csh', self.DIR_WRFOUT)
            cmd = cmd + '; ' + self.CMD_CP % (self.DIR_TEMPLATES + 'template_runwrf.csh', self.DIR_WRFOUT)
        else:
            cmd = self.CMD_CP % (self.DIR_TEMPLATES + '*', self.DIR_WRFOUT)
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

    def prepare_namelists(self):
        """
        Writes WPS and WRF namelist files.

        :return:
        """

        def read_namelist(namelist_file):
            with open(self.DIR_WRFOUT + namelist_file, 'r') as namelist:
                NAMELIST = namelist.read()
            return NAMELIST

        # Try to open WPS and WRF namelists as readonly,
        # and print an error & exit if you cannot.
        try:
            NAMELIST_WPS = read_namelist('namelist.wps')
            NAMELIST_WRF = read_namelist('namelist.input')
        except IOError as e:
            print(e.errno)
            print(e)
            exit()

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
        print('Done writing WPS namelist')

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
        wrf_physics = wrf_physics + str(self.param_ids[5]) + ', 0, 0,'
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
        print('Done writing WRF namelist\n')

    def run_wps(self):
        """
        Runs the WRF preprocessing executables and confirms thier success.

        :return:
        """
        # Link the grib files
        sys.stdout.flush()
        os.system(self.CMD_LINK_GRIB)

        # Run geogrid if it has not already been run
        startTime = datetime.datetime.now()
        startTimeInt = int(time.time())
        print('Starting Geogrid at: ' + str(startTime))
        sys.stdout.flush()
        os.system(self.CMD_GEOGRID)
        geogrid_sim = self.runwrf_finish_check('geogrid')
        while geogrid_sim is not 'complete':
            if geogrid_sim is 'failed':
                print_last_3lines(self.DIR_WRFOUT + 'geogrid.log')
                return False
            elif (int(time.time()) - startTimeInt) < 600:
                time.sleep(2)
                geogrid_sim = self.runwrf_finish_check('geogrid')
            else:
                print('TimeoutError in run_wps: Geogrid took more than 10min to run... exiting.')
                return False
        elapsed = datetime.datetime.now() - startTime
        print('Geogrid ran in: ' + str(elapsed))

        # Run ungrib and metgrid
        startTime = datetime.datetime.now()
        startTimeInt = int(time.time())
        print('Starting Ungrib and Metgrid at: ' + str(startTime))
        sys.stdout.flush()
        os.system(self.CMD_UNGMETG)
        metgrid_sim = self.runwrf_finish_check('metgrid')
        while metgrid_sim is not 'complete':
            if metgrid_sim is 'failed':
                print_last_3lines(self.DIR_WRFOUT + 'metgrid.log')
                return False
            elif (int(time.time()) - startTimeInt) < 600:
                time.sleep(2)
                metgrid_sim = self.runwrf_finish_check('metgrid')
            else:
                print('TimeoutError in run_wps: Ungrib and Metgrid took more than 10min to run... exiting.')
                return False
        elapsed = datetime.datetime.now() - startTime
        print('Ungrib and Metgrid ran in: ' + str(elapsed))

        # Remove the data directory after WPS has run
        # lh.remove_dir(DIR_DATA)
        return True

    def run_real(self):
        """
        Runs real.exe and checks to see that if it was successful.

        :return:
        """

        startTime = datetime.datetime.now()
        startTimeInt = int(time.time())
        print('Starting Real at: ' + str(startTime))
        sys.stdout.flush()
        os.system(self.CMD_REAL)
        real_sim = self.runwrf_finish_check('real')
        while real_sim is not 'complete':
            if real_sim is 'failed':
                print_last_3lines(self.DIR_WRFOUT + 'rsl.out.0000')
                return False
            elif (int(time.time()) - startTimeInt) < 600:
                time.sleep(2)
                real_sim = self.runwrf_finish_check('real')
            else:
                print('TimeoutError in run_real: Real took more than 10min to run... exiting.')
                return False
        elapsed = datetime.datetime.now() - startTime
        print('Real ran in: ' + str(elapsed) + ' seconds')
        return True

    def run_wrf(self):
        """
        Runs wrf.exe and checks to see if it was successful.

        :return:
        """

        startTime = datetime.datetime.now()
        startTimeInt = int(time.time())
        print('Starting WRF at: ' + str(startTime))
        sys.stdout.flush()
        os.system(self.CMD_WRF)
        # Make the script sleep for 5 minutes to allow for the rsl.out.0000 file to reset.
        time.sleep(300)
        wrf_sim = self.runwrf_finish_check('wrf')
        while wrf_sim is not 'complete':
            if wrf_sim is 'failed':
                print_last_3lines(self.DIR_WRFOUT + 'rsl.out.0000')
                return False
            elif (int(time.time()) - startTimeInt) < 7200:
                time.sleep(10)
                wrf_sim = self.runwrf_finish_check('wrf')
            else:
                print('TimeoutError in run_wrf at {}: WRF took more than 2hrs to run... exiting.'.format(
                    datetime.datetime.now()))
                return False
        print('WRF finished running at: ' + str(datetime.datetime.now()))
        elapsed = datetime.datetime.now() - startTime
        print('WRF ran in: ' + str(elapsed))

        # Rename the wrfout files.
        for n in range(1, self.n_domains + 1):
            os.system(self.CMD_MV % (self.DIR_WRFOUT + 'wrfout_d0' + str(n) + '_'
                                     + self.forecast_start.strftime('%Y') + '-'
                                     + self.forecast_start.strftime('%m') + '-'
                                     + self.forecast_start.strftime('%d') + '_00:00:00',
                                     self.DIR_WRFOUT + 'wrfout_d0' + str(n) + '.nc'))
        return True

    def wrf_era5_diff(self):
        """
        Computes the difference between the wrf simulation and ERA5

        NEEDS QUITE A BIT OF WORK!!!

        :return:
        """

        # Download ERA5 data for benchmarking
        if self.on_cheyenne:
            ERA5_ROOT = '/gpfs/fs1/collections/rda/data/ds633.0/e5.oper.an.sfc/'
            # DATA_ROOT1 = DATA_ROOT1 + self.forecast_start.strftime('%Y') + self.forecast_start.strftime('%m') + '/'
        else:
            ERA5_ROOT = '/share/mzhang/jas983/wrf_data/data/ERA5/'
            datpfx1 = 'EastUS_e5.oper.an.sfc.128_165_10u.ll025sc.'
            datpfx2 = 'EastUS_e5.oper.an.sfc.128_166_10v.ll025sc.'
            datpfx3 = 'EastUS_e5.oper.an.sfc.128_167_2t.ll025sc.'
            datpfx4 = 'EastUS_e5.oper.an.sfc.228_246_100u.ll025sc.'
            datpfx5 = 'EastUS_e5.oper.an.sfc.228_247_100v.ll025sc.'
            if not os.path.exists(ERA5_ROOT + datpfx1 + self.forecast_start.strftime('%Y')
                                  + self.forecast_start.strftime('%m') + '0100_'
                                  + self.forecast_start.strftime('%Y')
                                  + self.forecast_start.strftime('%m') + '3123.nc'):

                # Change into the ERA5 data directory
                if not os.path.exists(ERA5_ROOT):
                    os.mkdir(ERA5_ROOT)
                # The following define paths to the required data on the RDA site
                dspath = 'http://rda.ucar.edu/data/ds633.0/'
                DATA_ROOT1 = 'e5.oper.an.sfc/' + self.forecast_start.strftime('%Y') \
                             + self.forecast_start.strftime('%m') + '/'

                # Build the file list to be downloaded from the RDA
                filelist = [DATA_ROOT1 + datpfx1 + self.forecast_start.strftime('%Y')
                            + self.forecast_start.strftime('%m') + '0100_'
                            + self.forecast_start.strftime('%Y') + self.forecast_start.strftime('%m') + '3123.nc',
                            DATA_ROOT1 + datpfx2 + self.forecast_start.strftime('%Y')
                            + self.forecast_start.strftime('%m') + '0100_'
                            + self.forecast_start.strftime('%Y') + self.forecast_start.strftime('%m') + '3123.nc',
                            DATA_ROOT1 + datpfx3 + self.forecast_start.strftime('%Y')
                            + self.forecast_start.strftime('%m') + '0100_'
                            + self.forecast_start.strftime('%Y') + self.forecast_start.strftime('%m') + '3123.nc',
                            DATA_ROOT1 + datpfx4 + self.forecast_start.strftime('%Y')
                            + self.forecast_start.strftime('%m') + '0100_'
                            + self.forecast_start.strftime('%Y') + self.forecast_start.strftime('%m') + '3123.nc',
                            DATA_ROOT1 + datpfx5 + self.forecast_start.strftime('%Y')
                            + self.forecast_start.strftime('%m') + '0100_'
                            + self.forecast_start.strftime('%Y') + self.forecast_start.strftime('%m') + '3123.nc']
                print(filelist)
                # Download the data from the RDA
                rda_download(filelist, dspath)
                # Move the files into the ERA5 data directory
                cmd = self.CMD_MV % (datpfx1 + '*', ERA5_ROOT)
                cmd = cmd + '; ' + self.CMD_MV % (datpfx2 + '*', ERA5_ROOT)
                cmd = cmd + '; ' + self.CMD_MV % (datpfx3 + '*', ERA5_ROOT)
                cmd = cmd + '; ' + self.CMD_MV % (datpfx4 + '*', ERA5_ROOT)
                cmd = cmd + '; ' + self.CMD_MV % (datpfx5 + '*', ERA5_ROOT)
                os.system(cmd)
        # Run ncks to reduce the size of the files
        # Below is an example of what needs to be implemented:
        # ncks -d longitude,265.,295. -d latitude,30.,50.
        # e5.oper.an.sfc.128_165_10u.regn320sc.2011010100_2011013123.nc
        # EastUS_e5.oper.an.sfc.128_165_10u.regn320sc.2011010100_2011013123.nc

        # Run the NCL script that computes the error between the WRF run and the ERA5 surface analysis
        CMD_REGRID = 'ncl in_yr=%s in_mo=%s in_da=%s \'WRFdir="%s"\' \'paramstr="%s"\' %swrf2era_error.ncl' % \
                     (self.forecast_start.strftime('%Y'), self.forecast_start.strftime('%m'),
                      self.forecast_start.strftime('%d'), self.DIR_WRFOUT, self.paramstr, self.DIR_WRFOUT)
        os.system(CMD_REGRID)

        # Extract the total error after the script has run
        error_file = self.DIR_WRFOUT + 'mae_wrfyera_' + self.paramstr + '.csv'
        while not os.path.exists(error_file):
            time.sleep(1)
        mae = read_last_line(error_file)
        mae = mae.split(',')
        mae[-1] = mae[-1].strip()
        mae = [float(i) for i in mae]
        total_error = sum(mae)
        print(f'!!! Parameters {self.paramstr} have a total error {mae}')
        return total_error


def determine_computer():
    """
    Determine the computer.

    :return:
    """
    if 'GROUP' in os.environ:
        # Determine if we are on Cheyenne
        if os.environ['GROUP'] == 'ncar':
            on_cheyenne = True
            on_aws = False
            on_magma = False
        # Determine if we are on AWS
        elif os.environ['GROUP'] == 'ec2-user':
            on_cheyenne = False
            on_aws = True
            on_magma = False
        elif os.environ['GROUP'] == 'mzhang':
            on_cheyenne = False
            on_aws = False
            on_magma = True
        else:
            on_cheyenne = False
            on_aws = False
            on_magma = False
    else:
        on_cheyenne = False
        on_aws = False
        on_magma = False
    return on_aws, on_cheyenne, on_magma


def read_last_line(file_name):
    """
    Reads the last line of a file.

    :param file_name:
    :return:
    """
    try:
        with open(file_name, mode='r') as infile:
            lines = infile.readlines()
    except IOError:
        last_line = 'IOEror in read_last_line: this file does not exist.'
        return last_line
    try:
        last_line = lines[-1]
    except IndexError:
        last_line = 'IndexError in read_last_line: no last line appears to exist in this file.'
    return last_line


def read_2nd2_last_line(file_name):
    """
    Reads the second to last line of a file.

    :param file_name:
    :return:
    """
    try:
        with open(file_name, mode='r') as infile:
            lines = infile.readlines()
    except IOError:
        second2_last_line = 'IOError in read_2nd2_last_line: this file does not currently exist.'
        return second2_last_line
    try:
        second2_last_line = lines[-2]
    except IndexError:
        second2_last_line = 'IndexError in read_2nd2_last_line: ' \
                            'there do not appear to be at least two lines in this file.'
    return second2_last_line


def print_last_3lines(file_name):
    """
    Prints the last three lines of a file.

    :param file_name:
    :return:
    """
    try:
        with open(file_name, mode='r') as infile:
            lines = infile.readlines()
    except IOError:
        print('IOError in print_last_3lines: this file does not currently exist.')
        return
    try:
        txt = lines[-4:-1]
        print('\n'.join(txt))
    except IndexError:
        print('IndexError in print_last_3lines: there do not appear to be at least three lines in this file.')
        return


def rda_download(filelist, dspath):
    """
    Logs into the RDA file and downloads specified files.

    :param filelist:
    :param dspath:
    :return:
    """
    # Specify login information and url for RDA
    pswd = 'mkjmJ17'
    url = 'https://rda.ucar.edu/cgi-bin/login'
    values = {'email': 'jas983@cornell.edu', 'passwd': pswd, 'action': 'login'}

    # RDA user authentication
    ret = requests.post(url, data=values)
    if ret.status_code != 200:
        print('Bad Authentication for RDA')
        print(ret.text)
        return

    # Download files from RDA server
    print('Downloading data from RDA...')
    for datafile in filelist:
        filename = dspath + datafile
        file_base = os.path.basename(datafile)
        # print('Downloading', file_base)
        req = requests.get(filename, cookies=ret.cookies, allow_redirects=True, stream=True)
        try:
            filesize = int(req.headers['Content-length'])
        except KeyError as e:
            print('KeyError in rda_download:\n%s\nCHECK THAT RDA IS WORKING!!!' % e)
            return
        with open(file_base, 'wb') as outfile:
            chunk_size = 1048576
            for chunk in req.iter_content(chunk_size=chunk_size):
                outfile.write(chunk)
        #         if chunk_size < filesize:
        #             check_file_status(file_base, filesize)
        check_file_status(file_base, filesize)
    print('Done downloading data from RDA!')


def check_file_status(filepath, filesize):
    """
    Checks the file status during a download from the internet.

    :param filepath:
    :param filesize:
    :return:
    """
    sys.stdout.write('\r')
    sys.stdout.flush()
    size = int(os.stat(filepath).st_size)
    percent_complete = (size / filesize) * 100
    sys.stdout.write('%.3f %s\n' % (percent_complete, '% Completed'))
    sys.stdout.flush()
