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

echo Starting wrf
date

mpirun ./wrf.exe

echo Done  clean up
date

rm met_em.d*

rm OBS_DOMAIN201
rm OBS_DOMAIN201-1
rm OBS_DOMAIN301
rm OBS_DOMAIN301-1
rm wrfsfdda_d01
rm wrfsfdda_d02
rm wrfsfdda_d03
