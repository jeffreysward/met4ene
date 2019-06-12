##########################################################
###  This is the executable file that should be called via
###  qsub or via a separate which calls this script via a 
###  qsub command.

###  geogrid.exe only needs to be rerun if the domain has changed

###  If you need to make changes to domain, intervals, options, make
###  the changes in nam1.template and nam2.template. 
##########################################################

### Set options for PBS
#PBS -N run_geogrid
#PBS -o output.geogrid
#PBS -A UCOR0037
#PBS -l walltime=00:30:00
#PBS -q regular
#PBS -j oe
#PBS -M jas983@cornell.edu 
#PBS -l select=2:ncpus=1:mpiprocs=1

### Change to whe WPS working directory 
cd /glade/scratch/$USER/wps

### Run geogrid
echo Stating geogrid
set verbose

./geogrid.exe

echo Done...
exit