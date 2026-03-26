"""1D Cutting Stock -- GRASP (Greedy Randomized Adaptive Search Procedure).

Construction phase:
    Randomized greedy: adds items in decreasing order of width,
    with randomness controlled by the alpha parameter (0=greedy, 1=random).

Local search phase:
    Tries to move items between rolls to reduce the number of rolls used.

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
from pathlib import Path


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def load(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def cost(rolls: list[dict]) -> int:
    return len(rolls)


def free_space(roll: dict, W: float, widths: dict) -> float:
    return W - sum(widths[i] * q for i, q in roll.items())


# ---------------------------------------------------------------------------
# GRASP construction
# ---------------------------------------------------------------------------

def construction(W: float, widths: dict, demands: dict, alpha: float = 0.3) -> list[dict]:
    """Construction phase: randomized greedy.

    Args:
        W: Master roll width.
        widths: {item_id: width}.
        demands: {item_id: demand}.
        alpha: Randomness level (0=greedy, 1=fully random).

    Returns:
        Constructed solution (list of rolls).
    """
    # Build list of items to place (item_id repeated by demand)
    pending = []
    for i, d in demands.items():
        pending.extend([i] * d)

    # Sort decreasingly by width
    pending.sort(key=lambda i: widths[i], reverse=True)

    rolls: list[dict] = []
    spaces: list[float] = []

    while pending:
        item = pending.pop(0)

        # Candidates: rolls with enough free space
        candidates = [
            idx for idx, sp in enumerate(spaces) if sp >= widths[item]
        ]

        if candidates:
            # Restricted Candidate List: best options (least remaining space after insertion)
            sorted_cands = sorted(
                candidates,
                key=lambda idx: spaces[idx] - widths[item],
            )
            min_sp = spaces[sorted_cands[0]] - widths[item]
            max_sp = spaces[sorted_cands[-1]] - widths[item]
            limit = min_sp + alpha * (max_sp - min_sp)
            rcl = [idx for idx in candidates if (spaces[idx] - widths[item]) <= limit]
            dest = random.choice(rcl) if rcl else candidates[0]

            rolls[dest][item] = rolls[dest].get(item, 0) + 1
            spaces[dest] -= widths[item]
        else:
            rolls.append({item: 1})
            spaces.append(W - widths[item])

    return rolls


# ---------------------------------------------------------------------------
# Local search
# ---------------------------------------------------------------------------

def local_search(rolls: list[dict], W: float, widths: dict) -> list[dict]:
    """Try to reduce number of rolls by moving items from near-empty rolls."""
    improved = True
    while improved:
        improved = False
        rolls = [r for r in rolls if r]  # remove empty rolls
        # Sort rolls by load ascending (target candidates first)
        order = sorted(range(len(rolls)), key=lambda j: sum(widths[i]*q for i,q in rolls[j].items()))
        for src in order:
            src_roll = rolls[src]
            if not src_roll:
                continue
            # Try to move all items from src to other rolls
            temp = deepcopy(rolls)
            items_src = [(i, q) for i, q in src_roll.items() for _ in range(q)]
            temp[src] = {}
            for item, _ in items_src:
                placed = False
                for dst in range(len(temp)):
                    if dst == src:
                        continue
                    sp = W - sum(widths[i]*q for i,q in temp[dst].items())
                    if sp >= widths[item]:
                        temp[dst][item] = temp[dst].get(item, 0) + 1
                        placed = True
                        break
                if not placed:
                    break  # could not empty src roll
            else:
                # Success: removed src roll
                temp = [r for r in temp if r]
                if len(temp) < len([r for r in rolls if r]):
                    rolls = temp
                    improved = True
                    break
    return [r for r in rolls if r]


# ---------------------------------------------------------------------------
# GRASP
# ---------------------------------------------------------------------------

def grasp(
    W: float,
    widths: dict,
    demands: dict,
    n_iter: int = 50,
    alpha: float = 0.3,
) -> tuple[list[dict], int]:
    """Run GRASP for 1D Cutting Stock.

    Args:
        W: Master roll width.
        widths: {item_id: width}.
        demands: {item_id: demand}.
        n_iter: Number of GRASP iterations.
        alpha: Randomness level in construction.

    Returns:
        (best_solution, best_cost)
    """
    best = None
    best_cost = float("inf")

    for _ in range(n_iter):
        sol = construction(W, widths, demands, alpha)
        sol = local_search(sol, W, widths)
        c = cost(sol)
        if c < best_cost:
            best = deepcopy(sol)
            best_cost = c

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
    solution, n_rolls = grasp(W, widths, demands)
    print(f"GRASP -- Rolls used: {n_rolls}")
    for idx, roll in enumerate(solution, 1):
        print(f"  Roll {idx}: {roll}")
