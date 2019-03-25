#!/bin/csh

# This script runs OBSGRID for the desired period. 
# Submit this script via condor or run it directly on the NAS.

# Load gcc version 4.9.2
module load scl-3

set verbose
date
unlimit

# Set the directories in which the met_em files and surface observations are located
set metdir = "/share/mzhang/jas983/wrf_data/eas5555/solar_wfp/wps"
set surfdat = "/share/mzhang/jas983/wrf_data/raw_data/ds461"
set obsins = "/home/jas983/models/wrf/OBSGRID"

# Link the OBSGRID exe
ln -s $obsins/src/obsgrid.exe
# Set the days that you intend to run and link observational data
set hours = ('00' '06' '12' '18')
set yr = (2011 2011)
set mo = (01 01)
set d  = (23 24)
@   ed = $d[2] + 1
echo The end day is: $ed

set day = $d[1]
while ($day < $ed)
	#Link in the metfiles from the WPS directory
	ln -s $metdir/met_em.*${yr[1]}-${mo[1]}-$day* .
	foreach hr (1 2 3 4)
		ln -s $surfdat/SURFACE_OBS:${yr[1]}${mo[1]}${day}$hours[$hr] SURFACE_OBS:${yr}-${mo}-${day}_$hours[$hr]
	end
	@ day = $day + 1
end

#This is the hour after the last day
echo Linking : $metdir/met_em.*${yr[1]}-${mo[1]}-${ed}*
ln -s $metdir/met_em.*${yr[1]}-${mo[1]}-${ed}* .
echo Linking : $surfdat/SURFACE_OBS:${yr[1]}${mo[1]}${ed}00
ln -s $surfdat/SURFACE_OBS:${yr[1]}${mo[1]}${ed}00 SURFACE_OBS:${yr[1]}-${mo[1]}-${ed}_00

#Run OBSGRID for each domain (I could combine these, but it may not be worth it if the time difference is small)
foreach g (1 2 3)
	# Create namelist for the OBSGRID run.
	cat nam1.input > namelist.oa

cat << -eof- >> namelist.oa
 start_year                    = $yr[1]
 start_month                   = $mo[1]
 start_day                     = $d[1]
 start_hour                    = 00
 end_year                      = $yr[2]
 end_month                     = $mo[2]
 end_day                       = $ed
 end_hour                      = 00
-eof-
	
	cat nam2.input_d0${g} >> namelist.oa

	# Run the obsgrid execuable.
	./obsgrid.exe

	# This name change is to mark this for the start day. 
	mv wrfsfdda_d0${g} wrfsfdda_d0${g}_${yr}-${mo}-${d[1]}
	date

end
