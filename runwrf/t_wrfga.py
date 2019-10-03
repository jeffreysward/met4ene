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


class WRFGATests(unittest.TestCase):
    def test(self):
        start_time = datetime.datetime.now()
        pop_size = 6
        n_elites = int(0.1*pop_size) if int(0.1*pop_size) < 0 else 1
        print('The number of elites is {}'.format(n_elites))
        n_generations = 3
        optimal_fitness = 0

        def fn_display(individual):
            wrfga.display(individual, start_time)

        def fn_display_pop(pop):
            wrfga.display_pop(pop, fn_display)

        def fn_get_pop_fitness(pop):
            for ii in range(0, len(pop)):
                if pop[ii].Fitness is None:
                    pop[ii].Fitness = get_fitness()
            fn_display_pop(pop)

        # Create an initial population
        population = wrfga.generate_population(pop_size)

        # Calculate the fitness of the initial population
        print('Calculating the fitness of the initial population...')
        fn_get_pop_fitness(population)

        # Until the specified generation number is reached,
        gen = 1
        while gen <= n_generations:
            print('\n------ Starting generation {} ------'.format(gen))
            # Select the mating population
            mating_pop = wrfga.selection(population, pop_size)
            print('The mating population is:')
            fn_display_pop(mating_pop)
            # Carry out crossover
            offspring_pop = []
            while len(offspring_pop) < pop_size - n_elites:
                offspring = wrfga.crossover(mating_pop)
                if offspring is not None:
                    offspring_pop.extend(offspring)
            print('The offspring population is:')
            fn_display_pop(offspring_pop)
            # Give a chance for mutation on each member of the offspring population
            offspring_pop = wrfga.mutate(offspring_pop)
            print('The offspring population after mutation is:')
            fn_display_pop(offspring_pop)
            # Copy the elites into the offspring population
            elites = wrfga.find_elites(population, n_elites, fn_display_pop)
            if elites is not None:
                offspring_pop.extend(elites)
                print('The offspring population after adding the elites is:')
                fn_display_pop(offspring_pop)
            # Calculate the fitness of the population
            print('Calculating the fitness of the generation {} population...'.format(gen))
            fn_get_pop_fitness(offspring_pop)
            # Initialize the next generation
            population = offspring_pop
            gen += 1

        self.assertEqual(0, optimal_fitness)



