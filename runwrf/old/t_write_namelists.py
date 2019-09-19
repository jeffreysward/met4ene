#!/usr/bin/python

import os.path
from argparse import ArgumentParser
from datetime import datetime, timedelta
from os import chdir, getcwd, makedirs, system, path
from shutil import rmtree
from socket import gethostname
from subprocess import call
from sys import exit
from time import localtime, strftime, strptime, time
import time as tm
from wrfparams import name2num, generate, combine, filldefault, pbl2sfclay
import csv

# I think this is a command line interface; how are these arguments input?
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

# Reformat input start dates
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

# Next, we define the data directories and file prefixes on RDA which correspond
# to each specific type of input data
# ERA is the only supported data type right now
if args.b == 'ERA':
    DATA_ROOT1 = '/gpfs/fs1/collections/rda/data/ds627.0/ei.oper.an.pl/'
    DATA_ROOT1 = DATA_ROOT1 + forecast_start.strftime('%Y') + forecast_start.strftime('%m') + '/'
    datpfx1 = 'ei.oper.an.pl.regn128sc.'
    datpfx2 = 'ei.oper.an.pl.regn128uv.'
    DATA_ROOT2 = '/gpfs/fs1/collections/rda/data/ds627.0/ei.oper.an.sfc/'
    DATA_ROOT2 = DATA_ROOT2 + forecast_start.strftime('%Y') + forecast_start.strftime('%m') + '/'
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

# Set the sf_sfclay_pysics option based on that selected for PBL
id_sfclay = pbl2sfclay(param_ids[4])
param_ids.append(id_sfclay)

# sets directory names
DIR_OUT = getcwd() + '/'  # Needs Editing
DIR_LOCAL_TMP = '../wrfout/%s_%dmp%dlw%dsw%dlsm%dpbl%dcu/' % \
                (forecast_start.strftime('%Y-%m-%d'), param_ids[0], param_ids[1],
                 param_ids[2], param_ids[3], param_ids[4], param_ids[6])
DIR_WRF_ROOT = '/glade/u/home/wrfhelp/PRE_COMPILED_CODE/%s/'
DIR_WPS = DIR_WRF_ROOT % 'WPSV4.1_intel_serial_large-file'
DIR_WRF = DIR_WRF_ROOT % 'WRFV4.1_intel_dmpar'
DIR_WPS_GEOG = '/glade/u/home/wrfhelp/WPS_GEOG/'
DIR_DATA = '/glade/scratch/sward/data/' + str(args.b) + '/'

# I think this defines a directory of qsub template csh scripts for running geogrid, ungrib and metgrid, real, and wrf.
if args.t is not None:
    DIR_TEMPLATES = args.t + '/'
else:
    DIR_TEMPLATES = '../templates/wrftemplates/'

# Define command aliai
CMD_LN = 'ln -sf %s %s'
CMD_CP = 'cp %s %s'
CMD_MV = 'mv %s %s'
CMD_CHMOD = 'chmod -R %s %s'
CMD_LINK_GRIB = DIR_WPS + 'link_grib.csh ' + DIR_DATA + '*' #Needs editing
CMD_GEOGRID = 'qsub template_rungeogrid.csh'
# CMD_GEOGRID = DIR_WPS + 'geogrid.exe >& log.geogrid'
# CMD_UNGRIB = DIR_WPS + 'ungrib.exe >& log.ungrib'
# CMD_METGRID = DIR_WPS + 'metgrid.exe >& log.metgrid'
CMD_UNGMETG = 'qsub template_runungmetg.csh'
# CMD_REAL = 'qsub template_runreal.csh'
CMD_REALWRF = 'qsub template_runrealwrf.csh'

# Set the number of domains to that input, or default to a single domain.
if args.d is not None and args.d > 0:
    MAX_DOMAINS = int(args.d)
else:
    MAX_DOMAINS = 3

# Try to remove the local tmp directory, and print 'DIR_LOCAL_TMP not deleted' if you cannot.
# Then remake the dir, and enter it.
try: rmtree(DIR_LOCAL_TMP)
except: print(DIR_LOCAL_TMP + ' not deleted')
os.makedirs(DIR_LOCAL_TMP, 0755)

# Copy over namelists and Cheyenne submission scripts
cmd = CMD_CP % (DIR_TEMPLATES + 'template_rungeogrid.csh', DIR_LOCAL_TMP)
cmd = cmd + '; ' + CMD_CP % (DIR_TEMPLATES + 'template_runungmetg.csh', DIR_LOCAL_TMP)
cmd = cmd + '; ' + CMD_CP % (DIR_TEMPLATES + 'template_runreal.csh', DIR_LOCAL_TMP)
cmd = cmd + '; ' + CMD_CP % (DIR_TEMPLATES + 'template_runwrf.csh', DIR_LOCAL_TMP)
cmd = cmd + '; ' + CMD_CP % (DIR_TEMPLATES + 'namelist.wps', DIR_LOCAL_TMP)
cmd = cmd + '; ' + CMD_CP % (DIR_TEMPLATES + 'namelist.input', DIR_LOCAL_TMP)
system(cmd)

# Write parameter combinations to CSV
# (if you would like to restart this, you must manually delete this CSV)
runwrfcsv = 'paramfeed_runwrf.csv'
if not os.path.exists(runwrfcsv):
    csvData = [['ra_lw_physics', 'ra_sw_physics', 'sf_surface_physics',
                'bl_pbl_physics', 'cu_physics', 'sf_sfclay_physics'], param_ids]
    with open(runwrfcsv, 'w') as csvFile:
        writer = csv.writer(csvFile)
        writer.writerows(csvData)
else:
    with open(runwrfcsv, 'a') as csvFile:
        writer = csv.writer(csvFile)
        writer.writerow(param_ids)

# I AM NOW CHANGING INTO THE LOCAL TEMP DIRECTORY - BE CAREFULE WITH ABSOLUTE VS. RELATIVE PATHS
os.chdir(DIR_LOCAL_TMP)

# Try to open WPS and WRF namelists as readonly, and print an error if you cannot.
try:
    with open('namelist.wps', 'r') as namelist:
        NAMELIST_WPS = namelist.read()
    with open('namelist.input', 'r') as namelist:
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
