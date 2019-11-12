import unittest
import datetime
import random
import os
import concurrent.futures
import time
import wrfga
from wrfparams import ids2str, write_param_csv
import runwrf as rw
import sqlite3
from wrfga import Chromosome


def insert_sim(individual, conn, c):
    print(f'...Adding {individual.Genes} to the simulation database...')
    with conn:
        c.execute("""INSERT INTO simulations VALUES (
                    :mp_physics, :ra_lw_physics, :ra_sw_physics, :sf_surface_physics, 
                    :bl_pbl_physics, :cu_physics, :sf_sfclay_physics, :fitness)""",
            {'mp_physics': individual.Genes[0], 'ra_lw_physics': individual.Genes[1],
             'ra_sw_physics': individual.Genes[2], 'sf_surface_physics': individual.Genes[3],
             'bl_pbl_physics': individual.Genes[4], 'cu_physics': individual.Genes[5],
             'sf_sfclay_physics': individual.Genes[6], 'fitness': individual.Fitness})


def get_individual_by_genes(geneset, c):
    c.execute("""SELECT * FROM simulations 
                WHERE mp_physics = :mp_physics
                AND ra_lw_physics = :ra_lw_physics
                AND ra_sw_physics = :ra_sw_physics
                AND sf_surface_physics = :sf_surface_physics
                AND bl_pbl_physics = :bl_pbl_physics
                AND cu_physics = :cu_physics
                AND sf_sfclay_physics = :sf_sfclay_physics""",
              {'mp_physics': geneset[0], 'ra_lw_physics': geneset[1],
               'ra_sw_physics': geneset[2], 'sf_surface_physics': geneset[3],
               'bl_pbl_physics': geneset[4], 'cu_physics': geneset[5],
               'sf_sfclay_physics': geneset[6]})
    sim_data = c.fetchone()
    if sim_data is not None:
        past_sim = Chromosome(list(sim_data[0:-1]), sim_data[-1])
    else:
        return None
    return past_sim


# class Fitness:
#     def __init__(self, total_error):
#         self.TotalError = total_error
#
#     def __gt__(self, other):
#         self.TotalError < other.TotalError


# Define a function that produces a random fitness value between 0 - 100
def get_fitness(param_ids):
    print('Calculating fitness for: {}'.format(param_ids))
    time.sleep(2)
    return random.randrange(0, 100)


def get_wrf_fitness(param_ids, start_date='Jan 15 2011', end_date='Jan 16 2011',
                    bc_data='ERA', MAX_DOMAINS=1, template_dir=None):
    # Format the forecast start/end and determine the total time.
    forecast_start = datetime.datetime.strptime(start_date, '%b %d %Y')
    forecast_end = datetime.datetime.strptime(end_date, '%b %d %Y')
    delt = forecast_end - forecast_start
    print('- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -')
    print('\nCalculating fitness for: {}'.format(param_ids))
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
        conn = sqlite3.connect(':memory:')
        c = conn.cursor()
        c.execute("""CREATE TABLE simulations (
                    mp_physics INTEGER, 
                    ra_lw_physics INTEGER,
                    ra_sw_physics INTEGER,
                    sf_surface_physics INTEGER,
                    bl_pbl_physics INTEGER,
                    cu_physics INTEGER,
                    sf_sfclay_physics INTEGER,
                    fitness FLOAT 
                    )""")

        start_time = datetime.datetime.now()
        pop_size = 10
        n_elites = int(0.34*pop_size) if int(0.34*pop_size) > 0 else 1
        print('The number of elites is {}'.format(n_elites))
        n_generations = 2
        optimal_fitness = 0

        def fn_display(individual):
            wrfga.display(individual, start_time)

        def fn_display_pop(pop):
            wrfga.display_pop(pop, fn_display)

        def fn_get_pop_fitness(pop):
            with concurrent.futures.ThreadPoolExecutor() as executor:
                # Start running all the fitness functions that need to be calculated
                fitness_threads = []
                for individual in pop:
                    if individual.Fitness is None:
                        # Check to see if this individual already exists in the simulation database
                        past_individual = get_individual_by_genes(individual.Genes, c)
                        # If not, execute a new thread to calculate the fitness
                        if past_individual is None:
                            fitness_threads.append(executor.submit(get_wrf_fitness, individual.Genes))
                        else:
                            individual.Fitness = past_individual.Fitness
                            fitness_threads.append(None)
                    else:
                        fitness_threads.append(None)
                # Get the results from the thread pool executor
                fitness_matrix = []
                for thread in fitness_threads:
                    try:
                        fitness_value = thread.result()
                    except AttributeError:
                        fitness_value = None
                    fitness_matrix.append(fitness_value)
                # Attach fitness values generated by the thread pool to their Chromosome
                ii = 0
                for individual in pop:
                    if individual.Fitness is None:
                        individual.Fitness = fitness_matrix[ii]
                        insert_sim(individual, conn, c)
                    ii += 1
            fn_display_pop(pop)

            # # The following block is legacy code to run in serial
            # for individual in pop:
            #     if individual.Fitness is None:
            #         individual.Fitness = get_fitness(individual.Genes)
            # fn_display_pop(pop)

        # Create an initial population
        population = wrfga.generate_population(pop_size)

        # Calculate the fitness of the initial population
        print('--> Calculating the fitness of the initial population...')
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

        WRFga_winner = wrfga.get_best(population)
        print(f'\nWRFga finished running in {datetime.datetime.now() - start_time}')
        print(f'{WRFga_winner.Genes} is the best parameter combination')

        conn.close()

        self.assertEqual(0, optimal_fitness)



