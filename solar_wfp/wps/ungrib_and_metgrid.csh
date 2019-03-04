#!/bin/csh
set verbose

#  Use of this script:
#
#  geogrid.exe should be run prior to running this script
#  geogrid.exe would only need to be rerun if the domain has changed
#
#  if you need to make changes to domain, intervals, options, make
#  the changes in nam1.template and nam2.template. This script will
#  overwrite an existing namelist.wps
#
#  Vtable should already be linked to the correct file prior to running
#  this script

# The WPS executables were compiled using the scl-3 compiler! 
module load scl-3

# Set the start date/time in day_start and end date/time in day_end

#set day_start = "2010-12-26_00:00:00"
#set day_end = "2010-12-31_21:00:00"
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
set day_start = "2011-04-01_00:00:00"
set day_end = "2011-04-30_21:00:00"
#set day_start = "2011-05-01_00:00:00"
#set day_end = "2011-05-31_21:00:00"
#set day_start = "2011-06-01_00:00:00"
#set day_end = "2011-06-05_21:00:00"
#set day_start = "2011-06-06_00:00:00"
#set day_end = "2011-06-06_21:00:00"
#set day_start = "2011-06-07_00:00:00"
#set day_end = "2011-06-15_21:00:00"
#set day_start = "2011-06-16_00:00:00"
#set day_end = "2011-06-29_21:00:00"
#set day_start = "2011-06-29_00:00:00"
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

#  set the prefix to the NAMANL filesi
set dir = "/share/mzhang/jas983/wrf_data/raw_data/NAMANL/"
#set fileprfx = "namanl_218_201012"
#set fileprfx = "namanl_218_201101"
#set fileprfx = "namanl_218_201102"
#set fileprfx = "namanl_218_201103"
set fileprfx = "namanl_218_201104"
#set fileprfx = "namanl_218_201105"
#set fileprfx = "namanl_218_201106"
#set fileprfx = "namanl_218_201107"
#set fileprfx = "namanl_218_201108"
#set fileprfx = "namanl_218_201109"
#set fileprfx = "namanl_218_201110"
#set fileprfx = "namanl_218_201111"
#set fileprfx = "namanl_218_201112"

#  (Here is a sample name /hp1/npl/wrf/data_ds608/NARR/merged_AWIP32.2008012915.3D )
#set namprfx="/share/mzhang/jas983/wrf_data/raw_data/NAMANL/nam_218_201012"
#set namprfx = "nam_218_201101"
#set namprfx = "nam_218_201102"
#set namprfx = "nam_218_201103"
set namprfx = "nam_218_201104"
#set namprfx = "nam_218_201105"
#set namprfx = "nam_218_201106"
#set namprfx = "nam_218_201107"
#set namprfx = "nam_218_201108"
#set namprfx = "nam_218_201109"
#set namprfx = "nam_218_201110"
#set namprfx = "nam_218_201111"
#set namprfx = "nam_218_201112"

# -------------      create namelist file -------------

cat nam1.template > namelist.wps

cat << -eof- >> namelist.wps
start_date = '$day_start','$day_start','$day_start',
end_date   = '$day_end','$day_end','$day_end',
-eof-

cat nam2.template >> namelist.wps

# -------------      unzip the grib files -------------
if ( -f $dir$namprfx"01_0000_000.grib2" ) then
	echo These grib 2 files have already been unacrchived.
else
	echo Unarchiving grib 2 data...
	cat $dir$fileprfx* | tar -xzvf - -i -C $dir
endif

#---------------  link in the grib files --------------

./link_grib.csh $dir$namprfx

#---------------  run ungrib  -------------------------

./ungrib.exe

#---------------  get rid of links to raw grib file----

rm GRIBFILE.*

#---------------  run metgrid  ------------------------

./metgrid.exe

rm FILE*

echo Done
