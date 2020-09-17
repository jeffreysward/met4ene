"""
A framework to run the simple genetic algorithm for optimizing the WRF model physics.
All simulation parameters and fitness values are saved in an SQL database.


Known Issues/Wishlist:

"""

import concurrent.futures
import csv
import datetime
import os
import random
import sqlite3
import sys
import time

import optwrf.helper_functions as hf
from optwrf.runwrf import WRFModel
import optwrf.simplega as simplega
from optwrf.simplega import Chromosome
import optwrf.wrfparams as wrfparams


# class Fitness:
#     def __init__(self, total_error):
#         self.TotalError = total_error
#
#     def __gt__(self, other):
#         self.TotalError < other.TotalError


def conn_to_db(db_name='optwrf.db'):
    """
        Opens the connection to a SQL database.

        :param db_name: SQL database name (string).
            Can be ':memory:' if you only want the database to be held in memory.
            Otherwise, it will take the form <database_name>.db.
        :returns db_conn: database connection object
            that allows for additional interactions with the SQL database when referenced.

    """
    db_conn = sqlite3.connect(db_name)
    c = db_conn.cursor()
    with db_conn:
        c.execute("""CREATE TABLE IF NOT EXISTS simulations (
                        start_date DATE,
                        mp_physics INTEGER, 
                        ra_lw_physics INTEGER,
                        ra_sw_physics INTEGER,
                        sf_surface_physics INTEGER,
                        bl_pbl_physics INTEGER,
                        cu_physics INTEGER,
                        sf_sfclay_physics INTEGER,
                        fitness FLOAT,
                        ghi_error FLOAT,
                        wpd_error FLOAT,
                        runtime FLOAT 
                        )""")
    return db_conn


def insert_sim(individual, db_conn, verbose=False):
    """
    Inserts a simulation into the SQL database held in memory or written to a .db file.

    :param individual: simplega.Chromosome instance
        describing the simulation that you would like to add to the SQL simulation database.
    :param db_conn: database connection object
        created using the conn_to_db() function.
    :param verbose: boolean (default = False)
        instructing the program to print everything or just key information to the screen.

    """
    if verbose:
        print(f'...Adding {individual.Genes} to the simulation database...')
    c = db_conn.cursor()
    with db_conn:
        c.execute("""INSERT INTO simulations VALUES (
                    :start_date, :mp_physics, :ra_lw_physics, :ra_sw_physics, :sf_surface_physics, 
                    :bl_pbl_physics, :cu_physics, :sf_sfclay_physics, :fitness, :ghi_error, :wpd_error, :runtime)""",
                  {'start_date': individual.Start_date, 'mp_physics': individual.Genes[0],
                   'ra_lw_physics': individual.Genes[1],
                   'ra_sw_physics': individual.Genes[2], 'sf_surface_physics': individual.Genes[3],
                   'bl_pbl_physics': individual.Genes[4], 'cu_physics': individual.Genes[5],
                   'sf_sfclay_physics': individual.Genes[6],
                   'fitness': individual.Fitness, 'ghi_error': individual.GHI_error,
                   'wpd_error': individual.WPD_error, 'runtime': individual.Runtime})


def update_sim(individual, db_conn):
    """
    Inserts a simulation into the SQL database held in memory or written to a .db file.

    :param individual: simplega.Chromosome instance
        describing the simulation that you would like to update in the SQL simulation database.
    :param db_conn: database connection object
        created using the conn_to_db() function.

    """
    print(f'...Updating {individual.Genes} in the simulation database...')
    c = db_conn.cursor()
    with db_conn:
        c.execute("""UPDATE simulations 
                    SET start_date = :start_date, 
                    fitness = :fitness,
                    ghi_error = :ghi_error,
                    wpd_error = :wpd_error, 
                    runtime = :runtime
                    WHERE mp_physics = :mp_physics
                    AND ra_lw_physics = :ra_lw_physics
                    AND ra_sw_physics = :ra_sw_physics
                    AND sf_surface_physics = :sf_surface_physics
                    AND bl_pbl_physics = :bl_pbl_physics
                    AND cu_physics = :cu_physics
                    AND sf_sfclay_physics = :sf_sfclay_physics""",
                  {'start_date': individual.Start_date, 'fitness': individual.Fitness,
                   'ghi_error': individual.GHI_error, 'wpd_error': individual.WPD_error,
                   'runtime': individual.Runtime, 'mp_physics': individual.Genes[0],
                   'ra_lw_physics': individual.Genes[1], 'ra_sw_physics': individual.Genes[2],
                   'sf_surface_physics': individual.Genes[3], 'bl_pbl_physics': individual.Genes[4],
                   'cu_physics': individual.Genes[5], 'sf_sfclay_physics': individual.Genes[6]})


def get_individual_by_genes(individual, db_conn):
    """
    Looks for an indivual set of genes in an SQLite database.

    ***NOTE: I'm not sure if I want to remove the first where clause contianing the start date.

    :param individual: simplega.Chromosome instance
        describing the simulation that you would to extract from the SQL simulation database
        if it exists there.
    :param db_conn: database connection object
        created using the conn_to_db() function.
    :return past_sim: simplega.Chromosome instance
        describing the simulation that was run previously and stored in the SQL simulation database,
        and corresponding to the input individual function parameter.

    """
    c = db_conn.cursor()
    c.execute("""SELECT * FROM simulations 
                WHERE start_date = :start_date
                AND mp_physics = :mp_physics
                AND ra_lw_physics = :ra_lw_physics
                AND ra_sw_physics = :ra_sw_physics
                AND sf_surface_physics = :sf_surface_physics
                AND bl_pbl_physics = :bl_pbl_physics
                AND cu_physics = :cu_physics
                AND sf_sfclay_physics = :sf_sfclay_physics""",
              {'start_date': individual.Start_date, 'mp_physics': individual.Genes[0],
               'ra_lw_physics': individual.Genes[1],
               'ra_sw_physics': individual.Genes[2], 'sf_surface_physics': individual.Genes[3],
               'bl_pbl_physics': individual.Genes[4], 'cu_physics': individual.Genes[5],
               'sf_sfclay_physics': individual.Genes[6]})
    sim_data = c.fetchone()
    if sim_data is not None:
        param_ids = list(sim_data[1:-2])
        s_date = sim_data[0]
        s_date, e_date = simplega.generate_random_dates(input_start_date=s_date)
        fitness = sim_data[-2]
        runtime = sim_data[-1]
        past_sim = Chromosome(param_ids, s_date, e_date, fitness, runtime)
    else:
        return None
    return past_sim


def print_database(db_conn):
    """
    Prints the entire SQLite simulation database.

    :param db_conn: database connection object
        created using the conn_to_db() function.

    """
    c = db_conn.cursor()
    c.execute("""SELECT * FROM simulations""")
    print('----------------------------SIMULATIONS----------------------------')
    # Extract the table headers.
    headers = [i[0] for i in c.description]
    print(headers)
    for entry in c.fetchall():
        print(entry)


def sql_to_csv(csv_file_path, db_conn):
    """
    Writes the contents of a SQL database to a CSV file. The SQL database must
    be in the directory that you are running this function from.

    :param csv_file_path: string
        Exact path to where you would like to csv to be saved ending with the file name.
        e.g., csv_file_path = '/home/jas983/data/test.csv'
    :param db_conn: database connection object
        created using the conn_to_db() function.

    """
    c = db_conn.cursor()
    c.execute("""SELECT * FROM simulations""")
    header = [i[0] for i in c.description]
    csv_writer = csv.writer(open(csv_file_path, "w"))
    csv_data = c.fetchall()
    csv_writer.writerow(header)
    csv_writer.writerows(csv_data)


def close_conn_to_db(db_conn):
    """
    Closes the connection to a SQL database.

    :param db_conn: database connection object
        created using the conn_to_db() function.

    """
    db_conn.close()


def seed_initial_population(input_csv):
    """
    Reads the input csv file, which contains the dates and/or parameter combinations
    that you would like to see in the initial population. The CSV file should be
    formatted as follows (i.e., this function looks for these column names):

    Line 1: start_date, mp_physics, ra_lw_physics, ra_sw_physics, sf_surface_physics,
            bl_pbl_physics, cu_physics

    Line 2: Feb 28 2011,  1, 24, 99,  4, 11,  2

    Line 3: Aug 31 2011, 28,  4,  5,  2, 10, 93

    Line 4: Dec 10 2011,  7, 24,  3,  4,  9,  4

    Line 5: Jul 22 2011, 11, 24,  2,  1,  4, 10

    Line 6: May 23 2011,  1,  4,  5,  2, 10, 93

    Line 7: Mar 31 2011, 28, 24, 99,  4, 11,  2

    .

    .

    .

    :param input_csv: string
        defines the file name from which dates/parameters will be read.
    :return intial population: list of Chromosome instances
        made from the information specified in the input file.

    """
    initial_population = []
    try:
        with open(input_csv, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                start_date = row['start_date']
                param_ids = wrfparams.flexible_generate(generate_params=False,
                                                        mp=int(row['mp_physics']), lw=int(row['ra_lw_physics']),
                                                        sw=int(row['ra_sw_physics']), lsm=int(row['sf_surface_physics']),
                                                        pbl=int(row['bl_pbl_physics']), cu=int(row['cu_physics']))
                start_date, end_date = simplega.generate_random_dates(input_start_date=start_date)
                initial_population.append(Chromosome(param_ids, start_date, end_date))
    except IOError:
        print(f'IOEror in seed_initial_population: {input_csv} does not exist.')
        return initial_population

    return initial_population


def get_fitness(param_ids, verbose=False):
    """
    This function produces a random fitness value between 0 - 100

    :param param_ids: list of ints
        corresponding to each WRF physics parameterization.
    :param verbose: boolean (default = False)
        instructing the program to print everything or just key information to the screen.
    :return fitness: int
        randomly generated, and between 1 and 100.

    """
    start_time = datetime.datetime.now()
    if verbose:
        print('Calculating fitness for: {}'.format(param_ids))
    time.sleep(120)
    fitness = random.randrange(0, 100)
    error1 = random.randrange(0, 100)
    error2 = random.randrange(0, 100)
    runtime = hf.strfdelta(datetime.datetime.now() - start_time)
    return fitness, error1, error2, runtime


def get_wrf_fitness(param_ids, start_date='Jan 15 2011', end_date='Jan 16 2011',
                    bc_data='ERA', n_domains=1, correction_factor=0.0004218304553577255,
                    setup_yaml='dirpath.yml', disable_timeout=False, verbose=False):
    """
    Using the input physics parameters, date, boundary condition, and domain data,
    this function runs the WRF model and computes the error between WRF and ERA5.

    :param param_ids: list of integers
        corresponding to each WRF physics parameterization.
    :param start_date: string
        specifying a desired start date.
    :param end_date: string
        specifying a desired end date.
    :param bc_data: string
        specifying the boundary condition data to be used for the WRF forecast.
        Currently, only ERA data (ds627.0) is supported.
    :param n_domains: integer
        specifing the number of WRF model domains. 1 - 3 domains are currently supported.
    :param correction_factor: float
        capuring the relationship between GHI and wind power density (WPD) errors averaged
        across an entrie year. Calculated using opwrf/examples/Fitness_correction_factor.py.
    :param setup_yaml: string
        defining the path to the yaml file where input directory paths are specified.
    :param disable_timeout: boolean (default = False)
        telling runwrf if subprogram timeouts are allowed or not.
    :param verbose: boolean (default = False)
        instructing the program to print everything or just key information to the screen.
    :return fitness: float
        value denoting how well the WRF model run performed.
        Fitness is a measure of accumlated error, so a lower value is better.

    """
    if verbose:
        print('- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -')
        print('\nCalculating fitness for: {}'.format(param_ids))

    # Create a WRFModel instance
    wrf_sim = WRFModel(param_ids, start_date, end_date,
                       bc_data=bc_data, n_domains=n_domains, setup_yaml=setup_yaml, verbose=verbose)

    # Check to see if WRFModel instance exists; if not, run the WRF model.
    wrfout_file_path = wrf_sim.DIR_WRFOUT + 'wrfout_d01.nc'
    orig_wrfout_file_path = wrf_sim.DIR_WRFOUT + 'wrfout_d01_' \
                       + wrf_sim.forecast_start.strftime('%Y') + '-' \
                       + wrf_sim.forecast_start.strftime('%m') + '-' \
                       + wrf_sim.forecast_start.strftime('%d') + '_00:00:00'
    if [os.path.exists(file) for file in [wrfout_file_path, orig_wrfout_file_path]].count(True) is 0:
        # Next, get boundary condition data for the simulation
        # ERA is the only supported data type right now.
        vtable_sfx = wrf_sim.get_bc_data()

        # Setup the working directory to run the simulation
        wrf_sim.wrfdir_setup(vtable_sfx)

        # Prepare the namelists
        wrf_sim.prepare_namelists()

        # Run WPS
        success = wrf_sim.run_wps(disable_timeout)
        if verbose:
            print(f'WPS ran successfully? {success}')

        # Run REAL
        if success:
            success = wrf_sim.run_real(disable_timeout)
            if verbose:
                print(f'Real ran successfully? {success}')

        # RUN WRF
        if success:
            success, runtime = wrf_sim.run_wrf(disable_timeout)
            if verbose:
                print(f'WRF ran successfully? {success}')
        else:
            runtime = '00h 00m 00s'
    else:
        success = True
        runtime = '00h 00m 00s'

    # Postprocess wrfout file and ERA5 data
    if success:
        proc_wrfout_file_path = wrf_sim.DIR_WRFOUT + 'wrfout_processed_d01.nc'
        if not os.path.exists(proc_wrfout_file_path):
            wrf_sim.process_wrfout_data()
        wrf_sim.process_era5_data()

    # Compute the error between WRF run and ERA5 dataset and return fitness
    if success:
        mae = wrf_sim.wrf_era5_diff()
        ghi_total_error = mae[1]
        wpd_total_error = mae[2]
        daylight_factor = hf.daylight_frac(start_date)  # daylight fraction
        fitness = daylight_factor * ghi_total_error + correction_factor * wpd_total_error
        if verbose:
            print(f'!!! Physics options set {param_ids} has fitness {fitness}')

    else:
        ghi_total_error = 6.022 * 10 ** 23
        wpd_total_error = 6.022 * 10 ** 23
        fitness = 6.022 * 10 ** 23

    return fitness, ghi_total_error, wpd_total_error, runtime


def run_simplega(pop_size, n_generations, elite_pct=0.08, testing=False,
                 initial_pop_file=None, restart_file=True, verbose=False):
    """
    Runs the simple genetic algorithm specified in simplega either
    to optimize the WRF model physics or with a test fitness function
    that randomly selects a fitness value for each individual Chromosome.

    :param pop_size: int
        describing population size for the genetic algorithm. Must be >= 1
    :param n_generations: int
        corresponding to the total number of generations after which the genetic algorithm will time out.
    :param elite_pct: float (default = 0.08)
        value between 0 - 1 defining the percentage of the parent population that is automatically
        moved to the offspring population unchanged.
    :param testing: boolean (default = False)
        flag that uses a random number generator as the fitness function when True.
    :param initial_pop_file: string (default = None)
        of a csv file path containing the populaition you would like to begin the simulation with.
    :param restart_file: boolean (default = True)
        determining whether restart CSV files will be written before the fitness is calculated
        for each generation.
    :param verbose: boolean (default = False)
        instructing the program to print everything or just key information to the screen.
    :return WRFga_winner: simplega.Chromosome instance
        corresponding to the simulation preforming the best in the genetic algorithm.

    """
    def fn_display(individual):
        """
        Wrapper function for individual Chromosome display function.
        """
        simplega.display(individual, start_time)

    def fn_display_pop(pop):
        """
        Wrapper function for whole population display function.
        """
        simplega.display_pop(pop, fn_display)

    def fn_get_pop_fitness(pop):
        """
        Calculates the fitness for each member of the population using multithreadding,
        and adds its information to the SQLite database.

        :param pop: list of simplega.Chromosome
            A population made up of individual Chromosome instances.
            The fitness is added as an attribute to the individual instances.

        """
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Start running all the fitness functions that need to be calculated
            fitness_threads = []
            for individual in pop:
                if individual.Fitness is None:
                    # Check to see if this individual already exists in the simulation database
                    past_individual = get_individual_by_genes(individual, db_conn)
                    # If not, execute a new thread to calculate the fitness
                    if past_individual is None:
                        if not testing:
                            fitness_threads.append(executor.submit(get_wrf_fitness, individual.Genes,
                                                                   individual.Start_date, individual.End_date))
                        else:
                            fitness_threads.append(executor.submit(get_fitness, individual.Genes))
                    else:
                        individual.Fitness = past_individual.Fitness
                        fitness_threads.append(None)
                else:
                    fitness_threads.append(None)
            # Get the results from the thread pool executor
            fitness_matrix = []
            ghi_error_matrix = []
            wpd_error_matrix = []
            runtime_matrix = []
            for thread in fitness_threads:
                try:
                    fitness_value, ghi_error_value, wpd_error_value, runtime_value = thread.result()
                except AttributeError:
                    fitness_value = None
                    runtime_value = None
                    ghi_error_value = None
                    wpd_error_value = None
                fitness_matrix.append(fitness_value)
                ghi_error_matrix.append(ghi_error_value)
                wpd_error_matrix.append(wpd_error_value)
                runtime_matrix.append(runtime_value)
            # Attach fitness and runtime values generated by the thread pool to their Chromosome
            ii = 0
            for individual in pop:
                if individual.Fitness is None:
                    individual.Fitness = fitness_matrix[ii]
                    individual.GHI_error = ghi_error_matrix[ii]
                    individual.WPD_error = wpd_error_matrix[ii]
                    individual.Runtime = runtime_matrix[ii]
                    insert_sim(individual, db_conn)
                ii += 1
        fn_display_pop(pop)

    # ------> BEGINNING OF SIMPLEGA <------ #
    # Connect to the simulation database
    db_conn = conn_to_db()

    # Record the start time, and calculate the number of elites
    start_time = datetime.datetime.now()
    n_elites = int(elite_pct * pop_size) if int(elite_pct * pop_size) > 0 else 1
    if verbose:
        print(f'The elite percentage is {elite_pct*100}%; the number of elites is {n_elites}')

    # Create an initial population
    if initial_pop_file is not None:
        initial_pop = seed_initial_population(initial_pop_file)
    else:
        initial_pop = None
    population = simplega.generate_population(pop_size, initial_pop)

    # Calculate the fitness of the initial population
    print('--> Calculating the fitness of the initial population...')
    fn_get_pop_fitness(population)
    sys.stdout.flush()

    # Until the specified generation number is reached,
    gen = 1
    while gen <= n_generations:
        print('\n------ Starting generation {} ------'.format(gen))
        # Select the mating population
        mating_pop = simplega.selection(population, pop_size)
        if verbose:
            print('The mating population is:')
            fn_display_pop(mating_pop)
        # Carry out crossover
        offspring_pop = []
        while len(offspring_pop) < pop_size - n_elites:
            offspring = simplega.crossover(mating_pop)
            if offspring is not None:
                offspring_pop.extend(offspring)
        if verbose:
            print('The offspring population is:')
            fn_display_pop(offspring_pop)
        # Give a chance for mutation on each member of the offspring population
        offspring_pop = simplega.mutate(offspring_pop)
        if verbose:
            print('The offspring population after mutation is:')
            fn_display_pop(offspring_pop)
        # Copy the elites into the offspring population
        elites = simplega.find_elites(population, n_elites, fn_display_pop)
        if elites is not None:
            offspring_pop.extend(elites)
            print('The offspring population after adding the elites is:')
            fn_display_pop(offspring_pop)
        # Write the populaiton to a csv file for restart purposes
        if restart_file:
            csv_name = f'optwrf_restart_g{str(gen).zfill(3)}.csv'
            with open(csv_name, "w") as csvfile:
                csv_writer = csv.writer(csvfile)
                header = ['start_date', 'mp_physics', 'ra_lw_physics', 'ra_sw_physics',
                          'sf_surface_physics', 'bl_pbl_physics', 'cu_physics', 'sfclay_physics']
                csv_writer.writerow(header)
                for individual in offspring_pop:
                    csv_data = [individual.Start_date] + individual.Genes
                    csv_writer.writerow(csv_data)
        # Calculate the fitness of the population
        print('Calculating the fitness of the generation {} population...'.format(gen))
        sys.stdout.flush()
        fn_get_pop_fitness(offspring_pop)
        # Initialize the next generation
        population = offspring_pop
        gen += 1
        sys.stdout.flush()

    WRFga_winner = simplega.get_best(population)
    print(f'\nWRFga finished running in {datetime.datetime.now() - start_time}')
    print(f'{WRFga_winner.Genes} is the best parameter combination; all simulations are below')
    print_database(db_conn)
    close_conn_to_db(db_conn)

    return WRFga_winner
