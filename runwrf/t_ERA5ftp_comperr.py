#!/usr/bin/python

from argparse import ArgumentParser
from datetime import datetime, timedelta
from os import chdir, getcwd, mkdir, makedirs, system, path, environ
from shutil import rmtree
from socket import gethostname
from subprocess import call
from sys import exit
from time import localtime, strftime, strptime, time
import time as tm
from wrfparams import name2num, generate, combine, filldefault, pbl2sfclay
import sys, os
import requests


def check_file_status(filepath, filesize):
    sys.stdout.write('\r')
    sys.stdout.flush()
    size = int(os.stat(filepath).st_size)
    percent_complete = (size / filesize) * 100
    sys.stdout.write('%.3f %s' % (percent_complete, '% Completed'))
    sys.stdout.flush()


# Define command line input options
arg = ArgumentParser()
arg.add_argument('-s', help="Start Date", type=str)
arg.add_argument('-e', help="End Date", type=str)
arg.add_argument('-y', help="Parameterizations Yaml File", type=str)
arg.add_argument('-p', help="Generate Params?", type=bool)
arg.add_argument('-b', help="Boundary Conditon Data Source", type=str)
arg.add_argument('-d', help="Max Domains", type=int)
arg.add_argument('-t', help="Namelist Template Directory", type=str)
arg.add_argument('-mp', help="Microphysics scheme", type=str)
arg.add_argument('-lw', help="Longwave radiation scheme", type=str)
arg.add_argument('-sw', help="Shortwave radiation scheme", type=str)
arg.add_argument('-lsm', help="Land surface model", type=str)
arg.add_argument('-pbl', help="Planetary boundary layer scheme", type=str)
arg.add_argument('-cu', help="Cumulus scheme", type=str)
args = arg.parse_args()

# Determine if we are on Cheyenne
if system('echo $GROUP') == 'ncar':
    on_cheyenne = True
else:
    on_cheyenne = False

# Format the forecast start time
forecast_start = datetime.strptime(args.s, '%b %d %Y')
# forecast_start = datetime.strptime(args.s, '%b %d %Y %H')
# forecast_start = datetime.strptime(args.s, '%b %d %Y %H:%M:%S')
forecast_end = datetime.strptime(args.e, '%b %d %Y')
delt = forecast_end - forecast_start
print('Forecast statting on: ')
print(forecast_start)
print('Forecast ending on: ')
print(forecast_end)

# Define the yaml file containing a desired set of paramter combinations
if args.y is not None:
    in_yaml = args.y
else:
    in_yaml = 'params.yml'

# Next, define the data directories and file prefixes on RDA which correspond
# to each specific type of input data
# ERA is the only supported data type right now
if args.b == 'ERA':
    if on_cheyenne:
        DATA_ROOT1 = '/gpfs/fs1/collections/rda/data/ds627.0/ei.oper.an.pl/'
        DATA_ROOT1 = DATA_ROOT1 + forecast_start.strftime('%Y') + forecast_start.strftime('%m') + '/'
        DATA_ROOT2 = '/gpfs/fs1/collections/rda/data/ds627.0/ei.oper.an.sfc/'
        DATA_ROOT2 = DATA_ROOT2 + forecast_start.strftime('%Y') + forecast_start.strftime('%m') + '/'
    else:
        # The following define paths to the required data on the RDA site
        dspath = 'http://rda.ucar.edu/data/ds627.0/'
        DATA_ROOT1 = 'ei.oper.an.pl/' + forecast_start.strftime('%Y') + forecast_start.strftime('%m') + '/'
        DATA_ROOT2 = 'ei.oper.an.sfc/' + forecast_start.strftime('%Y') + forecast_start.strftime('%m') + '/'
    datpfx1 = 'ei.oper.an.pl.regn128sc.'
    datpfx2 = 'ei.oper.an.pl.regn128uv.'
    datpfx3 = 'ei.oper.an.sfc.regn128sc.'
    Vsfx = 'ERA-interim.pl'
else:
    Vsfx = args.b
print('Using Vtable: ')
print(Vsfx)

# Generate a parameter combination of the 6 core parameters if the user has specified this option.
# Otherwise, use specified input parameters and use defaults for the remaining paramters.
if args.p:
    rand_params = generate(in_yaml)
    print('The following parameters were chosen: ')
    print(rand_params)
    param_ids = name2num(in_yaml, mp_in=rand_params[0], lw_in=rand_params[1],
                         sw_in=rand_params[2], lsm_in=rand_params[3],
                         pbl_in=rand_params[4], clo_in=rand_params[5])
    print(param_ids)
else:
    param_ids = [None, None, None, None, None, None]
    if args.mp is not None:
        param_ids1 = name2num(yaml_file, use_defaults=False, mp_in=args.mp, lw_in="None",
                              sw_in="None", lsm_in="None", pbl_in="None", clo_in="None")
        param_ids = combine(param_ids, param_ids1)
    if args.lw is not None:
        param_ids2 = name2num(yaml_file, use_defaults=False, mp_in="None", lw_in="None",
                              sw_in="None", lsm_in="None", pbl_in="None", clo_in="None")
        param_ids = combine(param_ids, param_ids2)
    if args.sw is not None:
        param_ids3 = name2num(yaml_file, use_defaults=False, mp_in="None", lw_in="None",
                              sw_in="None", lsm_in="None", pbl_in="None", clo_in="None")
        param_ids = combine(param_ids, param_ids3)
    if args.lsm is not None:
        param_ids4 = name2num(yaml_file, use_defaults=False, mp_in="None", lw_in="None",
                              sw_in="None", lsm_in="None", pbl_in="None", clo_in="None")
        param_ids = combine(param_ids, param_ids4)
    if args.pbl is not None:
        param_ids5 = name2num(yaml_file, use_defaults=False, mp_in="None", lw_in="None",
                              sw_in="None", lsm_in="None", pbl_in="None", clo_in="None")
        param_ids = combine(param_ids, param_ids5)
    if args.cu is not None:
        param_ids6 = name2num(yaml_file, use_defaults=False, mp_in="None", lw_in="None",
                              sw_in="None", lsm_in="None", pbl_in="None", clo_in="None")
        param_ids = combine(param_ids, param_ids6)
    param_ids = filldefault(in_yaml, param_ids)

# Set the sf_sfclay_pysics option based on that selected for PBL
id_sfclay = pbl2sfclay(param_ids[4])
param_ids.append(id_sfclay)

# Set directory names
DIR_OUT = getcwd() + '/'  # Needs Editing
DIR_LOCAL_TMP = '../wrfout/%s_%dmp%dlw%dsw%dlsm%dpbl%dcu/' % \
                (forecast_start.strftime('%Y-%m-%d'), param_ids[0], param_ids[1],
                 param_ids[2], param_ids[3], param_ids[4], param_ids[6])
if on_cheyenne:
    DIR_WRF_ROOT = '/glade/u/home/wrfhelp/PRE_COMPILED_CODE/%s/'
    DIR_WPS = DIR_WRF_ROOT % 'WPSV4.1_intel_serial_large-file'
    DIR_WRF = DIR_WRF_ROOT % 'WRFV4.1_intel_dmpar'
    DIR_WPS_GEOG = '/glade/u/home/wrfhelp/WPS_GEOG/'
    DIR_DATA = '/glade/scratch/sward/data/' + str(args.b) + '/'
else:
    DIR_WPS = '/home/jas983/models/wrf/WPS-3.8.1/'
    DIR_WRF = '/home/jas983/models/wrf/WRFV3/'
    DIR_WPS_GEOG = '/share/mzhang/jas983/wrf_data/WPS_GEOG'
    DIR_DATA = '../../data/' + str(args.b) + '/'

# Define a directory containing:
# a) namelist.wps and namelist.input templates
# b) qsub template csh scripts for running geogrid, ungrib & metgrid, and real & wrf.
if args.t is not None:
    DIR_TEMPLATES = args.t + '/'
else:
    DIR_TEMPLATES = '../templates/wrftemplates/'

# Define command aliai
CMD_LN = 'ln -sf %s %s'
CMD_CP = 'cp %s %s'
CMD_MV = 'mv %s %s'
CMD_CHMOD = 'chmod -R %s %s'
CMD_LINK_GRIB = DIR_WPS + 'link_grib.csh ' + DIR_DATA + '*'  # Needs editing
if on_cheyenne:
    CMD_GEOGRID = 'qsub template_rungeogrid.csh'
    CMD_UNGMETG = 'qsub template_runungmetg.csh'
    CMD_REAL = 'qsub template_runreal.csh'
    CMD_WRF = 'qsub template_runwrf.csh'
else:
    CMD_GEOGRID = 'condor_submit sub.geogrid'
    CMD_UNGMETG = 'condor_submit sub.metgrid'
    CMD_REAL = 'condor_submit sub.real'
    CMD_WRF = 'condor_submit sub.real'

# Set the number of domains to that input, or default to a single domain.
if args.d is not None and args.d > 0:
    MAX_DOMAINS = int(args.d)
else:
    MAX_DOMAINS = 3

# Try to remove the data dir, and print 'DIR_DATA not deleted' if you cannot. Then remake the dir, and enter it.
try:
    rmtree(DIR_DATA)
except:
    print(DIR_DATA + ' not deleted')
makedirs(DIR_DATA, 0755)
chdir(DIR_DATA)
i = int(forecast_start.day)
n = int(forecast_start.day) + int(delt.days)
if on_cheyenne:
    # Copy desired data files from RDA
    ##### THIS ONLY WORKS IF YOU WANT TO RUN WITHIN A SINGLE MONTH
    while i <= n:
        cmd = CMD_CP % (DATA_ROOT1 + datpfx1 + forecast_start.strftime('%Y')
                        + forecast_start.strftime('%m') + str(i) + '*', DIR_DATA)
        cmd = cmd + '; ' + CMD_CP % (DATA_ROOT1 + datpfx2 + forecast_start.strftime('%Y')
                                     + forecast_start.strftime('%m') + str(i) + '*', DIR_DATA)
        cmd = cmd + '; ' + CMD_CP % (DATA_ROOT2 + datpfx3 + forecast_start.strftime('%Y')
                                     + forecast_start.strftime('%m') + str(i) + '*', DIR_DATA)
        os.system(cmd)
        i += 1
else:
    # Build the file list to be downloaded from the RDA
    hrs = ['00', '06', '12', '18']
    filelist = []
    while i <= n:
        for hr in hrs:
            filelist.append(DATA_ROOT1 + datpfx1 + forecast_start.strftime('%Y')
                            + forecast_start.strftime('%m') + str(i) + hr)
            filelist.append(DATA_ROOT1 + datpfx2 + forecast_start.strftime('%Y')
                            + forecast_start.strftime('%m') + str(i) + hr)
            filelist.append(DATA_ROOT2 + datpfx3 + forecast_start.strftime('%Y')
                            + forecast_start.strftime('%m') + str(i) + hr)
        i += 1
    pswd = 'mkjmJ17'
    url = 'https://rda.ucar.edu/cgi-bin/login'
    values = {'email': 'jas983@cornell.edu', 'passwd': pswd, 'action': 'login'}

    # RDA user authentication
    ret = requests.post(url, data=values)
    if ret.status_code != 200:
        print('Bad Authentication')
        print(ret.text)
        exit(1)

   # # Download files from RDA server
   # for erafile in filelist:
   #     filename = dspath + erafile
   #    file_base = os.path.basename(erafile)
   #     print('Downloading', file_base)
   #    req = requests.get(filename, cookies=ret.cookies, allow_redirects=True, stream=True)
   #    filesize = int(req.headers['Content-length'])
   #    with open(file_base, 'wb') as outfile:
   #        chunk_size = 1048576
   #        for chunk in req.iter_content(chunk_size=chunk_size):
   #            outfile.write(chunk)
   #             if chunk_size < filesize:
   #                check_file_status(file_base, filesize)
   #    check_file_status(file_base, filesize)
   #     print()

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
CMD_REGRID = 'ncl in_yr=%s in_mo=%s in_da=%s WRFdir=%s t_wrf2era_runwrf.ncl' % \
             (forecast_start.strftime('%Y'), forecast_start.strftime('%m'),
              forecast_start.strftime('%d'), DIR_LOCAL_TMP)

system(CMD_REGRID)
print('Congrats you pass the regridding test')
