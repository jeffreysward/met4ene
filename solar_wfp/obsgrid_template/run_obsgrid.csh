#!/bin/csh
#Note that I don't think I can submit this via condor because I 
#wont be able to source the bash profiles on the compute nodes
#without rewriting this script in bash.
set verbose
date
unlimit

#Link in the metfiles from the WPS directory
ln -s ../wps/met_em.*2010-12-26* .
ln -s ../wps/met_em.*2010-12-27* .
ln -s ../wps/met_em.*2010-12-28* .
ln -s ../wps/met_em.*2010-12-29* .
ln -s ../wps/met_em.*2010-12-30* .
ln -s ../wps/met_em.*2010-12-31* .
 
#Set the days that you intend to run and link observational data
set hours = ('00' '06' '12' '18')
set yr = 2010
set mo = 12
foreach day (27 28 29 30 31)
foreach hr (1 2 3 4)
ln -s /share/mzhang/jas983/wrf_data/raw_data/ds461/SURFACE_OBS:${yr}${mo}${day}$hours[$hr] SURFACE_OBS:${yr}-${mo}-${day}_$hours[$hr]
end
end

#This is the hour after the last day
ln -s /share/mzhang/jas983/wrf_data/raw_data/ds461/SURFACE_OBS:2011010100 SURFACE_OBS:2011-01-01_00

#Run OBSGRID for each domain (I could combine these, but it may not be worth it if the time difference is small)
foreach g (1 2 3)

cp namelist.input_d0${g} namelist.oa
/home/jas983/models/wrf/OBSGRID/src/obsgrid.exe
#This name change is to mark this for the start day... should improve this. 
mv wrfsfdda_d0${g} wrfsfdda_d0${g}_2010-12-27
date

end
