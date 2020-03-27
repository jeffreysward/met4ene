"""
A framework to run the simple genetic algorithm for optimizing the WRF model physics.
All simulation parameters and fitness values are saved in an SQL database.
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
Known Issues/Wishlist:
- This whole things needs to change...
    - I want the thread pool executor to operate within a Class or a function.
    - It would be cool if PyCharm recognized the SQL syntax.

"""

import concurrent.futures
import datetime
import random
import sqlite3
import csv
import time

from optwrf.runwrf import WRFModel
import optwrf.simplega as simplega
from optwrf.simplega import Chromosome


# class Fitness:
#     def __init__(self, total_error):
#         self.TotalError = total_error
#
#     def __gt__(self, other):
#         self.TotalError < other.TotalError


def conn_to_db(db_name='optwrf.db'):
    """
        Opens the connection to a SQL database.

        Parameters:
        ----------
        db_name : SQL database name
            Can be ':memory:' if you only want the database to be held in memory

        Returns:
        --------
        db_conn : database connection object

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
                        fitness FLOAT 
                        )""")
    return db_conn


def insert_sim(individual, db_conn):
    """
    Inserts a simulation into the SQL database held in memory or written to a .db file.

    Parameters:
    ----------
    individual : simplega.Chromosome instance
        The simulation that you would like to add to the simulation database.
    db_conn :
        lorem ipsum

    """

    print(f'...Adding {individual.Genes} to the simulation database...')
    c = db_conn.cursor()
    with db_conn:
        c.execute("""INSERT INTO simulations VALUES (
                    :start_date, :mp_physics, :ra_lw_physics, :ra_sw_physics, :sf_surface_physics, 
                    :bl_pbl_physics, :cu_physics, :sf_sfclay_physics, :fitness)""",
                  {'start_date': individual.Start_date, 'mp_physics': individual.Genes[0],
                   'ra_lw_physics': individual.Genes[1],
                   'ra_sw_physics': individual.Genes[2], 'sf_surface_physics': individual.Genes[3],
                   'bl_pbl_physics': individual.Genes[4], 'cu_physics': individual.Genes[5],
                   'sf_sfclay_physics': individual.Genes[6], 'fitness': individual.Fitness})


def update_sim(individual, db_conn):
    """
    Inserts a simulation into the SQL database held in memory or written to a .db file.

    Parameters:
    ----------
    individual : simplega.Chromosome instance
        The simulation that you would like to add to the simulation database.
    db_conn :
        lorem ipsum

    """

    print(f'...Updating {individual.Genes} in the simulation database...')
    c = db_conn.cursor()
    with db_conn:
        c.execute("""UPDATE simulations 
                    SET start_date = :start_date, 
                    fitness = :fitness 
                    WHERE mp_physics = :mp_physics
                    AND ra_lw_physics = :ra_lw_physics
                    AND ra_sw_physics = :ra_sw_physics
                    AND sf_surface_physics = :sf_surface_physics
                    AND bl_pbl_physics = :bl_pbl_physics
                    AND cu_physics = :cu_physics
                    AND sf_sfclay_physics = :sf_sfclay_physics""",
                    {'start_date': individual.Start_date, 'fitness': individual.Fitness,
                    'mp_physics': individual.Genes[0], 'ra_lw_physics': individual.Genes[1],
                    'ra_sw_physics': individual.Genes[2], 'sf_surface_physics': individual.Genes[3],
                    'bl_pbl_physics': individual.Genes[4], 'cu_physics': individual.Genes[5],
                    'sf_sfclay_physics': individual.Genes[6]})


def get_individual_by_genes(individual, db_conn):
    """
    Looks for an indivual set of genes in an SQLite database.

    Parameters:
    ----------
    individual : Chromosome Class instance
        lorem ipsum

    Returns:
    ----------
    past_sim : simplega.Chromosome
        Simulation that was run previously and stored in the SQLite database.

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
        past_sim = Chromosome(list(sim_data[0:-1]), sim_data[-1])
    else:
        return None
    return past_sim


def print_database(db_conn):
    """
        Prints the entire SQLite simulation database.

        Parameters:
        ----------
        db_conn :
            lorem ipsum

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

    Parameters:
    ----------
    csv_file_path : string
        Exact path to where you would like to csv to be saved ending with the file name.
        e.g., csv_file_path = '/home/jas983/data/test.csv'
    db_conn : database connection object

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

        Parameters:
        ----------
        db_conn : SQL database name
            Can be ':memory:' if you only want the database to be held in memory

    """

    db_conn.close()


def get_fitness(param_ids):
    """
    This function produces a random fitness value between 0 - 100

    Parameters:
    ----------
    param_ids : list of integers
        Numeric values corresponding to each WRF physics parameterization.

    Returns:
    ----------
    fitness : integer
        A randomly generated integer between 1 and 100.

    """

    print('Calculating fitness for: {}'.format(param_ids))
    time.sleep(2)
    fitness = random.randrange(0, 100)
    return fitness


def get_wrf_fitness(param_ids, start_date='Jan 15 2011', end_date='Jan 16 2011',
                    bc_data='ERA', n_domains=1, correction_factor=0.00033806364898425066,
                    setup_yaml='dirpath.yml', verbose=False):
    """
    Using the input physics parameters, date, boundary condition, and domain data,
    this function runs the WRF model and computes the error between WRF and ERA5.

    Parameters:
    ----------
    param_ids : list of integers
        Numeric values corresponding to each WRF physics parameterization.
    start_date : string
        lorem ipsum
    end_date : string
        lorem ipsum
    bc_data : string
        lorem ipsum
    n_domains : integer
        lorem ipsum
    setup_yaml : string
        lorem ipsum

    Returns:
    ----------
    fitness : float
        Fitness value denoting how well the WRF model run performed.

    """

    print('- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -')
    print('\nCalculating fitness for: {}'.format(param_ids))

    # Create a WRFModel instance
    wrf_sim = WRFModel(param_ids, start_date, end_date,
                       bc_data=bc_data, n_domains=n_domains, setup_yaml=setup_yaml, verbose=verbose)

    # Next, get boundary condition data for the simulation
    # ERA is the only supported data type right now.
    vtable_sfx = wrf_sim.get_bc_data()

    # Setup the working directory to run the simulation
    wrf_sim.wrfdir_setup(vtable_sfx)

    # Prepare the namelists
    wrf_sim.prepare_namelists()

    # Run WPS
    success = wrf_sim.run_wps()
    if verbose:
        print(f'WPS ran successfully? {success}')

    # Run REAL
    if success:
        success = wrf_sim.run_real()
        if verbose:
            print(f'Real ran successfully? {success}')

    # RUN WRF
    if success:
        success = wrf_sim.run_wrf(disable_timeout=True)
        if verbose:
            print(f'WRF ran successfully? {success}')

    # Postprocess wrfout file and ERA5 data
    if success:
        wrf_sim.process_wrfout_data()
        wrf_sim.process_era5_data()

    # Compute the error between WRF run and ERA5 dataset and return fitness
    if success:
        mae = wrf_sim.wrf_era5_diff()
        ghi_mean_error = mae[1]
        wpd_mean_error = mae[2]
        fitness = ghi_mean_error + correction_factor * wpd_mean_error
    else:
        fitness = 6.022 * 10 ** 23

    # The following comment is deprecated code ... I now use an SQLite database to hold simulaiton information.
    # Write parameter combinations to CSV
    # (if you would like to restart this, you must manually delete this CSV)
    # write_param_csv(wrf_sim.param_ids, fitness)
    return fitness


def run_simplega(pop_size, n_generations, testing=False):
    """
    Runs the simple genetic algorithm specified in simplega either
    to optimize the WRF model physics or with a test fitness function
    that randomly selects a fitness value for each individual Chromosome.

    I'm not sure if it would be better to make this a Class...

    Parameters:
    ----------
    pop_size : int
        Desired population size for the genetic algorithm
    n_generations : int
        Total number of generations after which the genetic algorithm will time out.
    testing : boolean
        Flag that uses a random number generator as the fitness function when True.

    Returns:
    ----------
    WRFga_winner : simplega.Chromosome instance
        The simulation preforming the best in the genetic algorithm.

    """

    db_conn = conn_to_db()

    start_time = datetime.datetime.now()
    n_elites = int(0.34 * pop_size) if int(0.34 * pop_size) > 0 else 1
    print('The number of elites is {}'.format(n_elites))

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

        Parameters
        ----------
        pop : list of simplega.Chromosome
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
                            fitness_threads.append(executor.submit(get_wrf_fitness, individual.Genes))
                        else:
                            fitness_threads.append(executor.submit(get_fitness, individual.Genes))
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
                    insert_sim(individual, db_conn)
                ii += 1
        fn_display_pop(pop)

        # # The following block is legacy code to run in serial
        # for individual in pop:
        #     if individual.Fitness is None:
        #         individual.Fitness = get_fitness(individual.Genes)
        # fn_display_pop(pop)

    # Create an initial population
    population = simplega.generate_population(pop_size)

    # Calculate the fitness of the initial population
    print('--> Calculating the fitness of the initial population...')
    fn_get_pop_fitness(population)

    # Until the specified generation number is reached,
    gen = 1
    while gen <= n_generations:
        print('\n------ Starting generation {} ------'.format(gen))
        # Select the mating population
        mating_pop = simplega.selection(population, pop_size)
        print('The mating population is:')
        fn_display_pop(mating_pop)
        # Carry out crossover
        offspring_pop = []
        while len(offspring_pop) < pop_size - n_elites:
            offspring = simplega.crossover(mating_pop)
            if offspring is not None:
                offspring_pop.extend(offspring)
        print('The offspring population is:')
        fn_display_pop(offspring_pop)
        # Give a chance for mutation on each member of the offspring population
        offspring_pop = simplega.mutate(offspring_pop)
        print('The offspring population after mutation is:')
        fn_display_pop(offspring_pop)
        # Copy the elites into the offspring population
        elites = simplega.find_elites(population, n_elites, fn_display_pop)
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

    WRFga_winner = simplega.get_best(population)
    print(f'\nWRFga finished running in {datetime.datetime.now() - start_time}')
    print(f'{WRFga_winner.Genes} is the best parameter combination; all simulations are below')
    print_database(db_conn)
    close_conn_to_db(db_conn)

    return WRFga_winner
