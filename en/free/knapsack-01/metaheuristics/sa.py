"""0/1 Knapsack -- Simulated Annealing (SA).

Solution representation:
    Binary vector x where x[i] in {0,1} indicates whether item i is selected.

Perturbation:
    - Random flip: toggle one item bit (insert or remove).
    - If the knapsack becomes overloaded, remove items with the lowest
      profit/weight ratio until feasibility is restored.

Dependencies: none (stdlib only)

References:
    Kirkpatrick, S., Gelatt, C. D., Vecchi, M. P. (1983). Optimization by
    Simulated Annealing. Science, 220(4598), 671-680.
"""

from __future__ import annotations

import json
import math
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
    """Remove items with lowest profit/weight ratio until feasible."""
    x = x[:]
    order = sorted(range(len(x)), key=lambda i: profits[i] / max(weights[i], 1e-9))
    for i in order:
        if total_weight(x, weights) <= C:
            break
        if x[i] == 1:
            x[i] = 0
    return x


def perturb(x: list[int], weights: list[float], profits: list[float], C: float) -> list[int]:
    """Flip a random bit and repair if necessary."""
    new_x = x[:]
    idx = random.randrange(len(new_x))
    new_x[idx] = 1 - new_x[idx]
    if total_weight(new_x, weights) > C:
        new_x = repair(new_x, weights, profits, C)
    return new_x


def simulated_annealing(
    C: float,
    weights: list[float],
    profits: list[float],
    T0: float = 10.0,
    alpha: float = 0.99,
    iters_per_temp: int = 100,
    stops: int = 300,
) -> tuple[list[int], float]:
    """Run SA for 0/1 Knapsack.

    Args:
        C: Knapsack capacity.
        weights: List of item weights.
        profits: List of item profits.
        T0: Initial temperature.
        alpha: Cooling rate.
        iters_per_temp: Iterations per temperature level.
        stops: Number of temperature reductions.

    Returns:
        (best_solution, best_profit)
    """
    n = len(weights)
    # Greedy initialization: items sorted by profit/weight ratio
    order = sorted(range(n), key=lambda i: profits[i] / max(weights[i], 1e-9), reverse=True)
    current = [0] * n
    cap_left = C
    for i in order:
        if weights[i] <= cap_left:
            current[i] = 1
            cap_left -= weights[i]

    best = current[:]
    best_profit = total_profit(best, profits)
    T = T0

    for _ in range(stops):
        for _ in range(iters_per_temp):
            neighbor = perturb(current, weights, profits, C)
            delta = total_profit(neighbor, profits) - total_profit(current, profits)
            if delta > 0 or random.random() < math.exp(delta / max(T, 1e-10)):
                current = neighbor
                if total_profit(current, profits) > best_profit:
                    best = current[:]
                    best_profit = total_profit(best, profits)
        T *= alpha

    return best, best_profit


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "../instances/small_5.json"
    data = load(path)
    C = data["capacity"]
    weights = [it["weight"] for it in data["items"]]
    profits = [it["profit"] for it in data["items"]]
    ids = [it["id"] for it in data["items"]]

    random.seed(42)
    solution, profit = simulated_annealing(C, weights, profits)
    selected = [ids[i] for i, xi in enumerate(solution) if xi == 1]
    print(f"SA -- Profit: {profit:.0f} | Items: {selected}")
