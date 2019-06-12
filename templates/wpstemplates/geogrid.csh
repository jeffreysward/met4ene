#!/bin/csh

##########################################################
###  This is the executable file that should be called via
###  qsub

###  geogrid.exe only needs to be rerun if the domain has changed

###  If you need to make changes to domain, intervals, options, make
###  the changes in nam1.template and nam2.template. 
##########################################################

### Set options for PBS
#PBS -N run_geogrid
#PBS -A UCOR0037
#PBS -l walltime=00:30:00
#PBS -q regular
#PBS -j oe
#PBS -m abe
#PBS -M jas983@cornell.edu 
#PBS -l select=2:ncpus=36:mpiprocs=36

### Change to whe WPS working directory 
cd /glade/scratch/$USER/wps

### Run geogrid
echo Stating geogrid
set verbose

### mpiexec_mpt -n 64 ./geogrid.exe
### mpiexec_mpt dplace -s 1 ./geogrid.exe
mpiexec_mpt ./geogrid.exe

echo Done...
exit
