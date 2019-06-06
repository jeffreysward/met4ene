#!/usr/bin/python

from argparse import ArgumentParser
from datetime import datetime, timedelta
from os import chdir, getcwd, mkdir, system
from shutil import rmtree
from socket import gethostname
from subprocess import call
from sys import exit
from time import localtime, strftime, strptime, time
import os.path
import time as tm

# I think this is a command line interface; how are these arguments input?
arg = ArgumentParser()
arg.add_argument('-s', help="Start Date", type=str)
arg.add_argument('-e', help="End Date", type=str)
arg.add_argument('-b', help="Boundary Conditon Data Source", type=str)
arg.add_argument('-d', help="Max Domains", type=int)
arg.add_argument('-t', help="Namelist Template Directory", type=str)
args = arg.parse_args()

forecast_start = datetime.strptime(args.s, '%b %d %Y')
#forecast_start = datetime.strptime(args.s, '%b %d %Y %H')
#forecast_start = datetime.strptime(args.s, '%b %d %Y %H:%M:%S')
forecast_end = datetime.strptime(args.e, '%b %d %Y')
delt = forecast_end - forecast_start
print(forecast_start)
print (forecast_end)

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

print(Vsfx)

# This sets directory names
DIR_OUT = getcwd() + '/' #Needs Editing
DIR_LOCAL_TMP = '/glade/scratch/sward/tmp/%s/' % forecast_start.strftime('%Y-%m-%d_%H-%M-%S')
DIR_WRF_ROOT = '/glade/u/home/wrfhelp/PRE_COMPILED_CODE/%s/'
DIR_WPS = DIR_WRF_ROOT % 'WPSV4.1_intel_serial_large-file'
DIR_WRF = DIR_WRF_ROOT % 'WRFV4.1_intel_dmpar'
DIR_WPS_GEOG = '/glade/u/home/wrfhelp/WPS_GEOG/'
DIR_DATA = '/glade/scratch/sward/data/' + str(args.b) + '/'

# I think this defines a directory of qsub template csh scripts for running geogrid, ungrib and metgrid, real, and wrf.
if args.t != None:
    DIR_TEMPLATES = args.t + '/'
else:
    DIR_TEMPLATES = '/glade/scratch/sward/met4ene/chstuff/wrftemplates/'

# Define command aliai
CMD_LN = 'ln -sf %s %s'
CMD_CP = 'cp %s %s'
CMD_MV = 'mv %s %s'
CMD_CHMOD = 'chmod -R %s %s'
CMD_LINK_GRIB = DIR_WPS + 'link_grib.csh ' + DIR_DATA + '*' #Needs editing
CMD_GEOGRID = 'qsub template_rungeogrid.csh'
#CMD_GEOGRID = DIR_WPS + 'geogrid.exe >& log.geogrid'
#CMD_UNGRIB = DIR_WPS + 'ungrib.exe >& log.ungrib' 
#CMD_METGRID = DIR_WPS + 'metgrid.exe >& log.metgrid' 
CMD_UNGMETG = 'qsub template_runungmetg.csh'
#CMD_REAL = 'qsub template_runreal.csh' 
CMD_REALWRF = 'qsub template_runrealwrf.csh'

# Set the number of domains to that input, or default to a single domain. 
if args.d != None and args.d > 0:
    MAX_DOMAINS = int(args.d)
else:
    MAX_DOMAINS = 3

# Try to remove the data dir, and print 'DIR_DATA not deleted' if you cannot. Then remake the dir, and enter it.
try: rmtree(DIR_DATA)
except: print(DIR_DATA + ' not deleted')
os.mkdir(DIR_DATA, 0755)
os.chdir(DIR_DATA)

# Copy desired data files from RDA
##### THIS ONLY WORKS IF YOU WANT TO RUN WITHIN A SINGLE MONTH
i = int(forecast_start.day)
n = int(forecast_start.day) + int(delt.days)
while i <= n:
    cmd = CMD_CP % (DATA_ROOT1 + datpfx1 + forecast_start.strftime('%Y') \
          + forecast_start.strftime('%m') + str(i) + '*', DIR_DATA)
    cmd = cmd + '; ' +  CMD_CP % (DATA_ROOT1 + datpfx2 + forecast_start.strftime('%Y') \
          + forecast_start.strftime('%m') + str(i) + '*', DIR_DATA)
    cmd = cmd + '; ' +  CMD_CP % (DATA_ROOT2 + datpfx3 + forecast_start.strftime('%Y') \
          + forecast_start.strftime('%m')+ str(i) + '*', DIR_DATA)
    os.system(cmd)
    i += 1 

# Try to remove the local tmp directory, and print 'DIR_LOCAL_TMP not deleted' if you cannot. Then remake the dir, and enter it.
try: rmtree(DIR_LOCAL_TMP)
except: print(DIR_LOCAL_TMP + ' not deleted')
os.mkdir(DIR_LOCAL_TMP, 0755)
os.chdir(DIR_LOCAL_TMP)

# Copy over namelists and Cheyenne submission scripts
cmd = CMD_CP % (DIR_TEMPLATES + 'template_rungeogrid.csh', DIR_LOCAL_TMP)
cmd = cmd + '; ' + CMD_CP % (DIR_TEMPLATES + 'template_runungmetg.csh', DIR_LOCAL_TMP)
cmd = cmd + '; ' + CMD_CP % (DIR_TEMPLATES + 'template_runrealwrf.csh', DIR_LOCAL_TMP)
cmd = cmd + '; ' + CMD_CP % (DIR_TEMPLATES + 'namelist.wps', DIR_LOCAL_TMP)
cmd = cmd + '; ' + CMD_CP % (DIR_TEMPLATES + 'namelist.input', DIR_LOCAL_TMP)
os.system(cmd)

# Link the metgrid and geogrid dirs and executables as well as the correct variable table for the BC/IC data.
cmd = CMD_LN % (DIR_WPS + 'geogrid', './')
cmd = cmd + '; ' + CMD_LN % (DIR_WPS + 'geogrid.exe', './')
cmd = cmd + '; ' + CMD_LN % (DIR_WPS + 'ungrib.exe', './')
cmd = cmd + '; ' + CMD_LN % (DIR_WPS + 'metgrid', './')
cmd = cmd + '; ' + CMD_LN % (DIR_WPS + 'metgrid.exe', './')
cmd = cmd + '; ' + CMD_LN % (DIR_WPS + 'ungrib/Variable_Tables/Vtable.' + Vsfx, 'Vtable')
os.system(cmd)

# Link WRF tables, data, and executables.
cmd = CMD_LN % (DIR_WRF + 'run/*.TBL', './')
cmd = cmd + '; ' + CMD_LN % (DIR_WRF + 'run/*_DATA', './')
cmd = cmd + '; ' + CMD_LN % (DIR_WRF + 'run/real.exe', './')
cmd = cmd + '; ' + CMD_LN % (DIR_WRF + 'run/wrf.exe', './')
os.system(cmd)

# Try to open WPS and WRF namelists as readonly, and print an error if you cannot.
try:
    with open(DIR_LOCAL_TMP + 'namelist.wps', 'r') as namelist:
        NAMELIST_WPS = namelist.read()
    with open(DIR_LOCAL_TMP + 'namelist.input', 'r') as namelist:
        NAMELIST_WRF = namelist.read()
except:
    print('Error reading namelist files')
    exit()

# Write the start and end dates to the WPS Namelist
wps_dates = ' start_date = '
for i in range(0, MAX_DOMAINS):
    wps_dates = wps_dates + forecast_start.strftime("'%Y-%m-%d_%H:%M:%S', ") 
wps_dates = wps_dates + '\n end_date  = '
for i in range(0, MAX_DOMAINS):
    wps_dates = wps_dates + forecast_end.strftime("'%Y-%m-%d_%H:%M:%S', ")

with open('namelist.wps', 'w') as namelist:
    namelist.write(NAMELIST_WPS.replace('%DATES%', wps_dates))

# Write the runtime info and start dates and times to the WRF Namelist
wrf_runtime = ' run_days                            = ' + str(delt.days - 1) + ',\n'
wrf_runtime = wrf_runtime + ' run_hours                           = ' + '0' + ',\n'
wrf_runtime = wrf_runtime + ' run_minutes                         = ' + '0' + ',\n'
wrf_runtime = wrf_runtime + ' run_seconds                         = ' + '0' + ','

with open('namelist.input', 'w') as namelist:
    namelist.write(NAMELIST_WRF.replace('%RUNTIME%', wrf_runtime))

with open(DIR_LOCAL_TMP + 'namelist.input', 'r') as namelist:
        NAMELIST_WRF = namelist.read()

wrf_dates = ' start_year = '
for i in range(0, MAX_DOMAINS):
    wrf_dates = wrf_dates + forecast_start.strftime('%Y, ')
wrf_dates = wrf_dates + '\n start_month = '
for i in range(0, MAX_DOMAINS):
    wrf_dates = wrf_dates + forecast_start.strftime('%m, ')
wrf_dates = wrf_dates + '\n start_day = '
for i in range(0, MAX_DOMAINS):
    wrf_dates = wrf_dates + forecast_start.strftime('%d, ')
wrf_dates = wrf_dates + '\n start_hour = '
for i in range(0, MAX_DOMAINS):
    wrf_dates = wrf_dates + forecast_start.strftime('%H, ')
wrf_dates = wrf_dates + '\n start_minute = '
for i in range(0, MAX_DOMAINS):
    wrf_dates = wrf_dates + '00, '
wrf_dates = wrf_dates + '\n start_second = '
for i in range(0, MAX_DOMAINS):
    wrf_dates = wrf_dates + '00, '
wrf_dates = wrf_dates + '\n end_year = '
for i in range(0, MAX_DOMAINS):
    wrf_dates = wrf_dates + forecast_end.strftime('%Y, ')
wrf_dates = wrf_dates + '\n end_month = '
for i in range(0, MAX_DOMAINS):
    wrf_dates = wrf_dates + forecast_end.strftime('%m, ')
wrf_dates = wrf_dates + '\n end_day = '
for i in range(0, MAX_DOMAINS):
    wrf_dates = wrf_dates + forecast_end.strftime('%d, ')
wrf_dates = wrf_dates + '\n end_hour = '
for i in range(0, MAX_DOMAINS):
    wrf_dates = wrf_dates + forecast_end.strftime('%H, ')
wrf_dates = wrf_dates + '\n end_minute = '
for i in range(0, MAX_DOMAINS):
    wrf_dates = wrf_dates + '00, '
wrf_dates = wrf_dates + '\n end_second = '
for i in range(0, MAX_DOMAINS):
    wrf_dates = wrf_dates + '00, '

with open('namelist.input', 'w') as namelist:
    namelist.write(NAMELIST_WRF.replace('%DATES%', wrf_dates))

# Link the grib files
os.system(CMD_LINK_GRIB)

# Run geogrid if it has not already been run
startTime = int(time())
os.system(CMD_GEOGRID)
	
while not os.path.exists(DIR_LOCAL_TMP + 'geo_em.d03.nc'):
        tm.sleep(10)

elapsed = int(time()) - startTime
print('Geogrid ran in: ' + str(elapsed))

# Run ungrib and metgrid
startTime = int(time())
os.system(CMD_UNGMETG)

while not os.path.exists(DIR_LOCAL_TMP + 'met_em.d03.' + forecast_end.strftime('%Y') \
    + '-' + forecast_end.strftime('%m') + '-' + forecast_end.strftime('%d') + '_00:00:00.nc'):
        tm.sleep(10)

elapsed = int(time()) - startTime
print('Ungrib and Metgrid ran in: ' + str(elapsed))

# Run real and wrf
startTime = int(time())
os.system(CMD_REALWRF)

while not os.path.exists(DIR_LOCAL_TMP + 'wrfout_d03_' + forecast_start.strftime('%Y') \
    + '-' + forecast_start.strftime('%m') + '-' + forecast_start.strftime('%d') + '_00:00:00'):
	tm.sleep(10)

elapsed = int(time()) - startTime
print('Real and WRF ran in: ' + str(elapsed))

# Rename the wrfout files.
os.system(CMD_MV % (DIR_LOCAL_TMP + 'wrfout_d01_' + forecast_start.strftime('%Y') \
    + '-' + forecast_start.strftime('%m') + '-' + forecast_start.strftime('%d') \
    + '_00:00:00', DIR_LOCAL_TMP + 'wrfout_d01.nc'))
os.system(CMD_MV % (DIR_LOCAL_TMP + 'wrfout_d02_' + forecast_start.strftime('%Y') \
    + '-' + forecast_start.strftime('%m') + '-' + forecast_start.strftime('%d') \
    + '_00:00:00', DIR_LOCAL_TMP + 'wrfout_d02.nc'))
os.system(CMD_MV % (DIR_LOCAL_TMP + 'wrfout_d03_' + forecast_start.strftime('%Y') \
    + '-' + forecast_start.strftime('%m') + '-' + forecast_start.strftime('%d') \
    + '_00:00:00', DIR_LOCAL_TMP + 'wrfout_d03.nc'))
