#!/bin/csh
set verbose
limit stacksize unlimited

date
####################################################################
# This script will create namelist.input, link in met_em files, and
# run real.exe. To run WRF on Magma, this is script 1 of 4!
####################################################################
# The following comment is only applicable to the icf system:
	# For hp350 running gfortran version
	# setenv LD_LIBRARY_PATH /usr/local/lib

# I'm not sure what the following option sets, but I suspect it
# controls paralellism on the icf system. Probably ignore it...
	# setenv OMP_NUM_THREADS 12

# Set the year (y), month (m), and day (d) for the spin up period.
set y = (2010 2011)
set m = (12 1)
set d = (31 6)

# Directory in which met_em files are located
# Note: you may have to unzip these first!
set mdir = "/share/mzhang/jas983/wrf_data/nyserda_12-4-133/wpsprd_NAMANL"

# This sets up all the nubers to index the days of the year:
# a) digits are the days of the year,
# b) hdig are the possible hour strings for the met files
# c) ndays are the number of days in each month.
set digits  = (01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31)
set hdig = (00 03 06 09 12 15 18 21)
set ndays = ( 31 28 31 30 31 30 31 31 30 31 30 31 )

# --------------  link met_em files ------------------------------

set iy = $y[1]
set im = $m[1]
set id = $d[1]
echo linking $mdir/met_em.d01.${iy}-$digits[${im}]-$digits[${id}]_12...nc
echo linking $mdir/met_em.d02.${iy}-$digits[${im}]-$digits[${id}]_12...nc
echo linking $mdir/met_em.d03.${iy}-$digits[${im}]-$digits[${id}]_12...nc
ln -sf $mdir/met_em.d01.${iy}-$digits[${im}]-$digits[${id}]_12*.nc .
ln -sf $mdir/met_em.d02.${iy}-$digits[${im}]-$digits[${id}]_12*.nc .
ln -sf $mdir/met_em.d03.${iy}-$digits[${im}]-$digits[${id}]_12*.nc .
ln -sf $mdir/met_em.d01.${iy}-$digits[${im}]-$digits[${id}]_15*.nc .
ln -sf $mdir/met_em.d02.${iy}-$digits[${im}]-$digits[${id}]_15*.nc .
ln -sf $mdir/met_em.d03.${iy}-$digits[${im}]-$digits[${id}]_15*.nc .
ln -sf $mdir/met_em.d01.${iy}-$digits[${im}]-$digits[${id}]_18*.nc .
ln -sf $mdir/met_em.d02.${iy}-$digits[${im}]-$digits[${id}]_18*.nc .
ln -sf $mdir/met_em.d03.${iy}-$digits[${im}]-$digits[${id}]_18*.nc .
ln -sf $mdir/met_em.d01.${iy}-$digits[${im}]-$digits[${id}]_21*.nc .
ln -sf $mdir/met_em.d02.${iy}-$digits[${im}]-$digits[${id}]_21*.nc .
ln -sf $mdir/met_em.d03.${iy}-$digits[${im}]-$digits[${id}]_21*.nc .

# We run for five total days (there are 8 3-hour periods each day)
foreach day (1 2 3 4 5)
	foreach hour (1 2 3 4 5 6 7 8)

		if ($im == 12 && $id == 31) then
			set iy = $y[2]
			set im = 1
			set id = 1
		else
			set im = $m[2]
			@ id = $d[2] - ( 6 - $day )
		endif

		if ($id < 1) then
			@ im = $m[2] - 1
			@ id = $ndays[$im] + $id
		endif
		echo 'y m d h' $iy $im $id $hour
		echo linking $mdir/met_em.d01.${iy}-$digits[$im]-$digits[$id]_$hdig[$hour]...nc
		echo linking $mdir/met_em.d02.${iy}-$digits[$im]-$digits[$id]_$hdig[$hour]...nc
		echo linking $mdir/met_em.d03.${iy}-$digits[$im]-$digits[$id]_$hdig[$hour]...nc
		ln -sf $mdir/met_em.d01.${iy}-$digits[$im]-$digits[$id]_$hdig[$hour]*.nc .
		ln -sf $mdir/met_em.d02.${iy}-$digits[$im]-$digits[$id]_$hdig[$hour]*.nc .
		ln -sf $mdir/met_em.d03.${iy}-$digits[$im]-$digits[$id]_$hdig[$hour]*.nc .

	end

	#cat /bt1/nyc_2017/raw_data/ds472/output/${iy}$digits[$im]$digits[$id].obs >> OBS_DOMAIN201-1
	#cat /bt1/nyc_2017/raw_data/ds472/output/${iy}$digits[$im]$digits[$id].obs >> OBS_DOMAIN301-1

end

set iy = $y[2]
set im = $m[2]
set id = $d[2]
echo linking $mdir/met_em.d01.${iy}-$digits[$im]-$digits[$id]_00*.nc
echo linking $mdir/met_em.d02.${iy}-$digits[$im]-$digits[$id]_00*.nc
echo linking $mdir/met_em.d03.${iy}-$digits[$im]-$digits[$id]_00*.nc
ln -sf $mdir/met_em.d01.${iy}-$digits[$im]-$digits[$id]_00*.nc .
ln -sf $mdir/met_em.d02.${iy}-$digits[$im]-$digits[$id]_00*.nc .
ln -sf $mdir/met_em.d03.${iy}-$digits[$im]-$digits[$id]_00*.nc .

cat ../../nyserda_12-4-133/obsgrid_2010dec27-31/OBS_DOMAIN2* >> OBS_DOMAIN201
cat ../../nyserda_12-4-133/obsgrid_2010dec27-31/OBS_DOMAIN3* >> OBS_DOMAIN301
cat ../../nyserda_12-4-133/obsgrid_jan01-05/OBS_DOMAIN2* >> OBS_DOMAIN201-1
cat ../../nyserda_12-4-133/obsgrid_jan01-05/OBS_DOMAIN3* >> OBS_DOMAIN301-1

# -----------  create namelist for spinup ----------------------------

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

#goto 5dayonly (I'm not sure what this means...)

# Write contents of nam1-0.template to namelist.input 
# (overwrites any existing namelist.input)
cat nam1-0.template > namelist.input

# I think this compares the values of the following section in namelist.input
# and then appends overwrites the start and end values.
cat << -eof- >> namelist.input
 start_year                          = $y[1], $y[1], $y[1],
 start_month                         = $m[1],   $m[1],   $m[1],
 start_day                           = $d[1],   $d[1],   $d[1],
 start_hour                          = 12,   12,   12,
 start_minute                        = 00,   00,   00,
 start_second                        = 00,   00,   00,
 end_year                            = $begyr, $begyr, $begyr,
 end_month                           = $begmo,   $begmo,   $begmo,
 end_day                             = $begdy,   $begdy,   $begdy,
 end_hour                            = 24,   24,   24,
 end_minute                          = 00,   00,   00,
 end_second                          = 00,   00,   00,
-eof-

# Append contents of nam2-0.template to namelist.input
cat nam2-0.template >> namelist.input

# Link OBS_DOMAIN301 for four dimensional data assimilation (fdda)
set mm = $m[1]
set dd = $d[1]
#ln -s /bt1/nyc_2017/raw_data/ds472/output/$y[1]$digits[$mm]$digits[$dd].obs OBS_DOMAIN201
#ln -s /bt1/nyc_2017/raw_data/ds472/output/$y[1]$digits[$mm]$digits[$dd].obs OBS_DOMAIN301
ln -s ../../nyserda_12-4-133/obsgrid_2010dec27-31/wrfsfdda_d01_$y[1]-12-27 wrfsfdda_d01
ln -s ../../nyserda_12-4-133/obsgrid_2010dec27-31/wrfsfdda_d02_$y[1]-12-27 wrfsfdda_d02
ln -s ../../nyserda_12-4-133/obsgrid_2010dec27-31/wrfsfdda_d03_$y[1]-12-27 wrfsfdda_d03

echo Starting real for spin up period...
date

./real.exe
