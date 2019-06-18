#!/bin/csh
#PBS -N run_wrf
#PBS -A UCOR0037
#PBS -l walltime=8:00:00
#PBS -q regular
#PBS -j oe
#PBS -m abe
#PBS -M jas983@cornell.edu
#PBS -l select=4:ncpus=32:mpiprocs=32

limit stacksize unlimited

### -----------  run wrf ---------------------------

mpiexec_mpt ./wrf.exe

rm -f met_em*

exit
