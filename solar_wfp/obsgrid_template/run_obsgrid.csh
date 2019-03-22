#!/bin/csh

# This script runs OBSGRID for the desired period. 
# Submit this script via condor or run it directly on the NAS.

set verbose
date
unlimit

# Set the directories in which the met_em files and surface observations are located
set metdir = "../wps"
set surfdat = "/share/mzhang/jas983/wrf_data/raw_data/ds461"

# Set the days that you intend to run and link observational data
set hours = ('00' '06' '12' '18')
set yr = 2011
set mo = 07
set sd = 10
set ed = 15

foreach day (10 11 12 13 14)
	#Link in the metfiles from the WPS directory
	ln -s $metdir/met_em.*${yr}-${mo}-$day* .
	foreach hr (1 2 3 4)
		ln -s $surfdat/SURFACE_OBS:${yr}${mo}${day}$hours[$hr] SURFACE_OBS:${yr}-${mo}-${day}_$hours[$hr]
	end
end

#This is the hour after the last day
ln -s $metdir/met_em.*${yr}-${mo}-${ed}* .
ln -s $surfdat/SURFACE_OBS:${yr}${mo}${ed}00 SURFACE_OBS:${yr}-${mo}-${ed}_00

#Run OBSGRID for each domain (I could combine these, but it may not be worth it if the time difference is small)
foreach g (1 2 3)

	cp namelist.input_d0${g} namelist.oa
	./obsgrid.exe
	# This name change is to mark this for the start day. 
	mv wrfsfdda_d0${g} wrfsfdda_d0${g}_${yr}-${mo}-${sd}
	date

end
