#!/bin/csh

#PBS -N run_real
#PBS -A UCOR0037
#PBS -l walltime=00:30:00
#PBS -q regular
#PBS -j oe
#PBS -m abe
#PBS -M jas983@cornell.edu 
#PBS -l select=2:ncpus=16:mpiprocs=16

set verbose
limit stacksize unlimited

date

###  This will create namelist.input, link in met_em files, and
###  run real and then wrf

################### BEGIN USER INPUT SECTION ####################

### Set the start and end date separately below
set y = (2011 2011)
set m = (8 8)
set d = (10 19)

### Directory in which met_em files and met_oa files are located
set mdir = "/glade/scratch/sward/wps"

################### END USER INPUT SECTION ######################

set digits  = ( 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 )
set ndays = ( 31 28 31 30 31 30 31 31 30 31 30 31 )

### --------------  link met_em files ------------------------------
set iy = $y[1]
set im = $m[1]
set id = $d[1]

while ( $id <= $d[2] ) 

	echo linking $mdir/met_em.d01.${iy}-$digits[$im]-$digits[$id]...nc
	echo linking $mdir/met_em.d02.${iy}-$digits[$im]-$digits[$id]...nc
	echo linking $mdir/met_em.d03.${iy}-$digits[$im]-$digits[$id]...nc
	ln -sf $mdir/met_em.d01.${iy}-$digits[$im]-$digits[$id]*.nc .
	ln -sf $mdir/met_em.d02.${iy}-$digits[$im]-$digits[$id]*.nc .
	ln -sf $mdir/met_em.d03.${iy}-$digits[$im]-$digits[$id]*.nc .

	@ id = $id + 1

	if ($im == 12 && $id > 31) then
		@ iy = $iy + 1
		set im = 1
		set id = 1
	else if ($id > $ndays[$im]) then
		@ im = $im + 1
		set id = 1
	endif


end

### -----------  create namelist ----------------------------
cat nam1.template > namelist.input

cat << -eof- >> namelist.input
 start_year                          = $y[1],   $y[1],   $y[1],
 start_month                         = $m[1],   $m[1],   $m[1],
 start_day                           = $d[1],   $d[1],   $d[1],
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

### -----------  link stuff from WRF run dir ----------------------------

./link_wrf_stuff.csh

### -----------  run real ----------------------------
echo Starting real...
date

mpiexec_mpt ./real.exe

date
echo Done running real.
