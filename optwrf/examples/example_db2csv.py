"""
Write Contents of SQL Datatbase to CSV
======================================

This example shows how to dump the contents of the SQL optwrf database (optwrf.db)
to a CSV file, so it can be easily read.

"""
import optwrf.optimize_wrf_physics as owp


# Name of the csv file and optwrf database
#csv_outfile = 'optwrf_database.csv'
csv_outfile = 'optwrf_database_041620_11am.csv'
#sql_database = 'optwrf.db'
sql_database = 'optwrf_041620_11am.db'

# Connect to the sql database
db_conn = owp.conn_to_db(sql_database)

# Write the database contents to CSV
owp.sql_to_csv(csv_outfile, db_conn)

# Close connection to the sql database
owp.close_conn_to_db(db_conn)
