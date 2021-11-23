#!/bin/csh

#SBATCH -J wrf			# Job name
#SBATCH -o /share/mzhang/jas983/wrf_data/met4ene/wrfout/logs/output.wrf.%j		# Name of stdout output file(%j expands to jobId)
#SBATCH -e /share/mzhang/jas983/wrf_data/met4ene/wrfout/logs/errors.wrf.%j		# Name of stderr output file(%j expands to jobId)
#SBATCH --ntasks=8		# Total number of tasks to be configured for.
#SBATCH --tasks-per-node=8	# sets number of tasks to run on each node.
#SBATCH --cpus-per-task=1	# sets number of cpus needed by each task (if task is "make -j3" number should be 3).
#SBATCH --get-user-env		# tells sbatch to retrieve the users login environment. 
#SBATCH -t 72:00:00		# Run time (hh:mm:ss)
#SBATCH --mem=20000M		# memory required per node
#SBATCH --partition=default_cpu	# Which queue it should run on.

if ( $#argv == 1 ) then
    cd $argv
    set runwrfdir = $argv
else
    echo "Warning: runwrf.csh takes at most one input."
    echo "         running WRF in current directory."
    set runwrfdir = "./"
endif

limit stacksize unlimited

### -----------  run wrf ---------------------------
mpirun -np 8 ${argv}wrf.exe

exit
