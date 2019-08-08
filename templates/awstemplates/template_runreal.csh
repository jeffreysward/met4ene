#!/bin/csh

limit stacksize unlimited

### -----------  run real ---------------------------

mpirun ./real.exe

if (-f wrfinput_d03) then
        echo Done running real. Starting WRF...
else
        echo ERROR: wrf inputs were not created.
        exit
endif

exit
