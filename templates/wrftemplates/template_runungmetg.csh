#!/bin/csh

#PBS -N run_ung_metg
#PBS -A UCOR0037
#PBS -l walltime=00:30:00
#PBS -q regular
#PBS -j oe
#PBS -m abe
#PBS -M jas983@cornell.edu 
#PBS -l select=1:ncpus=1:mpiprocs=1

limit stacksize unlimited

### ---------------  run ungrib  -------------------------

./ungrib.exe

### ---------------  get rid of links to raw grib file----

rm -f GRIBFILE.*

### ---------------  run metgrid  ------------------------

./metgrid.exe

### ---------------  get rid of ungrib intermediate files-

rm -f FILE*
rm -f PFILE*

exit
