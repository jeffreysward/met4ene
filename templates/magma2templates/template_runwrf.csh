#!/bin/csh

#SBATCH -J wrf			# Job name
#SBATCH -o wrf.o%j		# Name of stdout output file(%j expands to jobId)
#SBATCH -e wrf.e%j		# Name of stderr output file(%j expands to jobId)
#SBATCH --nodes=1		# Total number of nodes requested 
#SBATCH --ntasks=8		# Total number of tasks to be configured for. 
#SBATCH --tasks-per-node=8	# sets number of tasks to run on each node. 
#SBATCH --cpus-per-task=1	# sets number of cpus needed by each task (if task is "make -j3" number should be 3).
#SBATCH --get-user-env		# tells sbatch to retrieve the users login environment. 
#SBATCH -t 12:00:00		# Run time (hh:mm:ss) 
#SBATCH --mem-per-cpu=1000	# memory required per allocated CPU
#SBATCH --mem=1000M		# memory required per node
#SBATCH --partition=default_cpu	# Which queue it should run on.

limit stacksize unlimited

### -----------  run wrf ---------------------------
mpirun ./wrf.exe

rm -f met_em*

exit
