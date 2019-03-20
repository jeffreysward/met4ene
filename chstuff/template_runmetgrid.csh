#!/bin/csh
#PBS -N run_metgrid
#PBS -A UCOR0037
#PBS -l walltime=03:00:00
#PBS -q regular
#PBS -j oe
#PBS -m abe
#PBS -M <your email address>
#PBS -l select=2:ncpus=36:mpiprocs=36
cd /glade/scratch/$USER/wrf/WPS # edit further to customize
###mpiexec_mpt -n 64 ./metgrid.exe
###mpiexec_mpt dplace -s 1 ./metgrid.exe
mpiexec_mpt ./metgrid.exe

exit
