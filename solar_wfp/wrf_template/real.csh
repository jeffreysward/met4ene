#!/bin/csh
set verbose
limit stacksize unlimited

hostname
date

# for hp350 running gfortran version
# # setenv LD_LIBRARY_PATH /usr/local/lib
#
# #  this will create namelist.input, link in met_em files, and
# #  run real and then wrf
#
# # setenv OMP_NUM_THREADS 12

set y = (2010 2011)
set m = (12 1)
set d = (31 6)

# directory in which met_em files are located
set mdir = "/share/mzhang/jas983/wrf_data/nyserda_12-4-133/wpsprd_NAMANL"

set digits  = (01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31)
set hdig = (00 03 06 09 12 15 18 21)
set ndays = ( 31 28 31 30 31 30 31 31 30 31 30 31 )

set iy = $y[1]
set im = $m[1]
set id = $d[1]

set begyr=$y[1]
set begmo=$m[1]
@ begdy = $d[1] + 1
if ( $begdy > $ndays[$begmo] ) then
	set begdy = 01
	@ begmo = $begmo + 1
	if ( $begmo > 12 ) then
		set begmo = 1
		@ begyr = $begyr + 1
	endif
endif

# -----------     create namelist for model run  ----------------------------

cat nam1.template > namelist.input

cat << -eof- >> namelist.input
 start_year                          = $begyr, $begyr, $begyr,
 start_month                         = $begmo,   $begmo,   $begmo,
 start_day                           = $begdy,   $begdy,   $begdy,
 start_hour                          = 00,   00,   00, 
 start_minute                        = 00,   00,   00,
 start_second                        = 00,   00,   00,
 end_year                            = $y[2], $y[2], $y[2],
 end_month                           = $m[2],   $m[2],   $m[2],
 end_day                             = $d[2],   $d[2],   $d[2],
 end_hour                            = 00,   00,   00,
 end_minute                          = 00,   00,   00,
 end_second                          = 00,   00,   00,
-eof-

cat nam2.template >> namelist.input

# link OBS_DOMAIN301 for fdda
ln -s OBS_DOMAIN201-1 OBS_DOMAIN201
ln -s OBS_DOMAIN301-1 OBS_DOMAIN301
ln -s ../../nyserda_12-4-133/obsgrid_jan01-05/wrfsfdda_d01_${begyr}-$digits[$begmo]-$digits[$begdy] wrfsfdda_d01
ln -s ../../nyserda_12-4-133/obsgrid_jan01-05/wrfsfdda_d02_${begyr}-$digits[$begmo]-$digits[$begdy] wrfsfdda_d02
ln -s ../../nyserda_12-4-133/obsgrid_jan01-05/wrfsfdda_d03_${begyr}-$digits[$begmo]-$digits[$begdy] wrfsfdda_d03


echo Starting real
date

./real.exe
