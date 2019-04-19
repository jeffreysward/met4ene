#! /bin/csh 
#-- 
#--CMC Mar 4, 2019 
#--

#-set compset = FSDSMAM 
#-set compset = FW5
set compset = FC5AQUAP

set pversion = /glade/u/home/sward/2017/eas5555/chstuff/cesm/cases/

set case = 001z
#set new_case = f.e12.${compset}.f19_19.waccm.$case
set new_case = f.e12.${compset}.f19_19.aquap.$case
set new_case_p = ~/cases/$new_case

#-- scripts 
set build = ${new_case}".build" 
set run = ${new_case}".run" 
set submit = ${new_case}".submit" 
#--
echo "NEW CASE = " $new_case_p 
#-- clean case folder 
if  ( -d $new_case_p )  then
   echo "GOT folder" 
   rm -rf $new_case_p 
   echo "RM folder" 
else 
   echo "NO folder, new case"
endif 
#-- STEPS from creating to submition of simulation case

# 1. create case 
$pversion/create_newcase -case $new_case_p -mach cheyenne  -res f19_f19 -compset ${compset} 

#--
cd $new_case_p  
#--

# 2. configure parameters for compilation 
./cesm_setup 

# 3. compile model and build executable 
./$build 

# 4. define project account 
sed -i "s/###PBS.*/#PBS -A UCOR0023/" $run 

# 5. define requesting time 
sed -i "s/#PBS -l walltime.*/#PBS -l walltime=00:30:00/" $run 

# 6. define lengh of run 
./xmlchange STOP_OPTION=ndays 
./xmlchange STOP_N=10 

# 7. submit job to cluster  
./$submit 

exit 

