import sqlite3
from wrfga import Chromosome

conn = sqlite3.connect(':memory:')
c = conn.cursor()

c.execute("""CREATE TABLE simulations (
            ra_lw_physics INTEGER,
            ra_sw_physics INTEGER,
            sf_surface_physics INTEGER,
            bl_pbl_physics INTEGER,
            cu_physics INTEGER,
            sf_sfclay_physics INTEGER,
            fitness FLOAT 
            )
            """)


def insert_sim(params):
    with conn:
        c.execute("INSERT INTO simulations VALUES (:ra_lw_physics, :ra_sw_physics, :pay)",
            {})


def get_sim_by_params(params):
    c.execute("""SELECT * FROM simulations 
                WHERE ra_lw_physics = :ra_lw_physics""", {'ra_lw_physics':params[1]})
    return c.fetchall()


emp_1 = Employee('John', 'Doe', 80000)
emp_2 = Employee('Jane', 'Doe', 90000)

insert_emp(emp_1)
insert_emp(emp_2)

emps = get_emps_by_name('Doe')
print(emps)

update_pay(emp_2, 95000)
remove_emp(emp_1)

emps = get_emps_by_name('Doe')
print(emps)

conn.close()
