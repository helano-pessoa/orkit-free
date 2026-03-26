"""1D Cutting Stock -- Compact MIP formulation with OR-Tools CP-SAT.

Formulation:
    min   sum_n  y_n
    s.t.  sum_n  x_{in}  >= d_i          for all i  (demand)
          sum_i  w_i * x_{in}  <= W*y_n  for all n  (capacity)
          y_n in {0,1},  x_{in} in Z+

N_max = sum(d_i): trivial upper bound.

CP-SAT requires integer coefficients -- widths are scaled by SCALE=100.

Dependencies:
    pip install ortools

References:
    Kantorovich (1960). Mathematical Methods of Organising and Planning Production.
    Wascher et al. (2007). EJOR, 183(3), 1109-1130.
"""

from __future__ import annotations

import sys
from pathlib import Path

from ortools.sat.python import cp_model

from instance import CuttingStockInstance

# CP-SAT only accepts integers -- scale widths x SCALE to avoid floats
SCALE = 100


def build_and_solve(instance: CuttingStockInstance, time_limit: float = 60.0) -> dict:
    """Build and solve the compact MIP with CP-SAT.

    Args:
        instance: Problem instance.
        time_limit: Time limit in seconds.

    Returns:
        Dict with 'status', 'rolls_used', 'patterns'.
    """
    W = int(round(instance.master_roll * SCALE))
    items = instance.items
    item_ids = [it.id for it in items]
    widths = {it.id: int(round(it.width * SCALE)) for it in items}
    demands = {it.id: it.demand for it in items}
    n_max = sum(it.demand for it in items)

    model = cp_model.CpModel()

    # Variables
    y = [model.new_bool_var(f"y_{n}") for n in range(n_max)]
    x = {
        (i, n): model.new_int_var(0, demands[i], f"x_{i}_{n}")
        for i in item_ids
        for n in range(n_max)
    }

    # Objective: minimize number of open rolls
    model.minimize(sum(y))

    # Demand constraints
    for i in item_ids:
        model.add(sum(x[i, n] for n in range(n_max)) >= demands[i])

    # Capacity constraints (scaled)
    for n in range(n_max):
        model.add(
            sum(widths[i] * x[i, n] for i in item_ids) <= W * y[n]
        )

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    status_code = solver.solve(model)

    status_map = {
        cp_model.OPTIMAL: "OPTIMAL",
        cp_model.FEASIBLE: "FEASIBLE",
        cp_model.INFEASIBLE: "INFEASIBLE",
        cp_model.UNKNOWN: "UNKNOWN",
    }
    status = status_map.get(status_code, "UNKNOWN")
    rolls_used = int(solver.objective_value) if status in ("OPTIMAL", "FEASIBLE") else -1

    patterns = {}
    if status in ("OPTIMAL", "FEASIBLE"):
        for n in range(n_max):
            if solver.value(y[n]) > 0:
                pat = {
                    i: solver.value(x[i, n])
                    for i in item_ids
                    if solver.value(x[i, n]) > 0
                }
                if pat:
                    patterns[n + 1] = pat

    return {"status": status, "rolls_used": rolls_used, "patterns": patterns}


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "../instances/small_3.json"
    inst = CuttingStockInstance.from_json(Path(path))
    res = build_and_solve(inst)
    print(f"Status : {res['status']}")
    print(f"Rolls  : {res['rolls_used']}")
    for n, pat in res["patterns"].items():
        print(f"  Roll {n}: {pat}")
