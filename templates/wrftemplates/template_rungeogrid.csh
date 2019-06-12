#!/bin/csh

#PBS -N run_geogrid
#PBS -A UCOR0037
#PBS -l walltime=00:30:00
#PBS -q regular
#PBS -j oe
#PBS -m abe
#PBS -M jas983@cornell.edu 
#PBS -l select=1:ncpus=1:mpiprocs=1

limit stacksize unlimited
./geogrid.exe
exit
