import random
import time
import statistics
import wrfparams
import sys
import datetime


# Define a Chromosome class the provides information about each unique individual
class Chromosome:
    def __init__(self, genes, fitness=None):
        self.Genes = genes
        self.Fitness = fitness
        self.Age = 0


def display(individual, start_time):
    time_diff = datetime.datetime.now() - start_time
    print("Genes:{}\tFitness: {}\tElapsed Time: {}".format(
        ''.join(str(individual.Genes)), individual.Fitness, time_diff))


def display_pop(population, fn_display):
    for i in range(0, len(population)):
        fn_display(population[i])


def generate_genes():
    new_individual = wrfparams.flexible_generate()
    return new_individual


# This method provides a way to randomly generate an initial population for the GA
def generate_population(pop_size):
    population = []
    while len(population) < pop_size:
        new_individual = generate_genes()
        new_individual = Chromosome(new_individual)
        population.append(new_individual)
    return population


# The selection operator carries out a tournament selection,
# by selecting the fittest individual among a group of randomly selected individuals, to create the mating population.
def selection(population, pop_size):

    if 1 < pop_size < 30:
        mating_pop_size = int(0.5 * pop_size)
        tournament_size = int(0.5 * pop_size)
    elif pop_size is 1:
        mating_pop_size = 1
        tournament_size = 1
    else:
        mating_pop_size = int(0.5 * pop_size)
        tournament_size = int(0.1 * pop_size)

    mating_population = []
    while len(mating_population) < mating_pop_size:
        tournament_pop_idx = random.sample(range(0, pop_size), tournament_size)
        tournament_pop = [population[i] for i in tournament_pop_idx]
        mating_population.append(get_best(tournament_pop))
    return mating_population


# The crossover operator takes in the genes of two parent individuals
# and randomly exchanges one gene between the two producing two offspring.
def crossover(mating_population):
    parent_idxs = random.sample(range(0, len(mating_population)), 2)
    if random.randint(0, 1) is 1:
        parent1_genes = mating_population[parent_idxs[0]].Genes[:]
        child1_genes = parent1_genes
        parent2_genes = mating_population[parent_idxs[1]].Genes[:]
        child2_genes = parent2_genes
        gene_idx = random.randint(0, len(parent1_genes) - 1)
        child1_genes[gene_idx], child2_genes[gene_idx] = parent2_genes[gene_idx], parent1_genes[gene_idx]
        offspring = [Chromosome(child1_genes), Chromosome(child2_genes)]
    else:
        offspring = None
    return offspring


# The mutate operator takes in the genes of one offspring
# and randomly replaces one of the genes from the set of choices.
def mutate(offspring_population):
    for child in offspring_population:
        if random.randint(1, len(offspring_population)) is 1:
            new_child = generate_genes()
            gene_idx = random.randint(0, len(new_child) - 1)
            print('--> Mutating gene in position {} in child {}.'.format(gene_idx, child.Genes))
            child.Genes[gene_idx] = new_child[gene_idx]
    return offspring_population


# Function that finds the location of the best individual within the population
def get_best(population):
    fitness = [population[i].Fitness for i in range(0, len(population))]
    print('The tournament fitness values are: {}'.format(fitness))
    best_fitness = min(fitness)
    best_index = fitness.index(best_fitness)
    best_individual = population[best_index]
    return best_individual


def find_elites(population, n_elites, fn_display_pop):
    order = sorted(population, key=lambda x: x.Fitness)
    elites = order[0:n_elites]
    print('The elites moving to the next generation are: ')
    fn_display_pop(elites)
    return elites


class Benchmark:
    @staticmethod
    def run(function):
        timings = []
        stdout = sys.stdout
        for i in range(100):
            sys.stdout = None
            startTime = time.time()
            function()
            seconds = time.time() - startTime
            sys.stdout = stdout
            timings.append(seconds)
            mean = statistics.mean(timings)
            if i < 10 or i % 10 == 9:
                print("{} {:3.2f} {:3.2f}".format(1 + i, mean, statistics.stdev(timings, mean) if i > 1 else 0))

