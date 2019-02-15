#!/bin/csh
set verbose
limit stacksize unlimited

hostname
date

# for hp350 running gfortran version
# setenv LD_LIBRARY_PATH /usr/local/lib

#  this will create namelist.input, link in met_em files, and
#  run real and then wrf

# setenv OMP_NUM_THREADS 12

set y = (2010 2011)
set m = (12 1)
set d = (31 6)

# directory in which met_em files are located
set mdir = "/share/mzhang/jas983/wrf_data/eas5555/solar_wfp/wps"

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

#goto 5dayonly

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

# link OBS_DOMAIN301 for fdda
set mm = $m[1]
set dd = $d[1]
#ln -s /bt1/nyc_2017/raw_data/ds472/output/$y[1]$digits[$mm]$digits[$dd].obs OBS_DOMAIN201
#ln -s /bt1/nyc_2017/raw_data/ds472/output/$y[1]$digits[$mm]$digits[$dd].obs OBS_DOMAIN301
ln -s ../../nyserda_12-4-133/obsgrid_2010dec27-31/wrfsfdda_d01_$y[1]-12-27 wrfsfdda_d01
ln -s ../../nyserda_12-4-133/obsgrid_2010dec27-31/wrfsfdda_d02_$y[1]-12-27 wrfsfdda_d02
ln -s ../../nyserda_12-4-133/obsgrid_2010dec27-31/wrfsfdda_d03_$y[1]-12-27 wrfsfdda_d03


echo Starting real for spin up
date

real.exe
#/hp6/models/WRFV3.8.1/WRFV3_smpar/main/real.exe
#/hp1/models/WRFV3.8.1/WRFV3/main/real.exe


echo Starting wrf for spin up
date

wrf.exe
#/hp6/models/WRFV3.8.1/WRFV3_smpar/main/wrf.exe
#/hp1/models/WRFV3.8.1/WRFV3/main/wrf.exe

mv namelist.input namelist.input-0
mv wrfinput_d03 wrfinput_d03-0
mv wrffdda_d02 wrffdda_d02-0
mv wrfinput_d02 wrfinput_d02-0
mv wrfbdy_d01 wrfbdy_d01-0
mv wrffdda_d01 wrffdda_d01-0
mv wrfinput_d01 wrfinput_d01-0
rm wrfsfdda_d01
rm wrfsfdda_d02
rm wrfsfdda_d03
#rm OBS_DOMAIN101
rm OBS_DOMAIN201
rm OBS_DOMAIN301

echo Done  with spin up


#5dayonly:
rm OBS_DOMAIN201
rm OBS_DOMAIN301

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
ln -s /bt1/nyc_2017/wrf/domains/nyserda_12-4-133/obsgrid_jan01-05/wrfsfdda_d01_${begyr}-$digits[$begmo]-$digits[$begdy] wrfsfdda_d01
ln -s /bt1/nyc_2017/wrf/domains/nyserda_12-4-133/obsgrid_jan01-05/wrfsfdda_d02_${begyr}-$digits[$begmo]-$digits[$begdy] wrfsfdda_d02
ln -s /bt1/nyc_2017/wrf/domains/nyserda_12-4-133/obsgrid_jan01-05/wrfsfdda_d03_${begyr}-$digits[$begmo]-$digits[$begdy] wrfsfdda_d03


echo Starting real
date

real.exe
#/hp6/models/WRFV3.8.1/WRFV3_smpar/main/real.exe
#/hp1/models/WRFV3.8.1/WRFV3/main/real.exe


echo Starting wrf
date

wrf.exe
#/hp6/models/WRFV3.8.1/WRFV3_smpar/main/wrf.exe
#/hp1/models/WRFV3.8.1/WRFV3/main/wrf.exe

echo Done  clean up
date

rm met_em.d*

rm OBS_DOMAIN201
rm OBS_DOMAIN201-1
rm OBS_DOMAIN301
rm OBS_DOMAIN301-1
rm wrfsfdda_d01
rm wrfsfdda_d02
rm wrfsfdda_d03
