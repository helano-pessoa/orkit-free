"""0/1 Knapsack -- GRASP (Greedy Randomized Adaptive Search Procedure).

Construction phase:
    Adds items in decreasing order of profit/weight ratio, with randomness
    controlled by alpha (0=greedy, 1=fully random).

Local search phase:
    Tries item swaps to improve the total profit.

Dependencies: none (stdlib only)

References:
    Feo, T. A., Resende, M. G. C. (1995). Greedy Randomized Adaptive Search
    Procedures. Journal of Global Optimization, 6(2), 109-133.
"""

from __future__ import annotations

import json
import random
import sys
from copy import deepcopy


def load(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def total_profit(x: list[int], profits: list[float]) -> float:
    return sum(p * xi for p, xi in zip(profits, x))


def total_weight(x: list[int], weights: list[float]) -> float:
    return sum(w * xi for w, xi in zip(weights, x))


def construction(C: float, weights: list[float], profits: list[float], alpha: float = 0.3) -> list[int]:
    """Construction phase: randomized greedy by profit/weight ratio."""
    n = len(weights)
    x = [0] * n
    remaining = C
    unselected = list(range(n))

    while unselected:
        candidates = [i for i in unselected if weights[i] <= remaining]
        if not candidates:
            break

        ratios = [profits[i] / max(weights[i], 1e-9) for i in candidates]
        r_min, r_max = min(ratios), max(ratios)
        limit = r_max - alpha * (r_max - r_min)
        rcl = [candidates[j] for j, r in enumerate(ratios) if r >= limit]

        chosen = random.choice(rcl)
        x[chosen] = 1
        remaining -= weights[chosen]
        unselected.remove(chosen)

    return x


def local_search(x: list[int], C: float, weights: list[float], profits: list[float]) -> list[int]:
    """Swap a selected item for an unselected one if it improves profit."""
    improved = True
    while improved:
        improved = False
        selected = [i for i, xi in enumerate(x) if xi == 1]
        not_selected = [i for i, xi in enumerate(x) if xi == 0]
        for i in selected:
            for j in not_selected:
                new_x = x[:]
                new_x[i] = 0
                new_x[j] = 1
                if total_weight(new_x, weights) <= C and total_profit(new_x, profits) > total_profit(x, profits):
                    x = new_x
                    improved = True
                    break
            if improved:
                break
    return x


def grasp(
    C: float,
    weights: list[float],
    profits: list[float],
    n_iter: int = 50,
    alpha: float = 0.3,
) -> tuple[list[int], float]:
    """Run GRASP for 0/1 Knapsack.

    Returns:
        (best_solution, best_profit)
    """
    best = None
    best_profit = -1.0

    for _ in range(n_iter):
        sol = construction(C, weights, profits, alpha)
        sol = local_search(sol, C, weights, profits)
        p = total_profit(sol, profits)
        if p > best_profit:
            best = sol[:]
            best_profit = p

    return best, best_profit


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "../instances/small_5.json"
    data = load(path)
    C = data["capacity"]
    weights = [it["weight"] for it in data["items"]]
    profits = [it["profit"] for it in data["items"]]
    ids = [it["id"] for it in data["items"]]

    random.seed(42)
    solution, profit = grasp(C, weights, profits)
    selected = [ids[i] for i, xi in enumerate(solution) if xi == 1]
    print(f"GRASP -- Profit: {profit:.0f} | Items: {selected}")
