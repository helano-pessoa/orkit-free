"""
Transportation Problem -- Simulated Annealing.

Initialization : Northwest Corner Method (NW).
Perturbation   : Square loop — choose 4 cells (i1,j1),(i1,j2),(i2,j2),(i2,j1)
                 and shift a delta unit cyclically while keeping feasibility.

Run::

    python sa.py ../instances/small_3x4.json
"""
from __future__ import annotations
import json
import math
import random
import sys
from typing import List


# ------------------------------------------------------------------
# Cost evaluation
# ------------------------------------------------------------------
def total_cost(x: List[List[float]], costs: List[List[float]]) -> float:
    return sum(
        costs[i][j] * x[i][j]
        for i in range(len(x))
        for j in range(len(x[0]))
    )


# ------------------------------------------------------------------
# Northwest Corner initialisation
# ------------------------------------------------------------------
def init_nw(supply: List[float], demand: List[float]) -> List[List[float]]:
    m, n = len(supply), len(demand)
    s, d = supply[:], demand[:]
    x = [[0.0] * n for _ in range(m)]
    i = j = 0
    while i < m and j < n:
        v = min(s[i], d[j])
        x[i][j] = v
        s[i] -= v
        d[j] -= v
        if s[i] == 0:
            i += 1
        else:
            j += 1
    return x


# ------------------------------------------------------------------
# Square loop perturbation
# ------------------------------------------------------------------
def perturb(
    x: List[List[float]],
    supply: List[float],
    demand: List[float],
    costs: List[List[float]],
) -> List[List[float]]:
    m, n = len(x), len(x[0])
    best = x
    best_cost = total_cost(x, costs)

    for _ in range(20):
        i1, i2 = random.sample(range(m), 2)
        j1, j2 = random.sample(range(n), 2)
        # Maximum feasible shift
        max_delta = min(x[i1][j1], x[i2][j2])
        if max_delta <= 0:
            continue
        delta = random.uniform(0, max_delta)
        nx = [row[:] for row in x]
        nx[i1][j1] -= delta
        nx[i1][j2] += delta
        nx[i2][j2] -= delta
        nx[i2][j1] += delta
        nc = total_cost(nx, costs)
        if nc < best_cost:
            best, best_cost = nx, nc

    return best if best is not x else [row[:] for row in x]


def perturb_random(x: List[List[float]]) -> List[List[float]]:
    """Return a random square-loop neighbour (may be worse)."""
    m, n = len(x), len(x[0])
    nx = [row[:] for row in x]
    for _ in range(100):
        i1, i2 = random.sample(range(m), 2)
        j1, j2 = random.sample(range(n), 2)
        max_delta = min(nx[i1][j1], nx[i2][j2])
        if max_delta <= 0:
            continue
        delta = random.uniform(0, max_delta)
        nx[i1][j1] -= delta
        nx[i1][j2] += delta
        nx[i2][j2] -= delta
        nx[i2][j1] += delta
        return nx
    return nx


# ------------------------------------------------------------------
# Simulated Annealing
# ------------------------------------------------------------------
def simulated_annealing(
    supply: List[float],
    demand: List[float],
    costs: List[List[float]],
    T0: float = 1000.0,
    alpha: float = 0.98,
    iters_per_temp: int = 200,
    stops: int = 80,
) -> dict:
    x = init_nw(supply, demand)
    best = [row[:] for row in x]
    best_cost = total_cost(x, costs)
    T = T0

    for _ in range(stops):
        for _ in range(iters_per_temp):
            nx = perturb_random(x)
            delta = total_cost(nx, costs) - total_cost(x, costs)
            if delta < 0 or random.random() < math.exp(-delta / max(T, 1e-10)):
                x = nx
            c = total_cost(x, costs)
            if c < best_cost:
                best, best_cost = [row[:] for row in x], c
        T *= alpha

    return {"total_cost": best_cost, "plan": best}


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------
def _main(path: str) -> None:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    supply = [s["supply"] for s in data["suppliers"]]
    demand = [c["demand"] for c in data["customers"]]
    costs = data["costs"]
    result = simulated_annealing(supply, demand, costs)
    print(f"SA total cost : {result['total_cost']:.2f}")
    for row in result["plan"]:
        print(" ".join(f"{v:7.2f}" for v in row))


if __name__ == "__main__":
    _main(sys.argv[1] if len(sys.argv) > 1 else "../instances/small_3x4.json")
