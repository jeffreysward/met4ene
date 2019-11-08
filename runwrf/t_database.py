import sqlite3
from wrfga import Chromosome

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


def insert_sim(individual):
    print(individual.Genes)
    with conn:
        c.execute("""INSERT INTO simulations VALUES (
                    :mp_physics, :ra_lw_physics, :ra_sw_physics, :sf_surface_physics, 
                    :bl_pbl_physics, :cu_physics, :sf_sfclay_physics, :fitness)""",
            {'mp_physics': individual.Genes[0], 'ra_lw_physics': individual.Genes[1],
             'ra_sw_physics': individual.Genes[2], 'sf_surface_physics': individual.Genes[3],
             'bl_pbl_physics': individual.Genes[4], 'cu_physics': individual.Genes[5],
             'sf_sfclay_physics': individual.Genes[6], 'fitness': individual.Fitness})


def get_individual_by_genes(geneset):
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


sim_1 = Chromosome([28, 31, 5, 7, 1, 93, 1])
sim_2 = Chromosome([5, 99, 24, 8, 11, 7, 1])


insert_sim(sim_1)
insert_sim(sim_2)


sim = get_individual_by_genes([1, 31, 5, 7, 1, 93, 1])
if sim is not None:
    print(f'Genes: {sim.Genes}\t Fitness: {sim.Fitness}')

conn.close()
