#!/usr/local/bin/python

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
#arg.add_argument('-s', help="Start Date")
#arg.add_argument('-e', help="End Date")
arg.add_argument('-d', help="Max Domains")
arg.add_argument('-t', help="Namelist Template Directory")
arg.add_argument('-H', help="Path to host list file")
args = arg.parse_args()

# This looks like something that I can use to input a single date for a forecast. 
# I assume that the underscore is to avoid conflict with existing python commands.
day_ = '01'
month_ = 6
year_ = 2016
hour_ = 0

DATE = datetime(day=int(day_), month=int(month_), year=int(year_), hour=int(hour_), minute=0, second=0)

# This sets directory names
DIR_OUT = getcwd() + '/'
DIR_LOCAL_TMP = '/glade/scratch/sward/tmp/%s/' % DATE.strftime('%Y-%m-%d_%H-%M-%S') #Needs editing
DIR_WRF_ROOT = '/glade/u/home/wrfhelp/PRE_COMPILED_CODE/%s/'
DIR_WPS = DIR_WRF_ROOT % 'WPSV4.1_intel_serial_large-file'
DIR_WRF = DIR_WRF_ROOT % 'WRFV4.1_intel_dmpar'
DIR_WPS_GEOG = '/glade/u/home/wrfhelp/WPS_GEOG/'
DIR_LA = '/glade/u/home/sward/land_atmosphere/' #Needs editing

# I think this defines a directory of templates presumably csh scripts for running real and wrf.
if args.t != None:
    DIR_TEMPLATES = args.t + '/'
else:
    DIR_TEMPLATES = '/glade/u/home/sward/land_atmosphere/templates/' #Needs editing

# It looks like these are command aliai
CMD_LN = 'ln -sf %s %s'
CMD_CP = 'cp %s %s'
CMD_MV = 'mv %s %s'
CMD_CHMOD = 'chmod -R %s %s'
CMD_LINK_GRIB = DIR_WPS + 'link_grib.csh /glade/scratch/sward/era5_data/*.grb' #Needs editing
CMD_GEOGRID = DIR_WPS + 'geogrid.exe >& log.geogrid'
CMD_UNGRIB = DIR_WPS + 'ungrib.exe >& log.ungrib'
CMD_METGRID = DIR_WPS + 'metgrid.exe >& log.metgrid'
CMD_REAL = 'qsub template_runreal.csh' #Are these templates assumed to be in DIR_LA?
CMD_WRF = 'qsub template_runwrf.csh'

# Set the number of domains as the input, or default to a single domain. 
if args.d != None and args.d > 0:
    MAX_DOMAINS = int(args.d)
else:
    MAX_DOMAINS = 1

# Try to open WPS and WRF namelists as readonly, and print an error if you cannot.
try:
    with open(DIR_TEMPLATES + 'namelist.wps', 'r') as namelist:
        NAMELIST_WPS = namelist.read()
    with open(DIR_TEMPLATES + 'namelist.input', 'r') as namelist:
        NAMELIST_WRF = namelist.read()
except:
    print('Error reading namelist files')
    exit()

# Try to remove the local tmp directory, and print 'not deleted' if you cannot. Then remake the dir, and enter it.
try: rmtree(DIR_LOCAL_TMP)
except: print('not deleted')
mkdir(DIR_LOCAL_TMP)
chdir(DIR_LOCAL_TMP)

# Copy over Cheyenne submission scripts
cmd = CMD_CP % (DIR_LA + 'template_rungeogrid.csh', DIR_LOCAL_TMP)
cmd = cmd + '; ' + CMD_CP % (DIR_LA + 'template_runmetgrid.csh', DIR_LOCAL_TMP)
cmd = cmd + '; ' + CMD_CP % (DIR_LA + 'template_runreal.csh', DIR_LOCAL_TMP)
cmd = cmd + '; ' + CMD_CP % (DIR_LA + 'template_runwrf.csh', DIR_LOCAL_TMP)
system(cmd)

# Link the metgrid and geogrid dirs as well as the correct variable table for the BC/IC data.
cmd = CMD_LN % (DIR_WPS + 'geogrid', './')
cmd = cmd + '; ' + CMD_LN % (DIR_WPS + 'metgrid', './')
cmd = cmd + '; ' + CMD_LN % (DIR_WPS + 'ungrib/Variable_Tables/Vtable.ERA-interim.pl', 'Vtable')
system(cmd)

# Link WRF tables and data.
cmd = CMD_LN % (DIR_WRF + '*.TBL', './')
cmd = cmd + '; ' + CMD_LN % (DIR_WRF + '*_DATA', './')
system(cmd)

# Insert Dates into Namelists. I think these next few lines are written to accomidate a RT forecast.
cur_hour = DATE.hour
if cur_hour >= 0 and cur_hour < 6: z = 0
elif cur_hour >= 6 and cur_hour < 12: z = 6
elif cur_hour >= 12 and cur_hour < 18: z = 12
else: z = 18

# Here the number of days has been hard-coded to 91 days (correct?).
run_date = DATE.replace(hour = z,minute = 0,second = 0,microsecond = 0)
forecast_start = run_date
forecast_end = forecast_start + timedelta(days = 91, hours = 0)
print(forecast_start)
print (forecast_end)

# Write the start and end dates to the WPS Namelist
wps_dates = ' start_date = '
for i in range(0, MAX_DOMAINS):
    wps_dates = wps_dates + forecast_start.strftime("'%Y-%m-%d_%H:%M:%S', ") + forecast_start.strftime("'%Y-%m-%d_%H:%M:%S', ")+ forecast_start.strftime("'%Y-%m-%d_%H:%M:%S', ")
wps_dates = wps_dates + '\n end_date = '
for i in range(0, MAX_DOMAINS):
    wps_dates = wps_dates + forecast_end.strftime("'%Y-%m-%d_%H:%M:%S', ") + forecast_end.strftime("'%Y-%m-%d_%H:%M:%S', ") + forecast_end.strftime("'%Y-%m-%d_%H:%M:%S', ")

with open('namelist.wps', 'w') as namelist:
    namelist.write(NAMELIST_WPS.replace('%DATES%', wps_dates))

# Write the start and end dates and times to the WRF Namelist
wrf_dates = ' start_year = '
for i in range(0, MAX_DOMAINS):
    wrf_dates = wrf_dates + forecast_start.strftime('%Y, ') + forecast_start.strftime('%Y, ') + forecast_start.strftime('%Y, ')
wrf_dates = wrf_dates + '\n start_month = '
for i in range(0, MAX_DOMAINS):
    wrf_dates = wrf_dates + forecast_start.strftime('%m, ') + forecast_start.strftime('%m, ') + forecast_start.strftime('%m, ')
wrf_dates = wrf_dates + '\n start_day = '
for i in range(0, MAX_DOMAINS):
    wrf_dates = wrf_dates + forecast_start.strftime('%d, ') + forecast_start.strftime('%d, ') + forecast_start.strftime('%d, ')
wrf_dates = wrf_dates + '\n start_hour = '
for i in range(0, MAX_DOMAINS):
    wrf_dates = wrf_dates + forecast_start.strftime('%H, ') + forecast_start.strftime('%H, ') + forecast_start.strftime('%H, ')
wrf_dates = wrf_dates + '\n start_minute = '
for i in range(0, MAX_DOMAINS):
    wrf_dates = wrf_dates + '00, ' + '00, ' + '00, '
wrf_dates = wrf_dates + '\n start_second = '
for i in range(0, MAX_DOMAINS):
    wrf_dates = wrf_dates + '00, ' + '00, ' + '00, '
wrf_dates = wrf_dates + '\n end_year = '
for i in range(0, MAX_DOMAINS):
    wrf_dates = wrf_dates + forecast_end.strftime('%Y, ') + forecast_end.strftime('%Y, ') + forecast_end.strftime('%Y, ')
wrf_dates = wrf_dates + '\n end_month = '
for i in range(0, MAX_DOMAINS):
    wrf_dates = wrf_dates + forecast_end.strftime('%m, ') + forecast_end.strftime('%m, ') + forecast_end.strftime('%m, ')
wrf_dates = wrf_dates + '\n end_day = '
for i in range(0, MAX_DOMAINS):
    wrf_dates = wrf_dates + forecast_end.strftime('%d, ') + forecast_end.strftime('%d, ') + forecast_end.strftime('%d, ')
wrf_dates = wrf_dates + '\n end_hour = '
for i in range(0, MAX_DOMAINS):
    wrf_dates = wrf_dates + forecast_end.strftime('%H, ') + forecast_end.strftime('%H, ') + forecast_end.strftime('%H, ')
wrf_dates = wrf_dates + '\n end_minute = '
for i in range(0, MAX_DOMAINS):
    wrf_dates = wrf_dates + '00, ' + '00, ' + '00, '
wrf_dates = wrf_dates + '\n end_second = '
for i in range(0, MAX_DOMAINS):
    wrf_dates = wrf_dates + '00, ' + '00, ' + '00, '

with open('namelist.input', 'w') as namelist:
    namelist.write(NAMELIST_WRF.replace('%DATES%', wrf_dates))

# Link the grib files
hi = getcwd()
cmd = CMD_LINK_GRIB
system(cmd)

# Run geogrid
startTime = int(time())
system(CMD_GEOGRID)

##### Why is this commented out????? 
#while not os.path.exists(DIR_LOCAL_TMP + 'geo_em.d01.nc'):
#        tm.sleep(5)

elapsed = int(time()) - startTime
print('Geogrid ran in: ' + str(elapsed))

# Run ungrib
startTime = int(time())
system(CMD_UNGRIB)

elapsed = int(time()) - startTime
print('Ungrib ran in: ' + str(elapsed))

# Run metgrid
startTime = int(time())
system(CMD_METGRID)

elapsed = int(time()) - startTime
print('Metgrid ran in: ' + str(elapsed))

# Run real
startTime = int(time())
system(CMD_REAL)

while not os.path.exists(DIR_LOCAL_TMP + 'wrfinput_d03'):
	tm.sleep(5)

elapsed = int(time()) - startTime
print('Real ran in: ' + str(elapsed))

# Run wrf
startTime = int(time())
system(CMD_WRF)

##### The following needs editing to improve avoid hard coding.
while not os.path.exists(DIR_LOCAL_TMP + 'wrfout_d03_2016-06-01_00:00:00'):
	tm.sleep(10)

elapsed = int(time()) - startTime
print('WRF ran in: ' + str(elapsed))

# Rename the wrfout files.
system(CMD_MV % (DIR_LOCAL_TMP + 'wrfout_d01_2016-06-01_00:00:00', DIR_LOCAL_TMP + 'wrfout_d01.nc'))
system(CMD_MV % (DIR_LOCAL_TMP + 'wrfout_d02_2016-06-01_00:00:00', DIR_LOCAL_TMP + 'wrfout_d02.nc'))
system(CMD_MV % (DIR_LOCAL_TMP + 'wrfout_d03_2016-06-01_00:00:00', DIR_LOCAL_TMP + 'wrfout_d03.nc'))
