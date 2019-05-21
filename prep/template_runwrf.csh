#!/bin/csh
#PBS -N run_wrf
#PBS -A UCOR0037
#PBS -l walltime=8:30:00
#PBS -q regular
#PBS -j oe
#PBS -m abe
#PBS -M jas983@cornell.edu
#PBS -l select=8:ncpus=32:mpiprocs=32

limit stacksize unlimited
mpiexec_mpt /glade/u/home/wrfhelp/PRE_COMPILED_CODE/WRFV4.1_intel_dmpar/test/em_real/wrf.exe

exit