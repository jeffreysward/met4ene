"""
Optimization of WRF Model Physics
=================================

If you haven't inhereted a set of WRF model namelists, it's not readily apparent which model setup
among the ~1.5 million choices may work the best for your application. This example
runs a simple genetic algorithm to select a set of WRF physics options that preforms the best for
your application using ERA5 data to benchmark the 12-km WRF simulations.
"""
import optwrf.optimize_wrf_physics as owp

# Specify the population size and number of generations
# to run the simple genetic algorithm for optimizing WRF physics.
owp.run_simplega(pop_size=61, n_generations=0, initial_pop_file='8mp4lw4sw2lsm2pbl6cu_2011_sims_repeat.csv')
