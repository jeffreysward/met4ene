#!/bin/csh

# This script runs OBSGRID for the desired period. 
# Submit this script via condor or run it directly on the NAS.

# Load gcc version 4.9.2
module load scl-3

set verbose
date
unlimit

# Set the directories in which the met_em files and surface observations are located
set metdir = "/share/mzhang/jas983/wrf_data/eas5555/prep/wps"
set surfdat = "/share/mzhang/jas983/wrf_data/raw_data/ds461"
set obsins = "/home/jas983/models/wrf/OBSGRID"

# Link the OBSGRID exe
ln -s $obsins/src/obsgrid.exe
# Set the days that you intend to run and link observational data
set hours = ('00' '06' '12' '18')
set yr = (2011 2011)
set mo = (05 06)
set d  = (30 01)
set mo_len = (31 28 31 30 31 30 31 31 30 31 30 31)

if ($d[2] < $mo_len[$mo[2]]) then
	@   ed = $d[2] + 1
	if ($ed < 10) then
		set ed = "0$ed"
	endif
	set em = $mo[2]
else
	set ed = 01
	@   mo[2] = $mo[2] + 1
	if ($mo[2] < 10) then
		set em = "0$mo[2]"
	else
		set em = $mo[2]
	endif
endif
echo The end month is: $em
echo The end day is: $ed

set day = $d[1]
set month = $mo[1]
while ($month <= $mo[2])
	# If the month is not equal to the end month, run from $day to the end of the month
	if ($month < $mo[2]) then
	while ($day <= $mo_len[$month])
		echo The day is $day
		#Link in the metfiles from the WPS directory
		echo Linking : met_em.${yr[1]}-${month}-$day...
		ln -s $metdir/met_em.*${yr[1]}-${month}-$day* .
		foreach hr (1 2 3 4)
			echo Linking : SURFACE_OBS:${yr[1]}${month}${day}$hours[$hr]...
			ln -s $surfdat/SURFACE_OBS:${yr[1]}${month}${day}$hours[$hr] SURFACE_OBS:${yr[1]}-${month}-${day}_$hours[$hr]
		end
		@ day = $day + 1
		if ($day < 10) then
			set day = "0$day"
		endif
	end
	# Set the day back to 01 and add one to the month
	set day = 01
	@ month = $month + 1
	# Make sure the month is formatted correctly
	if ($month < 10) then
		set month = "0$month"
	endif

	else
	# If the month is equal to the end month, run from $day to the end day
	while ($day <= $d[2])
		echo The day is $day
		#Link in the metfiles from the WPS directory
		echo Linking : met_em.${yr[1]}-${month}-$day...
		ln -s $metdir/met_em.*${yr[1]}-${month}-$day* .
		foreach hr (1 2 3 4)
			echo Linking : SURFACE_OBS:${yr[1]}${month}${day}$hours[$hr]...
			ln -s $surfdat/SURFACE_OBS:${yr[1]}${month}${day}$hours[$hr] SURFACE_OBS:${yr[1]}-${month}-${day}_$hours[$hr]
		end
		@ day = $day + 1
		if ($day < 10) then
			set day = "0$day"
		endif
	end
	# Add one to the month so that the loop will end
	@ month = $month + 1
	endif
	echo The month is $month, and the end month is $mo[2]
end

#This is the hour after the last day
echo Linking met_em files from final hour: met_em.${yr[2]}-${em}-${ed}...
ln -s $metdir/met_em.*${yr[2]}-${em}-${ed}* .
echo Linking surface data from final hour: SURFACE_OBS:${yr[2]}${em}${ed}00
ln -s $surfdat/SURFACE_OBS:${yr[2]}${em}${ed}00 SURFACE_OBS:${yr[2]}-${em}-${ed}_00

#Run OBSGRID for each domain (I could combine these, but it may not be worth it if the time difference is small)
foreach g (1 2 3)
	# Create namelist for the OBSGRID run.
	cat nam1.input > namelist.oa

cat << -eof- >> namelist.oa
 start_year                    = $yr[1]
 start_month                   = $mo[1]
 start_day                     = $d[1]
 start_hour                    = 00
 end_year                      = $yr[2]
 end_month                     = $em
 end_day                       = $ed
 end_hour                      = 00
-eof-
	
	cat nam2.input_d0${g} >> namelist.oa

	# Run the obsgrid execuable.
	./obsgrid.exe

	# This name change is to mark this for the start day. 
	mv wrfsfdda_d0${g} wrfsfdda_d0${g}_${yr[1]}-${mo[1]}-${d[1]}
	date

end
