"""
Tests the optimize_wrf_physics functions

"""

import os
from optwrf.optimize_wrf_physics \
    import get_wrf_fitness, run_simplega, conn_to_db, print_database, sql_to_csv, close_conn_to_db
from optwrf.runwrf import determine_computer
import optwrf.wrfparams as wp
import optwrf.runwrf as rw
import optwrf.simplega as sga
import optwrf.optimize_wrf_physics as owp

param_ids = [10, 1, 1, 2, 2, 3, 2]
start_date = 'Dec 31  2011'
end_date = 'Jan 1 2012'
on_aws, on_cheyenne, on_magma = determine_computer()


def test_generate_random_dates():
    random_start_date, random_end_date = sga.generate_random_dates()
    print(f'Starting forecast at {random_start_date}')
    print(f'Ending forecast at {random_end_date}')
    assert random_start_date is not None
    assert random_end_date is not None


def test_get_wrf_fitness():
    if [on_aws, on_cheyenne, on_magma].count(True) is 0:
        print('\n!!!Not running test_wrf_era5_diff -- switch to Magma, Cheyenne, or AWS!!!')
        return
    fitness = get_wrf_fitness(param_ids, start_date, end_date)
    assert fitness >= 0


def test_run_simplega():
    WRFga_winner = run_simplega(pop_size=4, n_generations=2, testing=True)
    assert WRFga_winner.Fitness >= 0


def test_print_database():
    db_conn = conn_to_db('optwrf.db')
    print_database(db_conn)
    close_conn_to_db(db_conn)


def test_update_sim():
    # Generate one individual
    # dat = rw.format_date(start_date)
    # param_ids = wp.flexible_generate()
    individual = sga.Chromosome(param_ids, fitness=100, start_date=start_date)
    # Put individual in the database
    db_conn = conn_to_db('optwrf_repeat.db')
    owp.insert_sim(individual, db_conn)
    print_database(db_conn)
    # Generate the same individual again
    # new_params = wp.flexible_generate()
    individual = sga.Chromosome(param_ids, fitness=50, start_date='Jan 1 2011')
    # Update the database
    owp.update_sim(individual, db_conn)
    print_database(db_conn)


def test_sql_to_csv():
    csv_outfile = 'optwrf_database.csv'
    db_conn = conn_to_db('optwrf.db')
    sql_to_csv(csv_outfile, db_conn)
    close_conn_to_db(db_conn)
    assert os.path.exists(csv_outfile) == 1
