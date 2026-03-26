"""
Transportation Problem -- Genetic Algorithm.

Encoding : flat vector of length m*n (continuous allocation matrix).
Repair   : Sinkhorn-style iterative row/column normalization to restore
           supply and demand feasibility.
Seeding  : initial population uses Northwest Corner as one individual.

Run::

    python ga.py ../instances/small_3x4.json
"""
from __future__ import annotations
import json
import random
import sys
from typing import List


def total_cost(x: List[List[float]], costs: List[List[float]]) -> float:
    return sum(
        costs[i][j] * x[i][j]
        for i in range(len(x))
        for j in range(len(x[0]))
    )


def repair(
    flat: List[float],
    supply: List[float],
    demand: List[float],
    max_iter: int = 50,
) -> List[List[float]]:
    """Iterative row/column scaling (Sinkhorn) until feasibility is met."""
    m, n = len(supply), len(demand)
    x = [[max(flat[i * n + j], 0.0) for j in range(n)] for i in range(m)]
    for _ in range(max_iter):
        # Scale rows to satisfy supply
        for i in range(m):
            row_sum = sum(x[i])
            if row_sum > 1e-9:
                scale = min(supply[i], row_sum) / row_sum
                x[i] = [v * scale for v in x[i]]
        # Scale columns to satisfy demand
        for j in range(n):
            col_sum = sum(x[i][j] for i in range(m))
            if col_sum > 1e-9 and col_sum < demand[j]:
                scale = demand[j] / col_sum
                for i in range(m):
                    x[i][j] *= scale
    return x


def nw_individual(supply: List[float], demand: List[float]) -> List[float]:
    """Northwest corner individual (flat vector)."""
    m, n = len(supply), len(demand)
    s, d = supply[:], demand[:]
    flat = [0.0] * (m * n)
    i = j = 0
    while i < m and j < n:
        v = min(s[i], d[j])
        flat[i * n + j] = v
        s[i] -= v
        d[j] -= v
        if s[i] == 0:
            i += 1
        else:
            j += 1
    return flat


def random_individual(supply: List[float], demand: List[float]) -> List[float]:
    m, n = len(supply), len(demand)
    flat = [random.uniform(0, 1) for _ in range(m * n)]
    x = repair(flat, supply, demand)
    return [x[i][j] for i in range(m) for j in range(n)]


def fitness(flat: List[float], supply: List[float], demand: List[float], costs: List[List[float]]) -> float:
    n = len(demand)
    m = len(supply)
    x = [[flat[i * n + j] for j in range(n)] for i in range(m)]
    return total_cost(x, costs)


def crossover(p1: List[float], p2: List[float]) -> List[float]:
    cut = random.randint(1, len(p1) - 1)
    return p1[:cut] + p2[cut:]


def mutate(flat: List[float], rate: float = 0.05) -> List[float]:
    return [v + random.gauss(0, 0.5) if random.random() < rate else v for v in flat]


def genetic(
    supply: List[float],
    demand: List[float],
    costs: List[List[float]],
    pop_size: int = 40,
    n_generations: int = 200,
    mutation_rate: float = 0.05,
) -> dict:
    m, n = len(supply), len(demand)

    # Initialise population
    population = [nw_individual(supply, demand)] + [
        random_individual(supply, demand) for _ in range(pop_size - 1)
    ]
    population = [repair(ind, supply, demand) for ind in [
        [row[j] for row in ind_m for j in range(len(ind_m[0]))]
        if isinstance(ind_m[0], list) else ind_m
        for ind_m in population
    ]]
    # Flatten if needed
    population_flat = []
    for ind in population:
        if isinstance(ind[0], list):
            population_flat.append([ind[i][j] for i in range(m) for j in range(n)])
        else:
            population_flat.append(ind)
    population = population_flat

    def get_cost(ind):
        return fitness(ind, supply, demand, costs)

    best = min(population, key=get_cost)
    best_cost = get_cost(best)

    for _ in range(n_generations):
        population.sort(key=get_cost)
        elites = population[: max(1, pop_size // 5)]
        new_pop = elites[:]
        while len(new_pop) < pop_size:
            p1, p2 = random.choices(elites, k=2)
            child = crossover(p1, p2)
            child = mutate(child, mutation_rate)
            x = repair(child, supply, demand)
            child = [x[i][j] for i in range(m) for j in range(n)]
            new_pop.append(child)
        population = new_pop

        candidate = min(population, key=get_cost)
        c = get_cost(candidate)
        if c < best_cost:
            best_cost = c
            best = candidate[:]

    x_best = repair(best, supply, demand)
    return {"total_cost": total_cost(x_best, costs), "plan": x_best}


def _main(path: str) -> None:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    supply = [s["supply"] for s in data["suppliers"]]
    demand = [c["demand"] for c in data["customers"]]
    costs = data["costs"]
    result = genetic(supply, demand, costs)
    print(f"GA total cost : {result['total_cost']:.2f}")
    for row in result["plan"]:
        print(" ".join(f"{v:7.2f}" for v in row))


if __name__ == "__main__":
    _main(sys.argv[1] if len(sys.argv) > 1 else "../instances/small_3x4.json")
