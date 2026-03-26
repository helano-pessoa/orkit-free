"""
Transportation Problem -- GRASP (Greedy Randomized Adaptive Search Procedure).

Construction : build an allocation using a Restricted Candidate List (RCL)
               based on minimum cost, controlled by parameter alpha in [0,1].
Local search : flow reallocation -- shift flow along the 4 corners of a square
               whenever it reduces total cost.

Run::

    python grasp.py ../instances/small_3x4.json
"""
from __future__ import annotations
import json
import random
import sys
from typing import List, Tuple


def total_cost(x: List[List[float]], costs: List[List[float]]) -> float:
    return sum(
        costs[i][j] * x[i][j]
        for i in range(len(x))
        for j in range(len(x[0]))
    )


def construction(
    supply: List[float],
    demand: List[float],
    costs: List[List[float]],
    alpha: float,
) -> List[List[float]]:
    """Build a feasible solution using RCL based on minimum unit cost."""
    m, n = len(supply), len(demand)
    s, d = supply[:], demand[:]
    x = [[0.0] * n for _ in range(m)]

    while True:
        # Candidates: (i, j) pairs with remaining supply and demand
        candidates: List[Tuple[int, int, float]] = [
            (i, j, costs[i][j])
            for i in range(m)
            for j in range(n)
            if s[i] > 0 and d[j] > 0
        ]
        if not candidates:
            break
        c_min = min(c for _, _, c in candidates)
        c_max = max(c for _, _, c in candidates)
        threshold = c_min + alpha * (c_max - c_min)
        rcl = [(i, j) for i, j, c in candidates if c <= threshold]
        i, j = random.choice(rcl)
        v = min(s[i], d[j])
        x[i][j] += v
        s[i] -= v
        d[j] -= v

    return x


def local_search(
    x: List[List[float]],
    costs: List[List[float]],
    max_iter: int = 500,
) -> List[List[float]]:
    """Square loop flow reallocation: try all 4-corner shifts."""
    m, n = len(x), len(x[0])
    improved = True
    iterations = 0
    while improved and iterations < max_iter:
        improved = False
        iterations += 1
        for i1 in range(m):
            for i2 in range(i1 + 1, m):
                for j1 in range(n):
                    for j2 in range(j1 + 1, n):
                        # Shift delta from (i1,j1) and (i2,j2) to (i1,j2) and (i2,j1)
                        delta_cost = (
                            -costs[i1][j1]
                            + costs[i1][j2]
                            + costs[i2][j1]
                            - costs[i2][j2]
                        )
                        if delta_cost < 0:
                            shift = min(x[i1][j1], x[i2][j2])
                            if shift > 0:
                                x[i1][j1] -= shift
                                x[i1][j2] += shift
                                x[i2][j1] += shift
                                x[i2][j2] -= shift
                                improved = True
                        else:
                            delta_cost = -delta_cost
                            if delta_cost < 0:
                                shift = min(x[i1][j2], x[i2][j1])
                                if shift > 0:
                                    x[i1][j1] += shift
                                    x[i1][j2] -= shift
                                    x[i2][j1] -= shift
                                    x[i2][j2] += shift
                                    improved = True
    return x


def grasp(
    supply: List[float],
    demand: List[float],
    costs: List[List[float]],
    n_iter: int = 50,
    alpha: float = 0.3,
) -> dict:
    best_x = None
    best_cost = float("inf")

    for _ in range(n_iter):
        x = construction(supply, demand, costs, alpha)
        x = local_search(x, costs)
        c = total_cost(x, costs)
        if c < best_cost:
            best_cost = c
            best_x = [row[:] for row in x]

    return {"total_cost": best_cost, "plan": best_x}


def _main(path: str) -> None:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    supply = [s["supply"] for s in data["suppliers"]]
    demand = [c["demand"] for c in data["customers"]]
    costs = data["costs"]
    result = grasp(supply, demand, costs)
    print(f"GRASP total cost : {result['total_cost']:.2f}")
    for row in result["plan"]:
        print(" ".join(f"{v:7.2f}" for v in row))


if __name__ == "__main__":
    _main(sys.argv[1] if len(sys.argv) > 1 else "../instances/small_3x4.json")
