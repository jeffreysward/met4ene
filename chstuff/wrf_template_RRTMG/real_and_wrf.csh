#!/bin/csh

#PBS -N run_wrf
#PBS -A UCOR0037
#PBS -l walltime=8:30:00
#PBS -q regular
#PBS -j oe
#PBS -m abe
#PBS -M jas983@cornell.edu 
#PBS -l select=8:ncpus=32:mpiprocs=32
set verbose
limit stacksize unlimited

date

###  This will create namelist.input, link in met_em files, and
###  run real and then wrf

################### BEGIN USER INPUT SECTION ####################

### Set the start and end date separately below
set y = (2011 2011)
set m = (7 7)
set d = (9 15)

### Directory in which met_em files are located
set mdir = "/glade/scratch/$USER/wps"

### Set current and former directory strings
set lastdst = 05
set lastdir = "2011jul05-09"
set thisdir = "2011jul10-15"

################### END USER INPUT SECTION ######################

set digits  = (01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31)
set hdig = (00 03 06 09 12 15 18 21)
set ndays = ( 31 28 31 30 31 30 31 31 30 31 30 31 )

### --------------  link met_em files ------------------------------

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

### -----------  create namelist for spinup ----------------------------

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

cat nam1-0.template > namelist.input

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

cat nam2-0.template >> namelist.input

echo Starting real for spin up
date

mpiexec_mpt ./real.exe

echo Starting wrf for spin up
date

mpiexec_mpt ./wrf.exe

mv namelist.input namelist.input-0
mv wrfinput_d03 wrfinput_d03-0
mv wrfinput_d02 wrfinput_d02-0
mv wrfbdy_d01 wrfbdy_d01-0
mv wrfinput_d01 wrfinput_d01-0

echo Done running spin up

### -----------     create namelist for model run  ----------------------------

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

echo Starting real
date

mpiexec_mpt ./real.exe

echo Starting WRF
date

mpiexec_mpt ./wrf.exe

echo Done running WRF. Cleaning up...
date

rm met_em.d*

echo Done cleaning up.
exit
