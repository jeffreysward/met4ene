#!/bin/bash

##########################################################
# This is the executable file that should be called via
# wrf_spinup.sub. This is script 2 of 4.
##########################################################

# Source the shell profile on each node
for i in /etc/profile.d/*.sh; do
	if [ -r "$i" ]; then
		if [ "$PS1" ]; then
			. $i
		else
			. $i >/dev/null 2>&1
		fi
	fi
done

# Load the requried modules
module load rocks-openmpi

# Call the WRF executable
echo Starting wrf for spin up...
date

mpirun ./wrf.exe 

mv namelist.input namelist.input-0
mv wrfinput_d03 wrfinput_d03-0
mv wrffdda_d02 wrffdda_d02-0
mv wrfinput_d02 wrfinput_d02-0
mv wrfbdy_d01 wrfbdy_d01-0
mv wrffdda_d01 wrffdda_d01-0
mv wrfinput_d01 wrfinput_d01-0
rm wrfsfdda_d01
rm wrfsfdda_d02
rm wrfsfdda_d03
#rm OBS_DOMAIN101
rm OBS_DOMAIN201
rm OBS_DOMAIN301

echo Done  with spin up

#5dayonly:
rm OBS_DOMAIN201
rm OBS_DOMAIN301
