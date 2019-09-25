import unittest
import wrfga
import datetime
import random
import os
import time


# class Fitness:
#     def __init__(self, total_error):
#         self.TotalError = total_error
#
#     def __gt__(self, other):
#         self.TotalError < other.TotalError


# Define a function that produces a random fitness value between 0 - 100
def get_fitness():
    return random.randrange(0, 100)


def display(individual, start_time):
    time_diff = datetime.datetime.now() - start_time
    print("Genes:{}\tFitness: {}\tElapsed Time: {}".format(
        ''.join(str(individual.Genes)), individual.Fitness, time_diff))


def display_pop(populaiton, start_time):
    for i in range(0, len(populaiton)):
        display(populaiton[i], start_time)



class WRFGATests(unittest.TestCase):
    def test(self):
        start_time = datetime.datetime.now()
        pop_size = 10
        n_generations = 1
        optimal_fitness = 0

        def fn_display(individual):
            display(individual, start_time)

        def fn_display_pop(populaiton):
            display_pop(populaiton, start_time)

        # Create an initial population
        population = wrfga.generate_population(pop_size)

        # Calculate the fitness of the initial population
        print('Calculating the fitness of the initial population...')
        for i in range(0, pop_size):
            population[i].Fitness = get_fitness()
        fn_display_pop(population)

        # Until the specified generation number is reached,
        gen = 1
        while gen <= n_generations:
            print('\n------ Starting generation {} ------'.format(gen))
            # Select the mating population
            mating_pop = wrfga.selection(population, pop_size)
            print('The mating population is:')
            fn_display_pop(mating_pop)
            # Carry out crossover

            # Carry out mutation

            # Calculate the fitness of the population

            gen += 1

        self.assertEqual(0, optimal_fitness)



