"""0/1 Knapsack -- Genetic Algorithm (GA).

Chromosome representation:
    Binary vector of length n_items.
    chromosome[i] in {0,1}.

Operators:
    Selection: binary tournament
    Crossover: single-point
    Mutation: bit flip (with capacity repair)

Dependencies: none (stdlib only)

References:
    Holland, J. H. (1975). Adaptation in Natural and Artificial Systems. MIT Press.
"""

from __future__ import annotations

import json
import random
import sys


def load(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def total_profit(x: list[int], profits: list[float]) -> float:
    return sum(p * xi for p, xi in zip(profits, x))


def total_weight(x: list[int], weights: list[float]) -> float:
    return sum(w * xi for w, xi in zip(weights, x))


def repair(x: list[int], weights: list[float], profits: list[float], C: float) -> list[int]:
    x = x[:]
    order = sorted(range(len(x)), key=lambda i: profits[i] / max(weights[i], 1e-9))
    for i in order:
        if total_weight(x, weights) <= C:
            break
        if x[i] == 1:
            x[i] = 0
    return x


def fitness(x: list[int], weights: list[float], profits: list[float], C: float) -> float:
    weight = total_weight(x, weights)
    if weight > C:
        return total_profit(x, profits) - 1000.0 * (weight - C)
    return total_profit(x, profits)


def tournament(pop: list[list[int]], fits: list[float], k: int = 2) -> list[int]:
    competitors = random.sample(range(len(pop)), k)
    winner = max(competitors, key=lambda j: fits[j])
    return pop[winner][:]


def crossover(p1: list[int], p2: list[int]) -> tuple[list[int], list[int]]:
    n = len(p1)
    pt = random.randint(1, n - 1)
    return p1[:pt] + p2[pt:], p2[:pt] + p1[pt:]


def mutate(x: list[int], rate: float = 0.05) -> list[int]:
    return [1 - xi if random.random() < rate else xi for xi in x]


def genetic(
    C: float,
    weights: list[float],
    profits: list[float],
    pop_size: int = 50,
    n_generations: int = 200,
    mutation_rate: float = 0.05,
) -> tuple[list[int], float]:
    """Run GA for 0/1 Knapsack.

    Returns:
        (best_solution, best_profit)
    """
    n = len(weights)

    def greedy_individual():
        order = sorted(range(n), key=lambda i: profits[i] / max(weights[i], 1e-9), reverse=True)
        x = [0] * n
        cap = C
        for i in order:
            if weights[i] <= cap:
                x[i] = 1
                cap -= weights[i]
        return x

    pop = [greedy_individual()]
    while len(pop) < pop_size:
        pop.append([random.randint(0, 1) for _ in range(n)])

    best = None
    best_profit_val = -float("inf")

    for _ in range(n_generations):
        pop = [repair(c, weights, profits, C) for c in pop]
        fits = [fitness(c, weights, profits, C) for c in pop]

        idx_best = max(range(len(pop)), key=lambda j: fits[j])
        if fits[idx_best] > best_profit_val:
            best_profit_val = fits[idx_best]
            best = pop[idx_best][:]

        new_pop = [best[:]]  # elitism
        while len(new_pop) < pop_size:
            p1 = tournament(pop, fits)
            p2 = tournament(pop, fits)
            c1, c2 = crossover(p1, p2)
            new_pop.append(mutate(c1, mutation_rate))
            if len(new_pop) < pop_size:
                new_pop.append(mutate(c2, mutation_rate))
        pop = new_pop

    return best, total_profit(best, profits)


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "../instances/small_5.json"
    data = load(path)
    C = data["capacity"]
    weights = [it["weight"] for it in data["items"]]
    profits = [it["profit"] for it in data["items"]]
    ids = [it["id"] for it in data["items"]]

    random.seed(42)
    solution, profit = genetic(C, weights, profits)
    selected = [ids[i] for i, xi in enumerate(solution) if xi == 1]
    print(f"GA -- Profit: {profit:.0f} | Items: {selected}")
