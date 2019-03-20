#!/bin/csh
#PBS -N run_wrf
#PBS -A UCOR0037
#PBS -l walltime=8:30:00
#PBS -q regular
#PBS -j oe
#PBS -m abe
#PBS -M <your email address>
#PBS -l select=8:ncpus=32:mpiprocs=32
limit stacksize unlimited
cd /glade/scratch/$USER/wrf/WRF/test/em_real/
###mpiexec_mpt -n 64 ./wrf.exe
###mpiexec_mpt dplace -s 1 ./wrf.exe
mpiexec_mpt ./wrf.exe

exit
