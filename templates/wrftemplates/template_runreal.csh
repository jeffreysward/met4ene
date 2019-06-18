#!/bin/csh
#PBS -N run_real
#PBS -A UCOR0037
#PBS -l walltime=00:30:00
#PBS -q regular
#PBS -j oe
#PBS -m abe
#PBS -M jas983@cornell.edu
#PBS -l select=1:ncpus=16:mpiprocs=16

limit stacksize unlimited

### -----------  run real ---------------------------

mpiexec_mpt ./real.exe

if (-f wrfinput_d03) then
        echo Done running real. Starting WRF...
else
        echo ERROR: wrf inputs were not created.
        exit
endif

exit
