"""1D Cutting Stock -- Genetic Algorithm (GA).

Chromosome representation:
    List of length sum(demand), where chromosome[k] indicates
    which roll the k-th item unit (sorted order) was assigned to.

Operators:
    Selection: binary tournament
    Crossover: single-point
    Mutation: reassign a random item to a different roll

Dependencies: none (stdlib only)

References:
    Holland, J. H. (1975). Adaptation in Natural and Artificial Systems. MIT Press.
    Falkenauer, E. (1996). A hybrid grouping genetic algorithm for bin packing.
    Journal of Heuristics, 2(1), 5-30.
"""

from __future__ import annotations

import json
import random
import sys
from copy import deepcopy
from math import ceil


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def load(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def decode(chromosome: list[int], widths: dict, item_order: list[int]) -> list[dict]:
    """Convert chromosome to list of rolls.

    Args:
        chromosome: chromosome[k] = roll index for the k-th item unit.
        widths: {item_id: width}.
        item_order: sequence of item_ids (repeated by demand).

    Returns:
        List of rolls (dicts {item_id: qty}).
    """
    rolls: dict[int, dict] = {}
    for k, roll_id in enumerate(chromosome):
        i = item_order[k]
        if roll_id not in rolls:
            rolls[roll_id] = {}
        rolls[roll_id][i] = rolls[roll_id].get(i, 0) + 1
    return list(rolls.values())


def fitness(chromosome: list[int], widths: dict, item_order: list[int], W: float) -> float:
    """Compute fitness (lower = better). Penalizes capacity violations."""
    rolls_load: dict[int, float] = {}
    for k, roll_id in enumerate(chromosome):
        i = item_order[k]
        rolls_load[roll_id] = rolls_load.get(roll_id, 0.0) + widths[i]

    n_rolls = len(rolls_load)
    penalty = sum(max(0, load - W) for load in rolls_load.values()) * 1000.0
    return float(n_rolls) + penalty


def random_chromosome(n_items: int, max_rolls: int) -> list[int]:
    return [random.randint(0, max_rolls - 1) for _ in range(n_items)]


def ffd_chromosome(W: float, widths: dict, item_order: list[int]) -> list[int]:
    """FFD-based chromosome to seed the initial population."""
    rolls: list[float] = []
    assignment: list[int] = []
    for i in item_order:
        placed = False
        for j, load in enumerate(rolls):
            if load + widths[i] <= W:
                rolls[j] += widths[i]
                assignment.append(j)
                placed = True
                break
        if not placed:
            assignment.append(len(rolls))
            rolls.append(widths[i])
    return assignment


# ---------------------------------------------------------------------------
# Genetic operators
# ---------------------------------------------------------------------------

def tournament(pop: list[list[int]], fits: list[float], k: int = 2) -> list[int]:
    competitors = random.sample(range(len(pop)), k)
    winner = min(competitors, key=lambda j: fits[j])
    return pop[winner][:]


def crossover(parent1: list[int], parent2: list[int]) -> tuple[list[int], list[int]]:
    n = len(parent1)
    point = random.randint(1, n - 1)
    return parent1[:point] + parent2[point:], parent2[:point] + parent1[point:]


def mutate(chrom: list[int], max_rolls: int, rate: float = 0.05) -> list[int]:
    return [
        random.randint(0, max_rolls - 1) if random.random() < rate else g
        for g in chrom
    ]


# ---------------------------------------------------------------------------
# Genetic Algorithm
# ---------------------------------------------------------------------------

def genetic(
    W: float,
    widths: dict,
    demands: dict,
    pop_size: int = 50,
    n_generations: int = 200,
    mutation_rate: float = 0.05,
) -> tuple[list[dict], int]:
    """Run GA for 1D Cutting Stock.

    Returns:
        (best_decoded_solution, number_of_rolls)
    """
    # Build item sequence (repeated by demand, sorted desc by width)
    item_order = sorted(
        [i for i, d in demands.items() for _ in range(d)],
        key=lambda i: widths[i],
        reverse=True,
    )
    n_items = len(item_order)
    max_rolls = n_items  # trivial upper bound

    # Initial population: 50% FFD seeded + 50% random
    pop = [ffd_chromosome(W, widths, item_order)]
    while len(pop) < pop_size:
        pop.append(random_chromosome(n_items, max_rolls))

    best_chrom = None
    best_fit = float("inf")

    for _ in range(n_generations):
        fits = [fitness(c, widths, item_order, W) for c in pop]

        # Elitism: keep the best chromosome
        idx_best = min(range(len(pop)), key=lambda j: fits[j])
        if fits[idx_best] < best_fit:
            best_fit = fits[idx_best]
            best_chrom = pop[idx_best][:]

        # Generate new population
        new_pop = [best_chrom[:]]  # elitism
        while len(new_pop) < pop_size:
            p1 = tournament(pop, fits)
            p2 = tournament(pop, fits)
            c1, c2 = crossover(p1, p2)
            new_pop.append(mutate(c1, max_rolls, mutation_rate))
            if len(new_pop) < pop_size:
                new_pop.append(mutate(c2, max_rolls, mutation_rate))
        pop = new_pop

    rolls = decode(best_chrom, widths, item_order)
    return rolls, len(rolls)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "../instances/small_3.json"
    data = load(path)
    W = data["master_roll"]
    widths = {it["id"]: it["width"] for it in data["items"]}
    demands = {it["id"]: it["demand"] for it in data["items"]}

    random.seed(42)
    solution, n_rolls = genetic(W, widths, demands)
    print(f"GA -- Rolls used: {n_rolls}")
    for idx, roll in enumerate(solution, 1):
        print(f"  Roll {idx}: {roll}")
