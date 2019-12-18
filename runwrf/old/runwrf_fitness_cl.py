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
import sys
import os
import requests
import csv


# Set parameters here that should be set automatically eventually
remove_DIR_DATA = False


def read_last_line(file_name):
    try:
        with open(file_name, mode='r') as infile:
            lines = infile.readlines()
    except IOError:
        last_line = 'This file does not exist.'
        return last_line
    try:
        last_line = lines[-1]
    except IndexError:
        last_line = 'No last line appears to exist in this file.'
    return last_line


def read_2nd2_last_line(file_name):
    try:
        with open(file_name, mode='r') as infile:
            lines = infile.readlines()
    except IOError:
        second2_last_line = 'This file does not exist.'
        return second2_last_line
    try:
        second2_last_line = lines[-2]
    except IndexError:
        second2_last_line = 'There do not appear to be at least two lines in this file.'
    return second2_last_line


def runwrf_finish_check(program):
    if program == 'geogrid':
        msg = read_2nd2_last_line('output.geogrid')
        complete = 'Successful completion of geogrid' in msg
    elif program == 'metgrid':
        msg = read_2nd2_last_line('output.metgrid')
        complete = 'Successful completion of metgrid' in msg
    elif program == 'real':
        msg = read_last_line('rsl.out.0000')
        print(msg)
        complete = 'SUCCESS COMPLETE REAL' in msg
    elif program == 'wrf':
        msg = read_last_line('rsl.out.0000')
        complete = 'SUCCESS COMPLETE WRF' in msg
    else:
        complete = False
    return complete


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
if environ['GROUP'] == 'ncar':
    on_cheyenne = True
    on_aws = False
elif environ['GROUP'] == 'ec2-user':
    on_cheyenne = False
    on_aws = True
else:
    on_cheyenne = False
    on_aws = False

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
    print('The following random parameters were generated: ')
    param_ids = name2num(in_yaml, mp_in=rand_params[0], lw_in=rand_params[1],
                         sw_in=rand_params[2], lsm_in=rand_params[3],
                         pbl_in=rand_params[4], clo_in=rand_params[5])
    print(param_ids)
else:
    param_ids = [None, None, None, None, None, None]
    if args.mp is not None:
        param_ids1 = name2num(in_yaml, use_defaults=False, mp_in=args.mp, lw_in="None",
                              sw_in="None", lsm_in="None", pbl_in="None", clo_in="None")
        param_ids = combine(param_ids, param_ids1)
    if args.lw is not None:
        param_ids2 = name2num(in_yaml, use_defaults=False, mp_in="None", lw_in=args.lw,
                              sw_in="None", lsm_in="None", pbl_in="None", clo_in="None")
        param_ids = combine(param_ids, param_ids2)
    if args.sw is not None:
        param_ids3 = name2num(in_yaml, use_defaults=False, mp_in="None", lw_in="None",
                              sw_in=args.sw, lsm_in="None", pbl_in="None", clo_in="None")
        param_ids = combine(param_ids, param_ids3)
    if args.lsm is not None:
        param_ids4 = name2num(in_yaml, use_defaults=False, mp_in="None", lw_in="None",
                              sw_in="None", lsm_in=args.lsm, pbl_in="None", clo_in="None")
        param_ids = combine(param_ids, param_ids4)
    if args.pbl is not None:
        param_ids5 = name2num(in_yaml, use_defaults=False, mp_in="None", lw_in="None",
                              sw_in="None", lsm_in="None", pbl_in=args.pbl, clo_in="None")
        param_ids = combine(param_ids, param_ids5)
    if args.cu is not None:
        param_ids6 = name2num(in_yaml, use_defaults=False, mp_in="None", lw_in="None",
                              sw_in="None", lsm_in="None", pbl_in="None", clo_in=args.cu)
        param_ids = combine(param_ids, param_ids6)
    param_ids = filldefault(in_yaml, param_ids)
    print('The following parameters were chosen: ')
    print(param_ids)

# Write parameter combinations to CSV
# (if you would like to restart this, you must manually delete this CSV; should change this eventuallly)
runwrfcsv = 'paramfeed_runwrf.csv'
if not path.exists(runwrfcsv):
    csvData = [['ra_lw_physics', 'ra_sw_physics', 'sf_surface_physics',
                'bl_pbl_physics', 'cu_physics', 'sf_sfclay_physics'], param_ids]
    with open(runwrfcsv, 'w') as csvFile:
        writer = csv.writer(csvFile)
        writer.writerows(csvData)
else:
    with open(runwrfcsv, 'a') as csvFile:
        writer = csv.writer(csvFile)
        writer.writerow(param_ids)

# Set the sf_sfclay_pysics option based on that selected for PBL
id_sfclay = pbl2sfclay(param_ids[4])
param_ids.append(id_sfclay)

# Set directory names
DIR_OUT = getcwd() + '/'  # Needs Editing (maybe)
DIR_LOCAL_TMP = '../wrfout/%s_%dmp%dlw%dsw%dlsm%dpbl%dcu/' % \
                (forecast_start.strftime('%Y-%m-%d'), param_ids[0], param_ids[1],
                 param_ids[2], param_ids[3], param_ids[4], param_ids[6])
if on_cheyenne:
    DIR_WRF_ROOT = '/glade/u/home/wrfhelp/PRE_COMPILED_CODE/%s/'
    DIR_WPS = DIR_WRF_ROOT % 'WPSV4.1_intel_serial_large-file'
    DIR_WRF = DIR_WRF_ROOT % 'WRFV4.1_intel_dmpar'
    DIR_WPS_GEOG = '/glade/u/home/wrfhelp/WPS_GEOG/'
    DIR_DATA = '/glade/scratch/sward/data/' + str(args.b) + '/%s_%dmp%dlw%dsw%dlsm%dpbl%dcu/' % \
               (forecast_start.strftime('%Y-%m-%d'), param_ids[0], param_ids[1], param_ids[2],
                param_ids[3], param_ids[4], param_ids[6])
    DIR_LOCAL_TMP = '/glade/scratch/sward/met4ene/wrfout/%s_%dmp%dlw%dsw%dlsm%dpbl%dcu/' % \
                    (forecast_start.strftime('%Y-%m-%d'), param_ids[0], param_ids[1],
                     param_ids[2], param_ids[3], param_ids[4], param_ids[6])
elif on_aws:
    DIR_WPS = '/home/ec2-user/environment/Build_WRF/WPS/'
    DIR_WRF = '/home/ec2-user/environment/Build_WRF/WRF/'
    DIR_WPS_GEOG = '/home/ec2-user/environment/data/WPS_GEOG'
    DIR_DATA = '/home/ec2-user/environment/data/' + str(args.b) + '/%s_%dmp%dlw%dsw%dlsm%dpbl%dcu/' % \
               (forecast_start.strftime('%Y-%m-%d'), param_ids[0], param_ids[1], param_ids[2],
                param_ids[3], param_ids[4], param_ids[6])
    DIR_LOCAL_TMP = '/home/ec2-user/environment/met4ene/wrfout/ARW/%s_%dmp%dlw%dsw%dlsm%dpbl%dcu/' % \
                    (forecast_start.strftime('%Y-%m-%d'), param_ids[0], param_ids[1],
                     param_ids[2], param_ids[3], param_ids[4], param_ids[6])
else:
    DIR_WPS = '/home/jas983/models/wrf/WPS-3.8.1/'
    DIR_WRF = '/home/jas983/models/wrf/WRFV3/'
    DIR_WPS_GEOG = '/share/mzhang/jas983/wrf_data/WPS_GEOG'
    DIR_DATA = '/share/mzhang/jas983/wrf_data/data/' + str(args.b) + '/%s_%dmp%dlw%dsw%dlsm%dpbl%dcu/' % \
               (forecast_start.strftime('%Y-%m-%d'), param_ids[0], param_ids[1], param_ids[2],
                param_ids[3], param_ids[4], param_ids[6])
    DIR_LOCAL_TMP = '/share/mzhang/jas983/wrf_data/met4ene/wrfout/ARW/%s_%dmp%dlw%dsw%dlsm%dpbl%dcu/' % \
                    (forecast_start.strftime('%Y-%m-%d'), param_ids[0], param_ids[1],
                     param_ids[2], param_ids[3], param_ids[4], param_ids[6])

# Define a directory containing:
# a) namelist.wps and namelist.input templates
# b) qsub template csh scripts for running geogrid, ungrib & metgrid, and real & wrf.
if args.t is not None:
    DIR_TEMPLATES = args.t + '/'
else:
    if on_cheyenne:
        DIR_TEMPLATES = '/glade/scratch/sward/met4ene/templates/ncartemplates/'
    elif on_aws:
        DIR_TEMPLATES = '/home/ec2-user/environment/met4ene/templates/awstemplates/'
    else:
        DIR_TEMPLATES = '/share/mzhang/jas983/wrf_data/met4ene/templates/magmatemplates/'
print('Using template directory:')
print(DIR_TEMPLATES)

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
elif on_aws:
    CMD_GEOGRID = './template_rungeogrid.csh'
    CMD_UNGMETG = './template_runungmetg.csh'
    CMD_REAL = './template_runreal.csh'
    CMD_WRF = './template_runwrf.csh'
else:
    CMD_GEOGRID = 'condor_submit sub.geogrid'
    CMD_UNGMETG = 'condor_submit sub.metgrid'
    CMD_REAL = 'condor_submit sub.real'
    CMD_WRF = 'condor_submit sub.wrf'

# Set the number of domains to that input, or default to a single domain. 
if args.d is not None and args.d > 0:
    MAX_DOMAINS = int(args.d)
else:
    MAX_DOMAINS = 3

# Try to remove the data dir, and print 'DIR_DATA not deleted' if you cannot. Then remake the dir, and enter it.
if remove_DIR_DATA:
    try:
        rmtree(DIR_DATA)
    except:
        print(DIR_DATA + ' not deleted')

if not path.exists(DIR_DATA):
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
    # Build the file list required for the WRF run.
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

    # Check to see if these files alread exist in DIR_DATA.


    # Download non-existent files from RDA. Probably put this into its own method...
    pswd = 'mkjmJ17'
    url = 'https://rda.ucar.edu/cgi-bin/login'
    values = {'email': 'jas983@cornell.edu', 'passwd': pswd, 'action': 'login'}

    # RDA user authentication
    ret = requests.post(url, data=values)
    if ret.status_code != 200:
        print('Bad Authentication')
        print(ret.text)
        exit(1)

    # Download files from RDA server
    for erafile in filelist:
        filename = dspath + erafile
        file_base = os.path.basename(erafile)
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
chdir(DIR_OUT)

# Try to remove the local tmp directory, and print 'DIR_WRFOUT not deleted' if you cannot.
# Then remake the dir, and enter it.
try:
    rmtree(DIR_LOCAL_TMP)
except:
    print(DIR_LOCAL_TMP + ' not deleted')
makedirs(DIR_LOCAL_TMP, 0755)
chdir(DIR_LOCAL_TMP)

# Link WRF tables, data, and executables.
cmd = CMD_LN % (DIR_WRF + 'run/aerosol*', './')
# cmd = cmd + '; ' +  CMD_LN % (DIR_WRF + 'run/BROADBAND*', './')
cmd = cmd + '; ' + CMD_LN % (DIR_WRF + 'run/bulk*', './')
cmd = cmd + '; ' + CMD_LN % (DIR_WRF + 'run/CAM*', './')
cmd = cmd + '; ' + CMD_LN % (DIR_WRF + 'run/capacity*', './')
cmd = cmd + '; ' + CMD_LN % (DIR_WRF + 'run/CCN*', './')
cmd = cmd + '; ' + CMD_LN % (DIR_WRF + 'run/CLM*', './')
cmd = cmd + '; ' + CMD_LN % (DIR_WRF + 'run/co2*', './')
cmd = cmd + '; ' + CMD_LN % (DIR_WRF + 'run/coeff*', './')
cmd = cmd + '; ' + CMD_LN % (DIR_WRF + 'run/constants*', './')
# cmd = cmd + '; ' +  CMD_LN % (DIR_WRF + 'run/create*', './')
cmd = cmd + '; ' + CMD_LN % (DIR_WRF + 'run/ETAMPNEW*', './')
cmd = cmd + '; ' + CMD_LN % (DIR_WRF + 'run/GENPARM*', './')
cmd = cmd + '; ' + CMD_LN % (DIR_WRF + 'run/grib2map*', './')
cmd = cmd + '; ' + CMD_LN % (DIR_WRF + 'run/gribmap*', './')
# cmd = cmd + '; ' +  CMD_LN % (DIR_WRF + 'run/HLC*', './')
# cmd = cmd + '; ' +  CMD_LN % (DIR_WRF + 'run/ishmael*', './')
cmd = cmd + '; ' + CMD_LN % (DIR_WRF + 'run/kernels*', './')
cmd = cmd + '; ' + CMD_LN % (DIR_WRF + 'run/LANDUSE*', './')
cmd = cmd + '; ' + CMD_LN % (DIR_WRF + 'run/masses*', './')
cmd = cmd + '; ' + CMD_LN % (DIR_WRF + 'run/MPTABLE*', './')
cmd = cmd + '; ' + CMD_LN % (DIR_WRF + 'run/ozone*', './')
# cmd = cmd + '; ' +  CMD_LN % (DIR_WRF + 'run/p3_lookup*', './')
cmd = cmd + '; ' + CMD_LN % (DIR_WRF + 'run/RRTM*', './')
cmd = cmd + '; ' + CMD_LN % (DIR_WRF + 'run/SOILPARM*', './')
cmd = cmd + '; ' + CMD_LN % (DIR_WRF + 'run/termvels*', './')
cmd = cmd + '; ' + CMD_LN % (DIR_WRF + 'run/tr*', './')
cmd = cmd + '; ' + CMD_LN % (DIR_WRF + 'run/URBPARM*', './')
cmd = cmd + '; ' + CMD_LN % (DIR_WRF + 'run/VEGPARM*', './')
cmd = cmd + '; ' + CMD_LN % (DIR_WRF + 'run/*exe', './')
system(cmd)
print(getcwd())
# Copy over namelists and Cheyenne submission scripts
if on_cheyenne:
    cmd = CMD_CP % (DIR_TEMPLATES + 'template_rungeogrid.csh', DIR_LOCAL_TMP)
    cmd = cmd + '; ' + CMD_CP % (DIR_TEMPLATES + 'template_runungmetg.csh', DIR_LOCAL_TMP)
    cmd = cmd + '; ' + CMD_CP % (DIR_TEMPLATES + 'template_runreal.csh', DIR_LOCAL_TMP)
    cmd = cmd + '; ' + CMD_CP % (DIR_TEMPLATES + 'template_runwrf.csh', DIR_LOCAL_TMP)
# else:
#    cmd = CMD_CP % (DIR_TEMPLATES + 'geogrid.csh', DIR_WRFOUT)
#    cmd = cmd + '; ' + CMD_CP % (DIR_TEMPLATES + 'geogrid.sub', DIR_WRFOUT)
#    cmd = cmd + '; ' + CMD_CP % (DIR_TEMPLATES + 'metgrid.csh', DIR_WRFOUT)
#    cmd = cmd + '; ' + CMD_CP % (DIR_TEMPLATES + 'metgrid.sub', DIR_WRFOUT)
#    cmd = cmd + '; ' + CMD_CP % (DIR_TEMPLATES + 'real.csh', DIR_WRFOUT)
#    cmd = cmd + '; ' + CMD_CP % (DIR_TEMPLATES + 'real.sub', DIR_WRFOUT)
#    cmd = cmd + '; ' + CMD_CP % (DIR_TEMPLATES + 'wrf.csh', DIR_WRFOUT)
#    cmd = cmd + '; ' + CMD_CP % (DIR_TEMPLATES + 'wrf.sub', DIR_WRFOUT)
# cmd = cmd + '; ' + CMD_CP % (DIR_TEMPLATES + 'namelist.wps', DIR_WRFOUT)
# cmd = cmd + '; ' + CMD_CP % (DIR_TEMPLATES + 'namelist.input', DIR_WRFOUT)
else:
    cmd = CMD_CP % (DIR_TEMPLATES + '*', DIR_LOCAL_TMP)
system(cmd)

# Link the metgrid and geogrid dirs and executables as well as the correct variable table for the BC/IC data.
cmd = CMD_LN % (DIR_WPS + 'geogrid', './')
cmd = cmd + '; ' + CMD_LN % (DIR_WPS + 'geogrid.exe', './')
cmd = cmd + '; ' + CMD_LN % (DIR_WPS + 'ungrib.exe', './')
cmd = cmd + '; ' + CMD_LN % (DIR_WPS + 'metgrid', './')
cmd = cmd + '; ' + CMD_LN % (DIR_WPS + 'metgrid.exe', './')
cmd = cmd + '; ' + CMD_LN % (DIR_WPS + 'ungrib/Variable_Tables/Vtable.' + Vsfx, 'Vtable')
system(cmd)

# Try to open WPS and WRF namelists as readonly, and print an error if you cannot.
try:
    with open(DIR_LOCAL_TMP + 'namelist.wps', 'r') as namelist:
        NAMELIST_WPS = namelist.read()
    with open(DIR_LOCAL_TMP + 'namelist.input', 'r') as namelist:
        NAMELIST_WRF = namelist.read()
except IOError as e:
    print(e.errno)
    print(e)
    exit()

# Write the start and end dates to the WPS Namelist
wps_dates = ' start_date                     = '
for i in range(0, MAX_DOMAINS):
    wps_dates = wps_dates + forecast_start.strftime("'%Y-%m-%d_%H:%M:%S', ")
wps_dates = wps_dates + '\n end_date                     = '
for i in range(0, MAX_DOMAINS):
    wps_dates = wps_dates + forecast_end.strftime("'%Y-%m-%d_%H:%M:%S', ")

try:
    with open('namelist.wps', 'w') as namelist:
        namelist.write(NAMELIST_WPS.replace('%DATES%', wps_dates))
except IOError as e:
    print(e.errno)
    print(e)
    exit()

with open(DIR_LOCAL_TMP + 'namelist.wps', 'r') as namelist:
    NAMELIST_WPS = namelist.read()

# Write the GEOG data path to the WPS Namelist
geog_data = " geog_data_path = '" + DIR_WPS_GEOG + "'"
try:
    with open('namelist.wps', 'w') as namelist:
        namelist.write(NAMELIST_WPS.replace('%GEOG%', geog_data))
except IOError as e:
    print(e.errno)
    print(e)
    exit()

# Write the runtime info and start dates and times to the WRF Namelist
wrf_runtime = ' run_days                            = ' + str(delt.days - 1) + ',\n'
wrf_runtime = wrf_runtime + ' run_hours                           = ' + '0' + ',\n'
wrf_runtime = wrf_runtime + ' run_minutes                         = ' + '0' + ',\n'
wrf_runtime = wrf_runtime + ' run_seconds                         = ' + '0' + ','

try:
    with open('namelist.input', 'w') as namelist:
        namelist.write(NAMELIST_WRF.replace('%RUNTIME%', wrf_runtime))
except IOError as e:
    print(e.errno)
    print(e)
    exit()

with open('namelist.input', 'r') as namelist:
    NAMELIST_WRF = namelist.read()

wrf_dates = ' start_year                          = '
for i in range(0, MAX_DOMAINS):
    wrf_dates = wrf_dates + forecast_start.strftime('%Y, ')
wrf_dates = wrf_dates + '\n start_month                         = '
for i in range(0, MAX_DOMAINS):
    wrf_dates = wrf_dates + forecast_start.strftime('%m, ')
wrf_dates = wrf_dates + '\n start_day                           = '
for i in range(0, MAX_DOMAINS):
    wrf_dates = wrf_dates + forecast_start.strftime('%d, ')
wrf_dates = wrf_dates + '\n start_hour                          = '
for i in range(0, MAX_DOMAINS):
    wrf_dates = wrf_dates + forecast_start.strftime('%H, ')
wrf_dates = wrf_dates + '\n start_minute                        = '
for i in range(0, MAX_DOMAINS):
    wrf_dates = wrf_dates + '00, '
wrf_dates = wrf_dates + '\n start_second                        = '
for i in range(0, MAX_DOMAINS):
    wrf_dates = wrf_dates + '00, '
wrf_dates = wrf_dates + '\n end_year                            = '
for i in range(0, MAX_DOMAINS):
    wrf_dates = wrf_dates + forecast_end.strftime('%Y, ')
wrf_dates = wrf_dates + '\n end_month                           = '
for i in range(0, MAX_DOMAINS):
    wrf_dates = wrf_dates + forecast_end.strftime('%m, ')
wrf_dates = wrf_dates + '\n end_day                             = '
for i in range(0, MAX_DOMAINS):
    wrf_dates = wrf_dates + forecast_end.strftime('%d, ')
wrf_dates = wrf_dates + '\n end_hour                            = '
for i in range(0, MAX_DOMAINS):
    wrf_dates = wrf_dates + forecast_end.strftime('%H, ')
wrf_dates = wrf_dates + '\n end_minute                          = '
for i in range(0, MAX_DOMAINS):
    wrf_dates = wrf_dates + '00, '
wrf_dates = wrf_dates + '\n end_second                          = '
for i in range(0, MAX_DOMAINS):
    wrf_dates = wrf_dates + '00, '

with open('namelist.input', 'w') as namelist:
    namelist.write(NAMELIST_WRF.replace('%DATES%', wrf_dates))

# Write the physics paramerization scheme info to the WRF Namelist
with open('namelist.input', 'r') as namelist:
    NAMELIST_WRF = namelist.read()

wrf_physics = ' mp_physics                          = '
for i in range(0, MAX_DOMAINS):
    wrf_physics = wrf_physics + str(param_ids[0]) + ', '
wrf_physics = wrf_physics + '\n ra_lw_physics                       = '
for i in range(0, MAX_DOMAINS):
    wrf_physics = wrf_physics + str(param_ids[1]) + ', '
wrf_physics = wrf_physics + '\n ra_sw_physics                       = '
for i in range(0, MAX_DOMAINS):
    wrf_physics = wrf_physics + str(param_ids[2]) + ', '
wrf_physics = wrf_physics + '\n sf_surface_physics                  = '
for i in range(0, MAX_DOMAINS):
    wrf_physics = wrf_physics + str(param_ids[3]) + ', '
wrf_physics = wrf_physics + '\n bl_pbl_physics                      = '
for i in range(0, MAX_DOMAINS):
    wrf_physics = wrf_physics + str(param_ids[4]) + ', '
wrf_physics = wrf_physics + '\n cu_physics                          = '
wrf_physics = wrf_physics + str(param_ids[5]) + ', 0, 0,'
wrf_physics = wrf_physics + '\n sf_sfclay_physics                   = '
for i in range(0, MAX_DOMAINS):
    wrf_physics = wrf_physics + str(param_ids[6]) + ', '

# The following namelist options are only set if certain parameter choices are selected
if param_ids[6] in [1, 5, 7, 11]:
    wrf_physics = wrf_physics + '\n isfflx                              = 1, '
if param_ids[6] in [1]:
    wrf_physics = wrf_physics + '\n ifsnow                              = 1, '
if param_ids[1] in [1, 4] and param_ids[2] in [1, 4]:
    wrf_physics = wrf_physics + '\n icloud                              = 1, '
if param_ids[5] in [5, 93]:
    wrf_physics = wrf_physics + '\n maxiens                             = 1,'
if param_ids[5] in [93]:
    wrf_physics = wrf_physics + '\n maxens                              = 3,'
    wrf_physics = wrf_physics + '\n maxens2                             = 3,'
    wrf_physics = wrf_physics + '\n maxens3                             = 16,'
    wrf_physics = wrf_physics + '\n ensdim                              = 144,'

with open('namelist.input', 'w') as namelist:
    namelist.write(NAMELIST_WRF.replace('%PARAMS%', wrf_physics))
print('Done writing WRF namelist')

# LINK REMAING FILES, AND RUN THE WPS AND WRF EXECUTABLES
# Link the grib files
system(CMD_LINK_GRIB)

# Run geogrid if it has not already been run
startTime = datetime.now()
startTimeInt = int(time())
print('Starting Geogrid at: ' + str(startTime))
system(CMD_GEOGRID)
while not runwrf_finish_check('geogrid'):
    if (int(time()) - startTimeInt) < 1800:
        tm.sleep(2)
    else:
        print('ERROR: Geogrid took more than 30min to run... exiting.')
        exit()
elapsed = datetime.now() - startTime
print('Geogrid ran in: ' + str(elapsed))

# Run ungrib and metgrid
startTime = datetime.now()
startTimeInt = int(time())
print('Starting Ungrib and Metgrid at: ' + str(startTime))
system(CMD_UNGMETG)
while not runwrf_finish_check('metgrid'):
    if (int(time()) - startTimeInt) < 3600:
        tm.sleep(2)
    else:
        print('ERROR: Ungrib and Metgrid took more than 1hr to run... exiting.')
        exit()
elapsed = datetime.now() - startTime
print('Ungrib and Metgrid ran in: ' + str(elapsed))

# Run real
startTime = datetime.now()
startTimeInt = int(time())
print('Starting Real at: ' + str(startTime))
system(CMD_REAL)
while not runwrf_finish_check('real'):
    if (int(time()) - startTimeInt) < 3600:
        tm.sleep(2)
    else:
        print('ERROR: Real took more than 1hr to run... exiting.')
        exit()
elapsed = datetime.now() - startTime
print('Real ran in: ' + str(elapsed) + ' seconds')

# Run wrf
startTime = datetime.now()
startTimeInt = int(time())
print('Starting WRF at: ' + str(startTime))
system(CMD_WRF)
# Make the script sleep for 5 minutes to allow for the rsl.out.0000 file to reset.
tm.sleep(300)
while not runwrf_finish_check('wrf'):
    if (int(time()) - startTimeInt) < 86400:
        tm.sleep(10)
    else:
        print('ERROR: WRF took more than 24hrs to run... exiting.')
        exit()
print('WRF finished running at: ' + str(datetime.now()))
elapsed = datetime.now() - startTime
print('WRF ran in: ' + str(elapsed))

# Rename the wrfout files.
for n in range(1, MAX_DOMAINS + 1):
    system(CMD_MV % (DIR_LOCAL_TMP + 'wrfout_d0' + str(n) + '_' + forecast_start.strftime('%Y')
                     + '-' + forecast_start.strftime('%m') + '-' + forecast_start.strftime('%d')
                     + '_00:00:00', DIR_LOCAL_TMP + 'wrfout_d0' + str(n) + '.nc'))

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
CMD_REGRID = 'ncl in_yr=%s in_mo=%s in_da=%s \'WRFdir="%s"\' wrf2era.ncl' % \
             (forecast_start.strftime('%Y'), forecast_start.strftime('%m'),
              forecast_start.strftime('%d'), DIR_LOCAL_TMP)
system('pwd')
system(CMD_REGRID)
