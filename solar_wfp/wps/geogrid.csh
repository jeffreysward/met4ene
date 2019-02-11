#!/bin/bash

##########################################################
#  This is the executable file that should be called via
#  sub.geogrud.

#  geogrid.exe only needs to be rerun if the domain has changed

#  If you need to make changes to domain, intervals, options, make
#  the changes in nam1.template and nam2.template. 
##########################################################

# Source the shell profile on each node
for i in /etc/profile.d/*.sh; do
        if [ -r "$i" ]; then
		if [ "$PS1" ]; then
			. $i
		else
			. $i >/dev/null 2>&1
		fi
	fi
done

# Load the requried modules
module load scl-3
module load netcdf-gcc-4.6.1 
#ldconfig -p | grep netcdf

# Set desired environment variables
export CC="gcc"
export CXX="g++"
export FC="gfortran"
export FCFLAGS="-m64"
export F77="gfortran"
export FFLAGS="-m64"

export DIR="/home/jas983/models/wrf/LIBRARIES"
export JASPERLIB="$DIR/grib2/lib"
export JASPERINC="$DIR/grib2/include"
export NETCDF="$DIR/netcdf"
echo $NETCDF
export PATH="$PATH:/usr/lib64"
export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:/share/apps/mzhang/gnu/netcdf-4.6.1/lib"
export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:/home/jas983/models/wrf/LIBRARIES/grib2/lib"
echo $LD_LIBRARY_PATH
export PATH="$PATH:/home/jas983/post/ncview/bin"
export PATH="$PATH:$DIR/netcdf/bin"

# Run geogrid
echo Starting geogrid
set verbose

./geogrid.exe

echo Done 
