"""
A simple genetic algorithm for optimizing the WRF model physics.
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
Known Issues/Wishlist:

"""

import datetime
import random

import optwrf.wrfparams as wrfparams


# Define a Chromosome class the provides information about each unique individual
class Chromosome:
    def __init__(self, genes, start_date, end_date, fitness=None):
        self.Genes = genes
        self.Fitness = fitness
        self.Start_date = start_date
        self.End_date = end_date


def display(individual, start_time):
    """
    Aids in display of an individual Chromosome instance.

    :param individual: Chromosome instance
    :param start_time:

    """
    time_diff = datetime.datetime.now() - start_time
    print("Genes:{}\tFitness: {}\tElapsed Time: {}".format(
        ''.join(str(individual.Genes)), individual.Fitness, time_diff))


def display_pop(population, fn_display):
    """
    Aids in display of an entire population.

    :param population:
    :param fn_display:

    """
    for i in range(0, len(population)):
        fn_display(population[i])


def generate_genes():
    """
    Generates genes for a new individual to be placed within a population.

    :return:
    new individual : list
        list of WRF model physics parameters

    """
    new_individual = wrfparams.flexible_generate()
    return new_individual


def generate_random_dates(year=2011, n_days=1):
    """
    Generates a random start date and end date for running the WRF model.
    Start and end dates are offset by the parameter n_days, which is set to 1 as default

    Parameters:
    ----------
    year : integer or None
        Specifies the year within which you want random days to be selected.
        If this is specified as None, random dates between Jan 1, 2000 and today can be selected.
    n_days : integer
        Specifies the nuber of days between the start and the end dates of the simulation.
        The default is set to 1 day.

    Returns:
    ----------
    random_start_date : datetime64
        datetime64 array specifying the simulation start date
    random_end_date : datetime64
        datetime64 array specifying the simulation start date

    """
    if year is None:
        start_date = datetime.date(2000, 1, 1)
        end_date = datetime.date.today()
    else:
        start_date = datetime.date(year, 1, 1)
        end_date = datetime.date(year, 12, 31)

    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_number_of_days = random.randrange(days_between_dates)
    random_start_date = start_date + datetime.timedelta(days=random_number_of_days)
    random_end_date = random_start_date + datetime.timedelta(days=n_days)

    return random_start_date, random_end_date


def generate_population(pop_size):
    """
    This method provides a way to randomly generate an initial population for the GA.

    :param pop_size:
    :return:

    """
    population = []
    while len(population) < pop_size:
        new_genes = generate_genes()
        start_date, end_date = generate_random_dates()
        new_individual = Chromosome(new_genes, start_date, end_date)
        population.append(new_individual)
    return population


def selection(population, pop_size):
    """
    The selection operator carries out a tournament selection,
    by selecting the fittest individual among a group of randomly selected individuals,
    to create the mating population.

    :param population:
    :param pop_size:
    :return:

    """

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


def crossover(mating_population):
    """
    The crossover operator takes in the genes of two parent individuals
    and randomly exchanges one gene between the two producing two offspring.

    :param mating_population:
    :return:

    """
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


def mutate(offspring_population):
    """
    The mutate operator takes in the genes of one offspring
    and randomly replaces one of the genes from the set of choices.

    :param offspring_population:
    :return:

    """
    for child in offspring_population:
        if random.randint(1, len(offspring_population)) is 1:
            new_child = generate_genes()
            gene_idx = random.randint(0, len(new_child) - 1)
            print('--> Mutating gene in position {} in child {}.'.format(gene_idx, child.Genes))
            child.Genes[gene_idx] = new_child[gene_idx]
    return offspring_population


def get_best(population):
    """
    Finds the location of the individual within the population with the best fitness

    :param population:
    :return:

    """
    fitness = [population[i].Fitness for i in range(0, len(population))]
    print('The tournament fitness values are: {}'.format(fitness))
    best_fitness = min(fitness)
    best_index = fitness.index(best_fitness)
    best_individual = population[best_index]
    return best_individual


def find_elites(population, n_elites, fn_display_pop):
    """
    Finds elites within the population

    :param population:
    :param n_elites:
    :param fn_display_pop:
    :return:

    """
    order = sorted(population, key=lambda x: x.Fitness)
    elites = order[0:n_elites]
    print('The elites moving to the next generation are: ')
    fn_display_pop(elites)
    return elites
