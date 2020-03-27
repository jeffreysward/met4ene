"""
Tests the optimize_wrf_physics functions

"""

import os
from optwrf.optimize_wrf_physics \
    import get_wrf_fitness, run_simplega, conn_to_db, print_database, sql_to_csv, close_conn_to_db
from optwrf.runwrf import determine_computer

param_ids = [10, 1, 1, 2, 2, 3, 2]
start_date = 'Dec 31  2011'
end_date = 'Jan 1 2012'
on_aws, on_cheyenne, on_magma = determine_computer()


def test_get_wrf_fitness():
    if [on_aws, on_cheyenne, on_magma].count(True) is 0:
        print('\n!!!Not running test_wrf_era5_diff -- switch to Magma, Cheyenne, or AWS!!!')
        return
    fitness = get_wrf_fitness(param_ids, start_date, end_date)
    assert fitness >= 0


def test_run_simplega():
    WRFga_winner = run_simplega(pop_size=10, n_generations=4, testing=True)
    assert WRFga_winner.Fitness >= 0


def test_print_database():
    db_conn = conn_to_db('optwrf.db')
    print_database(db_conn)
    close_conn_to_db(db_conn)


def test_update_sim():
    db_conn = conn_to_db('optwrf_repeat.db')
    pass


def test_sql_to_csv():
    csv_outfile = 'optwrf_database.csv'
    db_conn = conn_to_db('optwrf.db')
    sql_to_csv(csv_outfile, db_conn)
    close_conn_to_db(db_conn)
    assert os.path.exists(csv_outfile) == 1
