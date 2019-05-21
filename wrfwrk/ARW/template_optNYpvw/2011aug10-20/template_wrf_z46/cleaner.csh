#!/bin/csh
# This scrip cleans the directory if you need to rerun this period. 
rm -f errors.wrf 
rm -f output.wrf 
rm -f namelist.output
rm -f wrffdda_d01
rm -f wrfbdy_d01
rm -f wrfinput_d01
rm -f wrfinput_d02
rm -f wrfinput_d03
rm -f namelist.input
rm -f wrfinput_d03-0
rm -f wrfinput_d02-0
rm -f wrffdda_d01-0
rm -f wrfbdy_d01-0
rm -f wrfinput_d01-0
rm -f namelist.input-0
rm -f wrfout*
rm -f rsl*
rm -f met_em.d*
rm -f OBS_DOMAIN201
rm -f OBS_DOMAIN201-1
rm -f OBS_DOMAIN301
rm -f OBS_DOMAIN301-1
rm -f wrfsfdda_d01
rm -f wrfsfdda_d02
rm -f wrfsfdda_d03

echo Done cleaning up.
