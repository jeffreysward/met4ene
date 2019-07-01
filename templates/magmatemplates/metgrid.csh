#!/bin/csh
set verbose

### ---------------  run ungrib  -------------------------

./ungrib.exe

### ---------------  get rid of links to raw grib file----

rm -f GRIBFILE.*

### ---------------  run metgrid  ------------------------

./metgrid.exe

### ---------------  get rid of ungrib intermediate files-

rm -f FILE*

exit