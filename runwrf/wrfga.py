import random
import time
import statistics
import sys
from bisect import bisect_left
from math import exp


# Define a Chromosome class the provides information about each unique individual
class Chromosome:
    def __init__(self, genes, fitness=10**6):
        self.Genes = genes
        self.Fitness = fitness
        self.Age = 0


# This function provides a way to generate a random string from the set of genes
def generate_parent(length, gene_set):
    genes = []
    while len(genes) < length:
        sample_size = min(length - len(genes), len(gene_set))
        genes.extend(random.sample(gene_set, sample_size))
    return Chromosome(genes)


def crossover(parent_genes, index, parents, get_fitness, crossover, mutate, generate_parent):
    donor_index = random.randrange(0, len(parents))
    if donor_index == index:
        donor_index = (donor_index + 1) % len(parents)
    child_genes = crossover(parent_genes, parents[donor_index].Genes)
    if child_genes is None:
        # parent and donor are indistinguishable
        parents[donor_index] = generate_parent()
        return mutate(parents[index])
    fitness = get_fitness(child_genes)
    return Chromosome(child_genes, fitness)


# A new Chromosome/individual can be created by mutating the current individual
def mutate(parent, gene_set):
    # Set the child genes to that of the parent
    child_genes = parent.Genes[:]
    # Randomly select a gene from the child to mutate
    index = random.randrange(0, child_genes)
    new_gene, alternate = random.sample(gene_set, 2)
    child_genes[index] = alternate \
        if new_gene == child_genes[index] \
        else new_gene
    return Chromosome(child_genes)


# Function that finds the best individual within the population
def get_best(get_fitness, target_len, optimal_fitness, gene_set,
             display, max_age=None, pool_size=1, crossover=None, max_seconds=None):

    random.seed()

    def fn_mutate(parent):
        return mutate(parent, gene_set)

    def fn_generate_parent():
        return generate_parent(target_len, gene_set)

    if crossover is not None:

        def fn_new_child(parent, index, parents):
            return random.choice(used_strategies)(parent, index, parents)
    else:
        def fn_new_child(parent, index, parents):
            return fn_mutate(parent)

    for timed_out, improvement in get_improvement(fn_new_child, fn_generate_parent, max_age, pool_size, max_seconds):
        if timed_out:
            return improvement
        display(improvement)
        if not optimal_fitness > improvement.Fitness:
            return improvement


def get_improvement(new_child, generate_parent, max_age, pool_size, max_seconds):
    # Start a timer for time_out purposes
    start_time = time.time()
    # Initialize parents with the best parent
    best_parent = generate_parent()
    yield max_seconds is not None and time.time() - start_time > max_seconds, best_parent
    parents = [best_parent]
    historical_fitness = [best_parent.Fitness]
    # Populate the parents array by generating new random parents
    for _ in range(pool_size - 1):
        parent = generate_parent()
        if max_seconds is not None and time.time() - start_time > max_seconds:
            yield True, parent
        if parent.Fitness > best_parent.Fitness:
            yield False, parent
            best_parent = parent
            historical_fitness.append(parent.Fitness)
        parents.append(parent)
    # Since we have an array of parents, each time through the loop we select a different one to be the current parent
    last_parent_index = pool_size - 1
    pindex = 1
    while True:
        if max_seconds is not None and time.time() - start_time > max_seconds:
            yield True, best_parent
        pindex = pindex - 1 if pindex > 0 else last_parent_index
        parent = parents[pindex]
        child = new_child(parent, pindex, parents)
        if parent.Fitness > child.Fitness:
            if max_age is None:
                continue
            parent.Age += 1
            if max_age > parent.Age:
                continue
            index = bisect_left(historical_fitness, child.Fitness, 0, len(historical_fitness))
            proportion_similar = index / len(historical_fitness)
            if random.random() < exp(-proportion_similar):
                parents[pindex] = child
                continue
            best_parent.Age = 0
            parents[pindex] = best_parent
            continue
        if not child.Fitness > parent.Fitness:
            # same fitness
            child.Age = parent.Age + 1
            parents[pindex] = child
            continue
        child.Age = 0
        parents[pindex] = child
        if child.Fitness > best_parent.Fitness:
            best_parent = child
            yield False, best_parent
            historical_fitness.append(best_parent.Fitness)


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

