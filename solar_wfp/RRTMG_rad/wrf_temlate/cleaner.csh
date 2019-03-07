#!/bin/csh
# This scrip cleans the directory if you need to rerun this period. 
rm errors.wrf 
rm output.wrf 
rm namelist.output
rm wrffdda_d01
rm wrfbdy_d01
rm wrfinput_d01
rm wrfinput_d02
rm wrfinput_d03
rm namelist.input
rm wrfinput_d03-0
rm wrfinput_d02-0
rm wrffdda_d01-0
rm wrfbdy_d01-0
rm wrfinput_d01-0
rm namelist.input-0
rm wrfout*
rm rsl*
rm met_em.d*
rm OBS_DOMAIN201
rm OBS_DOMAIN201-1
rm OBS_DOMAIN301
rm OBS_DOMAIN301-1
rm wrfsfdda_d01
rm wrfsfdda_d02
rm wrfsfdda_d03

echo Done cleaning up.
