#!/bin/csh
#PBS -N run_real
#PBS -A UCOR0037
#PBS -l walltime=03:00:00
#PBS -q regular
#PBS -j oe
#PBS -m abe
#PBS -M jas983@cornell.edu
#PBS -l select=1:ncpus=32:mpiprocs=32
cd /glade/scratch/$USER/wrf/WRF/test/em_real/
### mpiexec_mpt -n 64 ./real.exe
### mpiexec_mpt dplace -s 1 ./real.exe
mpiexec_mpt ./real.exe
exit
