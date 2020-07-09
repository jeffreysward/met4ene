"""
Tests the optimize_wrf_physics functions

"""

import os
from optwrf.optimize_wrf_physics \
    import get_wrf_fitness, run_simplega, conn_to_db, print_database, sql_to_csv, close_conn_to_db
from optwrf.runwrf import determine_computer
import optwrf.wrfparams as wp
import optwrf.simplega as sga
import optwrf.optimize_wrf_physics as owp

param_ids = [8, 7, 3, 1, 1, 10, 1]
start_date = 'Dec 13  2011'
end_date = 'Dec 14 2011'
on_aws, on_cheyenne, on_magma = determine_computer()


def test_generate_random_dates():
    """Check if start and end dates can be randomly generated."""
    random_start_date, random_end_date = sga.generate_random_dates()
    print(f'Starting forecast on {random_start_date}')
    print(f'Ending forecast on {random_end_date}')
    r_start_date, r_end_date = sga.generate_random_dates(input_start_date=start_date)
    print(f'Starting forecast on {r_start_date}')
    print(f'Ending forecast on {r_end_date}')
    assert random_start_date is not None
    assert random_end_date is not None
    assert r_start_date is not None
    assert r_end_date is not None


def test_seed_initial_population():
    """Check that individuals specified via an input CSV file
    can be used to create an initial population."""
    # Test if a initial population can be read in from CSV
    i_population = owp.seed_initial_population('initial_populations.csv')
    # Test if a new population can be generated with i_population as the base
    pop_size = 30
    population = sga.generate_population(pop_size, i_population)
    assert type(i_population) is list
    assert len(population) == pop_size


def test_get_wrf_fitness():
    """Checks to see if the WRF fitness can be calculated for the default simulaiton.
    For this, you must be on Magma, Cheyenne, or AWS."""
    if [on_aws, on_cheyenne, on_magma].count(True) is 0:
        print('\n!!!Not running test_wrf_era5_diff -- switch to Magma, Cheyenne, or AWS!!!')
        return
    fitness = get_wrf_fitness(param_ids, start_date, end_date)
    assert fitness >= 0


def test_run_simplega():
    """Tests the genetic algroithm framework without running WRF."""
    WRFga_winner = run_simplega(pop_size=6, n_generations=1, testing=True)
    assert WRFga_winner.Fitness >= 0


def test_print_database():
    """Checks to see if the contnts of a database can be successfully printed to the screen."""
    db_conn = conn_to_db('optwrf.db')
    print_database(db_conn)
    close_conn_to_db(db_conn)


def test_update_sim():
    """Checks to make sure that entries in the database can be updated."""
    # Generate a random set of parameters, a random start date, and a Chromosome
    r_start_date, r_end_date = sga.generate_random_dates()
    r_param_ids = wp.flexible_generate()
    individual = sga.Chromosome(r_param_ids, fitness=100, start_date=r_start_date, end_date=r_end_date)
    # Put individual in the database
    db_conn = conn_to_db('optwrf_repeat.db')
    owp.insert_sim(individual, db_conn)
    print_database(db_conn)
    # Generate a new random start date and a Chromosome
    r_start_date, r_end_date = sga.generate_random_dates()
    individual = sga.Chromosome(r_param_ids, fitness=50, start_date=r_start_date, end_date=r_end_date)
    # Update the individual in the database database
    owp.update_sim(individual, db_conn)
    print_database(db_conn)


def test_sql_to_csv():
    """Checks the function that writes the SQL database to a CSV file."""
    csv_outfile = 'optwrf_database.csv'
    db_conn = conn_to_db('optwrf.db')
    sql_to_csv(csv_outfile, db_conn)
    close_conn_to_db(db_conn)
    assert os.path.exists(csv_outfile) == 1
