#!/bin/csh

### This script runs WRF all the way through.

set wpsdir="/glade/scratch/$USER/wps"
set wrfdir = "/glade/scratch/sward/met4ene/wrfwrk/ARW/template_optNYpvw/2011aug10-20/template_wrf_z46"
cd $wpsdir

### Set up the WPS directory
./set_up_links_and_cp_files

### Check to see if geo_em files already exist


### Run ungrib and metgrid
qsub ungrib_and_metgrid.csh

### Run real 
cd $wrfdir
./link_wrf_stuff.csh
qsub 
### Run wrf
cd