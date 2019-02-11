#!/bin/csh
set verbose
date
unlimit

set hours = ('00', '06', '12', '18')
set yr = 2011
set mo = 01
foreach day (01 02 03 04 05)
foreach hr (1 2 3 4)
ln -s /bt1/nyc_2017/raw_data/ds461/SURFACE_OBS:${yr}${mo}${day}$hours[$hr] SURFACE_OBS:${yr}-${mo}-${day}_$hours[$hr]
end
end
ln -s /bt1/nyc_2017/raw_data/ds461/SURFACE_OBS:2011010100 SURFACE_OBS:2011-01-01_00

foreach g (1 2 3)

cp namelist.input_d0${g}_2011 namelist.oa
/hp6/models/WRFV3.8.1/OBSGRID/src/obsgrid.exe
mv wrfsfdda_d0${g} wrfsfdda_d0${g}_2011-01-01
date

end
