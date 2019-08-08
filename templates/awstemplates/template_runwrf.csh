#!/bin/csh

limit stacksize unlimited

### -----------  run wrf ---------------------------

mpirun ./wrf.exe

rm -f met_em*

exit
