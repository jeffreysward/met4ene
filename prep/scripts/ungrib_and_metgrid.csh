#!/bin/csh

#PBS -N run_geogrid
#PBS -A UCOR0037
#PBS -l walltime=00:30:00
#PBS -q regular
#PBS -j oe
#PBS -m abe
#PBS -M jas983@cornell.edu 
#PBS -l select=2:ncpus=1:mpiprocs=1

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
set yr = (2011 2011)
set mo = (08 08)
set da = (10 20) 
set day_start = "$yr[1]-$mo[1]-$da[1]_00:00:00"
set day_end = "$yr[2]-$mo[2]-$da[2]_21:00:00"

###  set the prefix to the data files
set datatype = "NARR"
set dir = "/gpfs/fs1/collections/rda/data/ds608.0/3HRLY/$yr[1]"
set fileprfx = "NARR3D_$yr[1]$mo[1]"
set namprfx="merged_AWIP32.$yr[1]$mo[1]"

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

if ( -f $dir/$namprfx"$yr[1]$mo[1]$da[1]00.3D" ) then
        echo These grib 2 files have already been unacrchived.
else
        echo Unarchiving grib 2 data...
        cat $dir/$fileprfx* | tar -xvf - -i -C $datdir
endif

### ---------------  link in the grib files --------------

./link_grib.csh $datdir/$namprfx

### ---------------  run ungrib  -------------------------

./ungrib.exe

### ---------------  get rid of links to raw grib file----

rm -f GRIBFILE.*

### ---------------  run metgrid  ------------------------

./metgrid.exe

### ---------------  get rid of ungrib intermediate files-

rm -f FILE*

echo Done
exit