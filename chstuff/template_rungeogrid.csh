#!/bin/csh
#PBS -N run_geogrid
#PBS -A UCOR0037
#PBS -l walltime=00:30:00
#PBS -q regular
#PBS -j oe
#PBS -m abe
#PBS -M <your email>
#PBS -l select=2:ncpus=36:mpiprocs=36
cd /glade/scratch/$USER/wrf/WPS # edit further to customize
###mpiexec_mpt -n 64 ./geogrid.exe
###mpiexec_mpt dplace -s 1 ./geogrid.exe
mpiexec_mpt ./geogrid.exe
exit
