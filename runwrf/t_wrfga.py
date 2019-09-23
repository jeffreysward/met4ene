import unittest
import wrfga
import datetime
import random


def get_fitness(genes):
    return genes.count(1)


def display(population_best, start_time):
    time_diff = datetime.datetime.now() - start_time
    print("Best Genes:{}\tFitness: {}\tElapsed Time: {}".format(
        ', '.join(population_best.Genes), population_best.Fitness, time_diff))

class OneMaxTest(unittest.TestCase):
    def test(self, length=100):
        geneset = [1, 0]
        start_time = datetime.datetime.now()
        optimal_fitness = length

        def fn_display(individual):
            display(individual, start_time)

        # Create an initial population

        # Calculate the fitness of the initial population

        # Until the max generation number is reached,

            # Carry out crossover

            # Carry out mutation

            # Calculate the fitness of the population





