"""1D Cutting Stock -- Simulated Annealing (SA).

Solution representation:
    List of rolls, each roll as a dict {item_id: quantity}.
    Initialization: First-Fit Decreasing (FFD).

Perturbation:
    - Move one unit of a random item from one roll to another (or a new roll).
    - Try to consolidate almost-empty rolls.

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
from copy import deepcopy
from pathlib import Path


# ---------------------------------------------------------------------------
# Lightweight data loading (no dependency on instance.py)
# ---------------------------------------------------------------------------

def load(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# Initial solution: First-Fit Decreasing
# ---------------------------------------------------------------------------

def ffd_initial(W: float, widths: dict, demands: dict) -> list[dict]:
    """Build initial solution via First-Fit Decreasing."""
    sorted_items = sorted(widths.keys(), key=lambda i: widths[i], reverse=True)
    rolls: list[dict] = []
    free_space: list[float] = []

    for i in sorted_items:
        for _ in range(demands[i]):
            placed = False
            for idx, space in enumerate(free_space):
                if space >= widths[i]:
                    rolls[idx][i] = rolls[idx].get(i, 0) + 1
                    free_space[idx] -= widths[i]
                    placed = True
                    break
            if not placed:
                rolls.append({i: 1})
                free_space.append(W - widths[i])

    return rolls


def cost(rolls: list[dict]) -> int:
    """Number of rolls used (objective function)."""
    return len(rolls)


def feasible(rolls: list[dict], W: float, widths: dict, demands: dict) -> bool:
    """Check feasibility: demand and capacity."""
    for roll in rolls:
        if sum(widths[i] * q for i, q in roll.items()) > W + 1e-9:
            return False
    count = {}
    for roll in rolls:
        for i, q in roll.items():
            count[i] = count.get(i, 0) + q
    return all(count.get(i, 0) >= demands[i] for i in demands)


# ---------------------------------------------------------------------------
# Perturbation
# ---------------------------------------------------------------------------

def perturb(rolls: list[dict], W: float, widths: dict) -> list[dict]:
    """Generate neighbor: move 1 unit of an item between rolls."""
    new_rolls = deepcopy(rolls)
    if len(new_rolls) == 0:
        return new_rolls

    attempts = 0
    while attempts < 20:
        attempts += 1
        src = random.randrange(len(new_rolls))
        if not new_rolls[src]:
            continue
        item = random.choice(list(new_rolls[src].keys()))

        # Remove from source
        new_rolls[src][item] -= 1
        if new_rolls[src][item] == 0:
            del new_rolls[src][item]

        # Try to place in another existing roll
        destinations = [j for j in range(len(new_rolls)) if j != src]
        random.shuffle(destinations)
        placed = False
        for dst in destinations:
            free = W - sum(widths[i] * q for i, q in new_rolls[dst].items())
            if free >= widths[item]:
                new_rolls[dst][item] = new_rolls[dst].get(item, 0) + 1
                placed = True
                break

        if not placed:
            # Open a new roll
            new_rolls.append({item: 1})

        # Remove empty rolls
        new_rolls = [r for r in new_rolls if r]
        return new_rolls

    return rolls


# ---------------------------------------------------------------------------
# Simulated Annealing
# ---------------------------------------------------------------------------

def simulated_annealing(
    W: float,
    widths: dict,
    demands: dict,
    T0: float = 10.0,
    alpha: float = 0.995,
    iters_per_temp: int = 100,
    stops: int = 500,
) -> tuple[list[dict], int]:
    """Run SA for 1D Cutting Stock.

    Args:
        W: Master roll width.
        widths: {item_id: width}.
        demands: {item_id: demand}.
        T0: Initial temperature.
        alpha: Cooling rate.
        iters_per_temp: Iterations per temperature level.
        stops: Number of temperature reductions.

    Returns:
        (best_solution, best_cost)
    """
    current = ffd_initial(W, widths, demands)
    best = deepcopy(current)
    best_cost = cost(best)
    T = T0

    for _ in range(stops):
        for _ in range(iters_per_temp):
            neighbor = perturb(current, W, widths)
            if not feasible(neighbor, W, widths, demands):
                continue
            delta = cost(neighbor) - cost(current)
            if delta < 0 or random.random() < math.exp(-delta / max(T, 1e-10)):
                current = neighbor
                if cost(current) < best_cost:
                    best = deepcopy(current)
                    best_cost = cost(best)
        T *= alpha

    return best, best_cost


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
    solution, n_rolls = simulated_annealing(W, widths, demands)
    print(f"SA -- Rolls used: {n_rolls}")
    for idx, roll in enumerate(solution, 1):
        print(f"  Roll {idx}: {roll}")
