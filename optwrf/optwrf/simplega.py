"""
A simple genetic algorithm for optimizing the WRF model physics.


Known Issues/Wishlist:

"""

import datetime
import random

import optwrf.helper_functions as hf
import optwrf.wrfparams as wrfparams
import optwrf.runwrf as runwrf


class Chromosome:
    """
    This class provides information about each unique individual to be placed within
    populations used in the genetic algorithm (e.g., parent population, mating population,
    or offspring population). Four pieces of information are associated with each individual:
        1. A set of genes corresponding to six major physics parameters that be changed within
        the WRF model (microphysics, longwave radiation, shortwave radiation, land surface,
        planetary boundary layer, and cumulus).
        2. A start date defining when the WRF forecast will begin running.
        3. An end date defining when the WRF forecast will finish running.
        4. A fitness value that will be used to determine how well each instance preforms.
    """
    def __init__(self, genes, start_date, end_date, fitness=None, runtime=None):
        self.Genes = genes
        self.Start_date = start_date
        self.End_date = end_date
        self.Fitness = fitness
        self.Runtime = runtime


def display(individual, start_time):
    """
    Aids in display of an individual Chromosome instanceby printing useful information
    to the screen.

    :param individual: Chromosome instance
    :param start_time: datetime object
        defining when the simiulation began running.

    """
    time_diff = hf.strfdelta(datetime.datetime.now() - start_time, fmt='{D:02}d {H:02}h {M:02}m {S:02}s')
    print(f'Genes:{str(individual.Genes)}\tFitness: {individual.Fitness}\t'
          f'Sim Runtime: {str(individual.Runtime)}\tGA Time: {time_diff}')


def display_pop(population, fn_display):
    """
    Aids in display of an entire population by printing useful information
    to the screen.

    :param population: list of Chromosome instances
    :param fn_display: function
        defining how to display eah individual in the population.

    """
    for i in range(0, len(population)):
        fn_display(population[i])


def generate_genes():
    """
    Generates genes for a new individual to be placed within a population.

    :return:
    new individual: list
        list of WRF model physics parameters

    """
    new_individual = wrfparams.flexible_generate()
    return new_individual


def generate_random_dates(year=2011, n_days=1, input_start_date=None):
    """
    Generates a random start date and end date for running the WRF model.
    Start and end dates are offset by the parameter n_days, which is set to 1 as default

    :param year: integer or None
        specifying the year within which you want random days to be selected.
        If this is specified as None, random dates between Jan 1, 2000 and today can be selected.
    :param n_days: integer
        specifying the nuber of days between the start and the end dates of the simulation.
        The default is set to 1 day.
    :param input_start_date: string
        specifying a desired start date.
    :return random_start_date: string
        specifying the simulation start date.
    :return random_end_date: string
        specifying the simulation end date.

    """
    if input_start_date is None:
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
    else:
        random_start_date = runwrf.format_date(input_start_date)
    random_end_date = random_start_date + datetime.timedelta(days=n_days)
    # Change from datetime object to string
    random_start_date = random_start_date.strftime('%b %d %Y')
    random_end_date = random_end_date.strftime('%b %d %Y')

    return random_start_date, random_end_date


def generate_population(pop_size, initial_population=None):
    """
    This method provides a way to randomly generate an initial population for the GA.

    :param pop_size: integer
        specifies the number of individuals in the population to be generated.
    :param initial_population: list of Chromosome instances
        allows users to seed the population with individuals of desired
        parameter combinations and start/end dates.
    :return: population: list of Chromosome instances

    """
    if initial_population is None:
        population = []
    else:
        population = initial_population
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

    :param population: list of Chromosome instances
        specifies the population that the selection operator will select from.
    :param pop_size: integer
        number of individuals within the population
    :return: mating population: list of Chromosome instances
        population of individuals that have been deemed fit enough by the selection operator
        and will be sent to the crossover operator.

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

    :param mating_population: list of Chromosome instances
        population of individuals that have been deemed fit enough by the selection operator.
    :return: offspring_population: list of Chromosome instances
        population of individuals created from the genes of mating population.

    """
    parent_idxs = random.sample(range(0, len(mating_population)), 2)
    if random.randint(0, 1) is 1:
        parent1_genes = mating_population[parent_idxs[0]].Genes[:]
        child1_genes = parent1_genes
        parent2_genes = mating_population[parent_idxs[1]].Genes[:]
        child2_genes = parent2_genes
        gene_idx = random.randint(0, len(parent1_genes) - 1)
        child1_genes[gene_idx], child2_genes[gene_idx] = parent2_genes[gene_idx], parent1_genes[gene_idx]
        child1_start_date, child1_end_date = generate_random_dates()
        child2_start_date, child2_end_date = generate_random_dates()
        offspring_population = [Chromosome(child1_genes, child1_start_date, child1_end_date),
                                Chromosome(child2_genes, child2_start_date, child2_end_date)]
    else:
        offspring_population = None
    return offspring_population


def mutate(offspring_population, verbose=False):
    """
    The mutate operator takes in the genes of one offspring
    and randomly replaces one of the genes from the set of choices.

    :param offspring_population: list of Chromosome instances
        population of individuals created from the genes of mating population.
    :return: offspring_population: list of Chromosome instances
        mutated offspring population.

    """
    for child in offspring_population:
        if random.randint(1, len(offspring_population)) is 1:
            new_child = generate_genes()
            gene_idx = random.randint(0, len(new_child) - 1)
            if verbose:
                print('--> Mutating gene in position {} in child {}.'.format(gene_idx, child.Genes))
            child.Genes[gene_idx] = new_child[gene_idx]
    return offspring_population


def get_best(population, verbose=False):
    """
    Finds the location of the individual within the population with the best (lowest) fitness.

    :param population: list of Chromosome instances
    :return: best_individual: single Chromosome instance
        individual within a population with the lowest fitness.

    """
    fitness = [population[i].Fitness for i in range(0, len(population))]
    if verbose:
        print('The tournament fitness values are: {}'.format(fitness))
    best_fitness = min(fitness)
    best_index = fitness.index(best_fitness)
    best_individual = population[best_index]
    return best_individual


def find_elites(population, n_elites, fn_display_pop, verbose=False):
    """
    Finds elites within the population by sorting the members of the population from
    best (numerically lowest) to worst (numerically highest) fitness value,
    and returns a list (with the nuber of individuals specified by the user)
    containing the individuals with the best fitness.

    :param population: list of Chromosome instances
    :param n_elites: integer
        specifying the number of individuals you want to keep from the population.
    :param fn_display_pop: function
        for printing information about the population to the screen.
    :return: elites: list of Chromosome instances
        specifying the elite individuals extracted from the population.

    """
    order = sorted(population, key=lambda x: x.Fitness)
    elites = order[0:n_elites]
    if verbose:
        print('The elites moving to the next generation are: ')
        fn_display_pop(elites)
    return elites
