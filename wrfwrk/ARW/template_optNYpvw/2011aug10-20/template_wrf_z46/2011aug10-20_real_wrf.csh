#!/bin/csh
set verbose
limit stacksize unlimited

date

#  This will create namelist.input, link in met_em files, and
#  run real and then wrf

################### BEGIN USER INPUT SECTION ####################

# Set the total number of processors
set nprocs = 32

# Set the start and end date separately below
set y = (2011 2011)
set m = (8 8)
set d = (10 20)

# Directory in which met_em files and met_oa files are located
set mdir = "/share/mzhang/jas983/wrf_data/eas5555/prep/wps"

################### END USER INPUT SECTION ######################

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

# -----------  create namelist ----------------------------

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

echo Starting real...
date

mpirun -np $nprocs ./real.exe

echo Done running real. Starting WRF...
date

mpirun -np $nprocs ./wrf.exe

echo Done running WRF. Cleaning up...
date

rm met_em.d*

echo Done cleaning up.
