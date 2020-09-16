#!/bin/csh

#SBATCH -J OptWRF			# Job name
#SBATCH -o /share/mzhang/jas983/wrf_data/met4ene/optwrf/examples/logs/log_optwrf_n200_g9.%j		# Name of stdout output file(%j expands to jobId)
#SBATCH -e /share/mzhang/jas983/wrf_data/met4ene/optwrf/examples/logs/err_optwrf_n200_g9.%j		# Name of stderr output file(%j expands to jobId)
#SBATCH --ntasks=1		    # Total number of tasks to be configured for.
#SBATCH --tasks-per-node=1	# sets number of tasks to run on each node.
#SBATCH --cpus-per-task=1	# sets number of cpus needed by each task (if task is "make -j3" number should be 3).
#SBATCH --get-user-env		# tells sbatch to retrieve the users login environment. 
#SBATCH -t 100:00:00		# Run time (hh:mm:ss)
#SBATCH --mem=10000M		# memory required per node
#SBATCH --partition=default_cpu	# Which queue it should run on.

python example_optimize_wrf_physics.py

exit
