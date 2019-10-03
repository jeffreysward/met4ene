#!/bin/tcsh
# This script downloads and installs all the required wrf libraries into the specified diretory

echo "Installing packages required by WRF..."

setenv DIR /home/jas983/models/wrf/LIBRARIES/default_libs
setenv DATA_dir /home/jas983/models/wrf/DATA
setenv CC gcc
setenv CXX g++
setenv FC gfortran
setenv FCFLAGS -m64
setenv F77 gfortran
setenv FFLAGS -m64
setenv JASPERLIB $DIR/grib2/lib
setenv JASPERINC $DIR/grib2/include
setenv LDFLAGS -L$DIR/grib2/lib
setenv CPPFLAGS -I$DIR/grib2/include

# Check to see if the LIBRARIES dir exists
if ( ! -d $DIR ) then
   mkdir -p $DIR
endif

cd $DIR

# Install NetCDF
wget "http://www2.mmm.ucar.edu/wrf/OnLineTutorial/compile_tutorial/tar_files/netcdf-4.1.3.tar.gz"
tar xzvf netcdf-4.1.3.tar.gz
cd netcdf-4.1.3
./configure --prefix=$DIR/netcdf --disable-dap --disable-netcdf-4 --disable-shared
make
make install
setenv PATH $DIR/netcdf/bin:$PATH
setenv NETCDF $DIR/netcdf
cd ..

# Install mpich
wget "http://www2.mmm.ucar.edu/wrf/OnLineTutorial/compile_tutorial/tar_files/mpich-3.0.4.tar.gz"
tar xzvf mpich-3.0.4.tar.gz
cd mpich-3.0.4
./configure --prefix=$DIR/mpich
make && make install
setenv PATH $DIR/mpich/bin:$PATH
cd ..

# Install zlib
setenv JASPERLIB $DIR/grib2/lib 
setenv JASPERINC $DIR/grib2/include
wget "http://www2.mmm.ucar.edu/wrf/OnLineTutorial/compile_tutorial/tar_files/zlib-1.2.7.tar.gz"
tar xzvf zlib-1.2.7.tar.gz
cd zlib-1.2.7
./configure --prefix=$DIR/grib2
make && make install
cd ..

# Install libpng
wget "http://www2.mmm.ucar.edu/wrf/OnLineTutorial/compile_tutorial/tar_files/libpng-1.2.50.tar.gz"
tar xzvf libpng-1.2.50.tar.gz
cd libpng-1.2.50
./configure --prefix=$DIR/grib2
make && make install
cd ..

# Install jasperlib
wget "http://www2.mmm.ucar.edu/wrf/OnLineTutorial/compile_tutorial/tar_files/jasper-1.900.1.tar.gz"
tar xzvf jasper-1.900.1.tar.gz
cd jasper-1.900.1
./configure --prefix=$DIR/grib2
make && make install
cd ../../.. #change back into the wrf dir

# Clone the WRF repository and compile the executables
#git clone https://github.com/wrf-model/WRF
cd WRFV3
./configure #Choose options 34 and 1
./compile em_real >& log.compile.em_real
cd ..

# Clone the WPS repository 
#git clone https://github.com/wrf-model/WPS
#cd WPS
#./configure #Choose option 1
#./compile >& log.compile
#cd ../..

