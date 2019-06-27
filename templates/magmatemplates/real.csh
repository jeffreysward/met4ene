#!/bin/csh
set verbose
limit stacksize unlimited

# Set the total number of processors
set nprocs = 32

mpirun -np $nprocs ./real.exe

exit