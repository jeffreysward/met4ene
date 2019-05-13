#!/bin/csh
set verbose
# This script extracts the desired fields from the wrfout netCDF files for the wind and solar work
##################################################################################################
# BEGIN USER INPUT SECTION
##################################################################################################
#set scen = "NYpvow_A5Dx3D"
#set scen = "NYpvow_A9Dx5D"
#set scen = "NYpvow_A1.9x1.9"
#set scen = "NYpvow_B5Dx3D"
#set scen = "NYpvow_B9Dx5D"
#set scen = "NYpvow_B1.9x1.9"
#set scen = "NYpvow_C5Dx3D"
#set scen = "NYpvow_C9Dx5D"
#set scen = "NYpvow_C1.9x1.9"
set scen = "NYpvow_D5Dx3D"
#set scen = "NYpvow_D9Dx5D"
#set scen = "NYpvow_D1.9x1.9"
set yr = 2011
#set mo = 01
#set mo = 05
#set mo = 07
set mo = 09
#set std = 24
#set std = 31
#set std = 22
set std = 14
set params = "z46r1bl5cu300ls2"

set outdir = "/share/mzhang/jas983/wrf_data/eas5555/post/wrf_xtract/"

##################################################################################################
# END USER INPUT SECTION
##################################################################################################
if ($mo == 01) then
	set month = "jan"
else if ($mo == 02) then
	set month = "feb"
else if ($mo == 03) then
	set month = "mar"
else if ($mo == 04) then
	set month = "apr"
else if ($mo == 05) then
	set month = "may"
else if ($mo == 06) then
	set month = "jun"
else if ($mo == 07) then
	set month = "jul"
else if ($mo == 08) then
	set month = "aug"
else if ($mo == 09) then
	set month = "sept"
else if ($mo == 10) then
	set month = "oct"
else if ($mo == 11) then
	set month = "nov"
else if ($mo == 12) then
	set month = "dec"
else
	echo That is not a valid month
	exit
endif
@ sud = $std - 1

set indir = "/share/mzhang/jas983/wrf_data/eas5555/wrfwrk/ARW/$scen/$yr$month$sud-$std/wrfrun_$params/"
echo The indir has been set to: $indir

# Extract data for offshore wind
set iwrfoutOW = "wrfout_d03_${yr}-${mo}-${std}_01*"
set owrfoutOW = "wrfout_OW_${scen}_${params}_d03_${yr}-${mo}-${std}"
ncks -v Times,POWER,WSPD100,XLAT,XLONG $indir$iwrfoutOW -O $outdir$owrfoutOW

# Extract data for solar
#set iwrfoutPV = "wrfout_d02_${yr}-${mo}-${std}_01*"
#set owrfoutPV = "wrfout_PV_${scen}_${params}_d02_${yr}-${mo}-${std}"
#ncks -v Times,SWDDNI,SWDDIF,T2,U10,V10 $indir$iwrfoutPV -O $outdir$owrfoutPV
