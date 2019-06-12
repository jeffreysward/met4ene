#!/bin/csh

#PBS -N run_geogrid
#PBS -A UCOR0037
#PBS -l walltime=00:30:00
#PBS -q regular
#PBS -j oe
#PBS -m abe
#PBS -M jas983@cornell.edu 
#PBS -l select=2:ncpus=36:mpiprocs=36

set verbose

###  Use of this script:
###
###  Submit this script via PBS by typing 'qsub ungrib_and_metgrid.csh'
###  geogrid should be run prior to running this script
###  geogrid would only need to be rerun if the domain has changed
###
###  If you need to make changes to domain, intervals, options, make
###  the changes in nam1.template and nam2.template. This script will
###  overwrite an existing namelist.wps
###
###  Vtable should already be linked to the correct file prior to running
###  this script


### Set the start date/time in day_start and end date/time in day_end

###set day_start = "2010-12-26_00:00:00"
###set day_end = "2010-12-31_21:00:00"
###set day_start = "2011-01-01_00:00:00"
###set day_end = "2011-01-05_21:00:00"
###set day_start = "2011-01-06_00:00:00"
###set day_end = "2011-01-15_21:00:00"
###set day_start = "2011-01-16_00:00:00"
###set day_end = "2011-01-31_21:00:00"
###set day_start = "2011-02-01_00:00:00"
###set day_end = "2011-02-05_21:00:00"
###set day_start = "2011-02-06_00:00:00"
###set day_end = "2011-02-28_21:00:00"
###set day_start = "2011-03-01_00:00:00"
###set day_end = "2011-03-02_21:00:00"
###set day_start = "2011-03-07_00:00:00"
###set day_end = "2011-03-31_21:00:00"
###set day_start = "2011-04-01_00:00:00"
###set day_end = "2011-04-01_21:00:00"
###set day_end = "2011-04-30_21:00:00"
###set day_start = "2011-05-01_00:00:00"
###set day_end = "2011-05-31_21:00:00"
###set day_start = "2011-06-01_00:00:00"
###set day_end = "2011-06-05_21:00:00"
###set day_start = "2011-06-06_00:00:00"
###set day_end = "2011-06-06_21:00:00"
###set day_start = "2011-06-07_00:00:00"
###set day_end = "2011-06-15_21:00:00"
###set day_start = "2011-06-16_00:00:00"
###set day_end = "2011-06-29_21:00:00"
###set day_start = "2011-06-29_00:00:00"
###set day_end = "2011-06-30_21:00:00"
set day_start = "2011-07-01_00:00:00"
set day_end = "2011-07-31_21:00:00"
###set day_start = "2011-08-01_00:00:00"
###set day_end = "2011-08-31_21:00:00"
###set day_start = "2011-09-01_00:00:00"
###set day_end = "2011-09-30_21:00:00"
###set day_start = "2011-10-01_00:00:00"
###set day_end = "2011-10-31_21:00:00"
###set day_start = "2011-11-01_00:00:00"
###set day_end = "2011-11-30_21:00:00"
###set day_start = "2011-12-01_00:00:00"
###set day_end = "2011-12-31_21:00:00"

###  set the prefix to the data files
set datatype = "NARR"
### set datatype = "NAMANL"
set dir = "/gpfs/fs1/collections/rda/data/ds608.0/3HRLY/2011"
set fileprfx = "NARR3D_201107"

###set fileprfx = "namanl_218_201012"
###set fileprfx = "namanl_218_201101"
###set fileprfx = "namanl_218_201102"
###set fileprfx = "namanl_218_201103"
###set fileprfx = "namanl_218_201104"
###set fileprfx = "namanl_218_201105"
###set fileprfx = "namanl_218_201106"
###set fileprfx = "namanl_218_201107"
###set fileprfx = "namanl_218_201108"
###set fileprfx = "namanl_218_201109"
###set fileprfx = "namanl_218_201110"
###set fileprfx = "namanl_218_201111"
###set fileprfx = "namanl_218_201112"

### set namprfx="merged_AWIP32.201107"

### set namprfx="nam_218_201012"
###set namprfx = "nam_218_201101"
###set namprfx = "nam_218_201102"
###set namprfx = "nam_218_201103"
###set namprfx = "nam_218_20110401"
###set namprfx = "nam_218_201105"
###set namprfx = "nam_218_201106"
###set namprfx = "nam_218_201107"
###set namprfx = "nam_218_201108"
###set namprfx = "nam_218_201109"
###set namprfx = "nam_218_201110"
###set namprfx = "nam_218_201111"
###set namprfx = "nam_218_201112"

### -------------      create namelist file -------------

cat nam1.template > namelist.wps

cat << -eof- >> namelist.wps
start_date = '$day_start','$day_start','$day_start',
end_date   = '$day_end','$day_end','$day_end',
-eof-

cat nam2.template >> namelist.wps

### -------------      unzip the grib files -------------
set datdir="/glade/scratch/$USER/data/$datatype"
if ( ! -d  $datdir ) then
	mkdir -p  $datdir
endif

if ( -f $dir$namprfx"2011071000.3D" ) then
	echo These grib 2 files have already been unacrchived.
else
	echo Unarchiving grib 2 data...
	cat $dir$fileprfx* | tar -xzvf - -i -C $datdir
endif

### ---------------  link in the grib files --------------

./link_grib.csh $datdir$namprfx

### ---------------  run ungrib  -------------------------

mpiexec_mpt ./ungrib.exe

### ---------------  get rid of links to raw grib file----

rm GRIBFILE.*

### ---------------  run metgrid  ------------------------

mpiexec_mpt ./metgrid.exe

### ---------------  get rid of ungrib intermediate files-

rm FILE*
rm PFILE*

echo Done
exit
