import unittest
import wrfga
import datetime
import random
from wrfparams import ids2str, write_param_csv
import runwrf as rw


# class Fitness:
#     def __init__(self, total_error):
#         self.TotalError = total_error
#
#     def __gt__(self, other):
#         self.TotalError < other.TotalError


# Define a function that produces a random fitness value between 0 - 100
def get_fitness(param_ids):
    print('Calculating fitness for: {}'.format(param_ids))
    return random.randrange(0, 100)


def get_wrf_fitness(param_ids, start_date='Jan 15 2011', end_date='Jan 16 2011',
                    bc_data='ERA', MAX_DOMAINS=1, template_dir=None):
    # Format the forecast start/end and determine the total time.
    forecast_start = datetime.datetime.strptime(start_date, '%b %d %Y')
    forecast_end = datetime.datetime.strptime(end_date, '%b %d %Y')
    delt = forecast_end - forecast_start
    print('Forecast starting on: {}'.format(forecast_start))
    print('Forecast ending on: {}'.format(forecast_end))
    paramstr = ids2str(param_ids)

    # Next, get boundary condition data for the simulation
    # ERA is the only supported data type right now.
    vtable_sfx = rw.get_bc_data(paramstr, bc_data, template_dir, forecast_start, delt)

    # Setup the working directory to run the simulation
    rw.wrfdir_setup(paramstr, forecast_start, bc_data, template_dir, vtable_sfx)

    # Prepare the namelist
    rw.prepare_namelists(paramstr, param_ids, forecast_start, forecast_end, delt,
                         bc_data, template_dir, MAX_DOMAINS)

    # RUN WPS
    success = rw.run_wps(paramstr, forecast_start, bc_data, template_dir)
    print('WPS ran successfully? {}'.format(success))

    # RUN REAL
    if success:
        success = rw.run_real(paramstr, forecast_start, bc_data, template_dir)
        print('Real ran successfully? {}'.format(success))

    # RUN WRF
    if success:
        success = rw.run_wrf(paramstr, forecast_start, bc_data, template_dir, MAX_DOMAINS)
        print('WRF ran successfully? {}'.format(success))

    # Compute the error between WRF run and ERA5 dataset and return fitness
    if success:
        fitness = rw.wrf_era5_diff(paramstr, forecast_start, bc_data, template_dir)
    else:
        fitness = 10**10

    # Write parameter combinations to CSV
    # (if you would like to restart this, you must manually delete this CSV)
    write_param_csv(param_ids, fitness)
    return fitness


class WRFGATests(unittest.TestCase):
    def test(self):
        start_time = datetime.datetime.now()
        pop_size = 6
        n_elites = int(0.34*pop_size) if int(0.34*pop_size) > 0 else 1
        print('The number of elites is {}'.format(n_elites))
        n_generations = 3
        optimal_fitness = 0

        def fn_display(individual):
            wrfga.display(individual, start_time)

        def fn_display_pop(pop):
            wrfga.display_pop(pop, fn_display)

        def fn_get_pop_fitness(pop):
            for ii in range(0, len(pop)):
                if pop[ii].Fitness is None:
                    pop[ii].Fitness = get_wrf_fitness(pop[ii].Genes)
            fn_display_pop(pop)

        # Create an initial population
        population = wrfga.generate_population(pop_size)

        # Calculate the fitness of the initial population
        print('Calculating the fitness of the initial population...')
        fn_get_pop_fitness(population)

        # Until the specified generation number is reached,
        gen = 1
        while gen <= n_generations:
            print('\n------ Starting generation {} ------'.format(gen))
            # Select the mating population
            mating_pop = wrfga.selection(population, pop_size)
            print('The mating population is:')
            fn_display_pop(mating_pop)
            # Carry out crossover
            offspring_pop = []
            while len(offspring_pop) < pop_size - n_elites:
                offspring = wrfga.crossover(mating_pop)
                if offspring is not None:
                    offspring_pop.extend(offspring)
            print('The offspring population is:')
            fn_display_pop(offspring_pop)
            # Give a chance for mutation on each member of the offspring population
            offspring_pop = wrfga.mutate(offspring_pop)
            print('The offspring population after mutation is:')
            fn_display_pop(offspring_pop)
            # Copy the elites into the offspring population
            elites = wrfga.find_elites(population, n_elites, fn_display_pop)
            if elites is not None:
                offspring_pop.extend(elites)
                print('The offspring population after adding the elites is:')
                fn_display_pop(offspring_pop)
            # Calculate the fitness of the population
            print('Calculating the fitness of the generation {} population...'.format(gen))
            fn_get_pop_fitness(offspring_pop)
            # Initialize the next generation
            population = offspring_pop
            gen += 1

        self.assertEqual(0, optimal_fitness)



