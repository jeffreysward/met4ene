import unittest
import wrfga
import datetime
from t_wrfga import get_wrf_fitness


class WRFFitnessTests(unittest.TestCase):
    def get_wrf_fitness_test(self):
        start_time = datetime.datetime.now()
        param_ids = [10, 1, 1, 2, 2, 3, 2]
        individual = wrfga.Chromosome(param_ids)
        individual.Fitness = get_wrf_fitness(individual.Genes)
        wrfga.display(individual, start_time)
        self.assertLessEqual(0, individual.Fitness)
