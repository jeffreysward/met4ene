from datetime import datetime
from os import chdir, getcwd, makedirs, system, path, environ
from shutil import rmtree
from sys import exit
from time import time
import time as tm
import os
import requests
from wrfparams import flexible_generate, write_param_csv
import runwrf as rw


# Set parameters here that should be set automatically eventually
remove_DIR_DATA = False


def wrf_fitness(start_date='Jan 15 2011', end_date='Jan 16 2011', in_yaml='params.yml', generate_params=True,
                bc_data='ERA', MAX_DOMAINS=1, template_dir=None,
                mp=None, lw=None, sw=None, lsm=None, pbl=None, cu=None):

    # Format the forecast start/end and determine the total time.
    forecast_start = datetime.strptime(start_date, '%b %d %Y')
    forecast_end = datetime.strptime(end_date, '%b %d %Y')
    delt = forecast_end - forecast_start
    print('Forecast starting on: {}'.format(forecast_start))
    print('Forecast ending on: {}'.format(forecast_end))

    # Generate a parameter combination of the 6 core parameters if the user has specified this option.
    # Otherwise, use specified input parameters and use defaults for the remaining paramters.
    param_ids, paramstr = flexible_generate(generate_params, mp, lw, sw, lsm, pbl, cu, in_yaml='params.yml')

    # Write parameter combinations to CSV
    # (if you would like to restart this, you must manually delete this CSV)
    write_param_csv(param_ids)

    # Next, get boundary condition data for the simulation
    # ERA is the only supported data type right now.
    vtable_sfx = rw.get_bc_data(paramstr, bc_data, template_dir, forecast_start, delt, remove_DIR_DATA)

    # Setup the working directory to run the simulation
    rw.wrfdir_setup(paramstr, forecast_start, bc_data, template_dir, vtable_sfx)

    # Prepare the namelist
    rw.prepare_namelists(paramstr, param_ids, forecast_start, forecast_end, delt,
                         bc_data, template_dir, MAX_DOMAINS)

    # RUN WPS
    rw.run_wps(paramstr, forecast_start, bc_data, template_dir)

    # RUN REAL
    rw.run_real(paramstr, forecast_start, bc_data, template_dir)

    # RUN WRF
    rw.run_wrf(paramstr, forecast_start, bc_data, template_dir, MAX_DOMAINS)

    # Remove the data directory after the WRF run
    if remove_DIR_DATA:
        try:
            rmtree(DIR_DATA)
        except:
            print(DIR_DATA + ' not deleted')

    # Download ERA5 data for benchmarking
    if on_cheyenne:
        DATA_ROOT1 = '/gpfs/fs1/collections/rda/data/ds630.0/e5.oper.an.sfc/'
        DATA_ROOT1 = DATA_ROOT1 + forecast_start.strftime('%Y') + forecast_start.strftime('%m') + '/'
    else:
        ERA5_ROOT = '/share/mzhang/jas983/wrf_data/data/ERA5/'
        datpfx1 = 'e5.oper.an.sfc.128_165_10u.regn320sc.'
        datpfx2 = 'e5.oper.an.sfc.128_166_10v.regn320sc.'
        datpfx3 = 'e5.oper.an.sfc.128_167_2t.regn320sc.'
        datpfx4 = 'e5.oper.an.sfc.228_246_100u.regn320sc.'
        datpfx5 = 'e5.oper.an.sfc.228_247_100v.regn320sc.'
        if not path.exists(ERA5_ROOT + datpfx1 + forecast_start.strftime('%Y')
                           + forecast_start.strftime('%m') + '0100_'
                           + forecast_start.strftime('%Y') + forecast_start.strftime('%m') + '3123.nc'):

            # Change into the ERA5 data directory
            chdir(ERA5_ROOT)
            # The following define paths to the required data on the RDA site
            dspath = 'http://rda.ucar.edu/data/ds630.0/'
            DATA_ROOT1 = 'e5.oper.an.sfc/' + forecast_start.strftime('%Y') + forecast_start.strftime('%m') + '/'

            # Build the file list to be downloaded from the RDA
            filelist = [DATA_ROOT1 + datpfx1 + forecast_start.strftime('%Y')
                        + forecast_start.strftime('%m') + '0100_'
                        + forecast_start.strftime('%Y') + forecast_start.strftime('%m') + '3123.nc',
                        DATA_ROOT1 + datpfx2 + forecast_start.strftime('%Y')
                        + forecast_start.strftime('%m') + '0100_'
                        + forecast_start.strftime('%Y') + forecast_start.strftime('%m') + '3123.nc',
                        DATA_ROOT1 + datpfx3 + forecast_start.strftime('%Y')
                        + forecast_start.strftime('%m') + '0100_'
                        + forecast_start.strftime('%Y') + forecast_start.strftime('%m') + '3123.nc',
                        DATA_ROOT1 + datpfx4 + forecast_start.strftime('%Y')
                        + forecast_start.strftime('%m') + '0100_'
                        + forecast_start.strftime('%Y') + forecast_start.strftime('%m') + '3123.nc',
                        DATA_ROOT1 + datpfx5 + forecast_start.strftime('%Y')
                        + forecast_start.strftime('%m') + '0100_'
                        + forecast_start.strftime('%Y') + forecast_start.strftime('%m') + '3123.nc']

            for era5file in filelist:
                filename = dspath + era5file
                file_base = os.path.basename(era5file)
                print('Downloading', file_base)
                req = requests.get(filename, cookies=ret.cookies, allow_redirects=True, stream=True)
                filesize = int(req.headers['Content-length'])
                with open(file_base, 'wb') as outfile:
                    chunk_size = 1048576
                    for chunk in req.iter_content(chunk_size=chunk_size):
                        outfile.write(chunk)
                        if chunk_size < filesize:
                            check_file_status(file_base, filesize)
                check_file_status(file_base, filesize)
                print()

    # Run the NCL script that computes the error between the WRF run and the ERA5 surface analysis
    chdir(DIR_RUNWRF)
    CMD_REGRID = 'ncl in_yr=%s in_mo=%s in_da=%s \'WRFdir="%s"\' \'paramstr="%s"\' wrf2era_error.ncl' % \
                 (forecast_start.strftime('%Y'), forecast_start.strftime('%m'),
                  forecast_start.strftime('%d'), DIR_LOCAL_TMP, paramstr)
    system('pwd')
    system(CMD_REGRID)

    # Extract the total error after the script has run
