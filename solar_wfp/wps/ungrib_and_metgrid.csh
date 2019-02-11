#!/bin/bash

##########################################################
#  This is the executable file that should be called via
#  sub.ungrib_metgrid.

#  geogrid.exe should be run prior to running this script
#  geogrid.exe would only need to be rerun if the domain has changed

#  if you need to make changes to domain, intervals, options, make
#  the changes in nam1.template and nam2.template. This script will
#  overwrite an existing namelist.wps

#  Vtable should already be linked to the correct file prior to running
#  this script
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
module load scl-3
module load netcdf-gcc-4.6.1 

# Set desired environment variables
export CC="gcc"
export CXX="g++"
export FC="gfortran"
export FCFLAGS="-m64"
export F77="gfortran"
export FFLAGS="-m64"

export DIR="/home/jas983/models/wrf/LIBRARIES"
export JASPERLIB="$DIR/grib2/lib"
export JASPERINC="$DIR/grib2/include"
export NETCDF="$DIR/netcdf"
export PATH="$PATH:/usr/lib64"
export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:/share/apps/mzhang/gnu/netcdf-4.6.1/lib"
export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:/home/jas983/models/wrf/LIBRARIES/grib2/lib"
export PATH="$PATH:$DIR/netcdf/bin"

echo Starting ungrib and metgrid
verbose

# Set the start date/time in day_start and end date/time in day_end

day_start = "2010-12-26_00:00:00"
day_end = "2010-12-31_21:00:00"
#set day_start = "2011-01-01_00:00:00"
#set day_end = "2011-01-05_21:00:00"
#set day_start = "2011-01-06_00:00:00"
#set day_end = "2011-01-15_21:00:00"
#set day_start = "2011-01-16_00:00:00"
#set day_end = "2011-01-31_21:00:00"
#set day_start = "2011-02-01_00:00:00"
#set day_end = "2011-02-05_21:00:00"
#set day_start = "2011-02-06_00:00:00"
#set day_end = "2011-02-28_21:00:00"
#set day_start = "2011-03-01_00:00:00"
#set day_end = "2011-03-02_21:00:00"
#set day_start = "2011-03-07_00:00:00"
#set day_end = "2011-03-31_21:00:00"
#set day_start = "2011-04-01_00:00:00"
#set day_end = "2011-04-30_21:00:00"
#set day_start = "2011-05-01_00:00:00"
#set day_end = "2011-05-31_21:00:00"
#set day_start = "2011-06-01_00:00:00"
#set day_end = "2011-06-05_21:00:00"
#set day_start = "2011-06-06_00:00:00"
#set day_end = "2011-06-06_21:00:00"
#set day_start = "2011-06-07_00:00:00"
#set day_end = "2011-06-15_21:00:00"
#set day_start = "2011-06-16_00:00:00"
#set day_end = "2011-06-30_21:00:00"
#set day_start = "2011-07-01_00:00:00"
#set day_end = "2011-07-31_21:00:00"
#set day_start = "2011-08-01_00:00:00"
#set day_end = "2011-08-31_21:00:00"
#set day_start = "2011-09-01_00:00:00"
#set day_end = "2011-09-30_21:00:00"
#set day_start = "2011-10-01_00:00:00"
#set day_end = "2011-10-31_21:00:00"
#set day_start = "2011-11-01_00:00:00"
#set day_end = "2011-11-30_21:00:00"
#set day_start = "2011-12-01_00:00:00"
#set day_end = "2011-12-31_21:00:00"
echo $day_start
echo $day_end

#  set the prefix to the NAMANL files
#  (Here is a sample name /hp1/npl/wrf/data_ds608/NARR/merged_AWIP32.2008012915.3D )
namprfx = "/share/mzhang/jas983/wrf_data/raw_data/NAMANL/nam_218_201012"
#set namprfx = "/share/mzhang/jas983/wrf_data/raw_data/NAMANL/nam_218_201101"
#set namprfx = "/share/mzhang/jas983/wrf_data/raw_data/NAMANL/nam_218_201102"
#set namprfx = "/share/mzhang/jas983/wrf_data/raw_data/NAMANL/nam_218_201106"
#set namprfx = "/share/mzhang/jas983/wrf_data/raw_data/NAMANL/nam_218_201107"
#set namprfx = "/share/mzhang/jas983/wrf_data/raw_data/NAMANL/nam_218_201108"
#set namprfx = "/share/mzhang/jas983/wrf_data/raw_data/NAMANL/nam_218_201109"
#set namprfx = "/share/mzhang/jas983/wrf_data/raw_data/NAMANL/nam_218_201110"
#set namprfx = "/share/mzhang/jas983/wrf_data/raw_data/NAMANL/nam_218_201111"
#set namprfx = "/share/mzhang/jas983/wrf_data/raw_data/NAMANL/nam_218_201112"
echo $namprfx

# -------------      create namelist file -------------

cat nam1.template > namelist.wps

cat << -eof- >> namelist.wps
start_date = '$day_start','$day_start','$day_start',
end_date   = '$day_end','$day_end','$day_end',
-eof-

cat nam2.template >> namelist.wps

#---------------  link in the grib files --------------

./link_grib.csh $namprfx

#---------------  run ungrib  -------------------------

./ungrib.exe

#---------------  get rid of links to raw grib file----

rm GRIBFILE.*

#---------------  run metgrid  ------------------------

./metgrid.exe

echo Done 
