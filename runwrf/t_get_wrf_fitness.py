import unittest
import wrfga
import datetime
from t_wrfga import get_wrf_fitness


class WRFFitnessTests(unittest.TestCase):
    def get_wrf_fitness_test(self):
        start_time = datetime.datetime.now()
        param_ids = [0, 3, 7, 7, 5, 2, 1]
        individual = wrfga.Chromosome(param_ids)
        fitness = get_wrf_fitness(individual.Genes)
        wrfga.display(individual, start_time)
        self.assertGreaterEqual(0, fitness)
