"""1D Cutting Stock -- Compact MIP formulation with Pyomo + HiGHS.

Formulation:
    min   sum_n  y_n
    s.t.  sum_n  x_{in}  >= d_i          for all i  (demand)
          sum_i  w_i * x_{in}  <= W*y_n  for all n  (capacity)
          y_n in {0,1},  x_{in} in Z+

N_max = sum(d_i): trivial upper bound (one item per roll in the worst case).

Supported solvers: "appsi_highs" (default), "glpk", "cbc", "scip".

Dependencies:
    pip install pyomo highspy

References:
    Kantorovich, L. V. (1960). Mathematical Methods of Organising and Planning Production.
    Wascher et al. (2007). European Journal of Operational Research, 183(3), 1109-1130.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pyomo.environ as pyo

from instance import CuttingStockInstance


def build_model(instance: CuttingStockInstance) -> pyo.ConcreteModel:
    """Build compact MIP model for 1D Cutting Stock.

    Args:
        instance: Problem instance (master_roll, items with width and demand).

    Returns:
        Pyomo ConcreteModel ready to solve.
    """
    W = instance.master_roll
    items = instance.items
    n_max = sum(it.demand for it in items)  # trivial upper bound

    model = pyo.ConcreteModel(name="CuttingStock_MIP")

    # --- Sets ---
    model.I = pyo.Set(initialize=[it.id for it in items])
    model.N = pyo.RangeSet(1, n_max)

    # --- Parameters ---
    model.w = pyo.Param(model.I, initialize={it.id: it.width for it in items})
    model.d = pyo.Param(model.I, initialize={it.id: it.demand for it in items})
    model.W = pyo.Param(initialize=W)

    # --- Variables ---
    model.y = pyo.Var(model.N, within=pyo.Binary)           # roll n opened?
    model.x = pyo.Var(model.I, model.N, within=pyo.NonNegativeIntegers)

    # --- Objective ---
    model.obj = pyo.Objective(
        expr=sum(model.y[n] for n in model.N),
        sense=pyo.minimize,
    )

    # --- Demand constraints ---
    def demand_rule(m, i):
        return sum(m.x[i, n] for n in m.N) >= m.d[i]

    model.demand = pyo.Constraint(model.I, rule=demand_rule)

    # --- Capacity constraints ---
    def capacity_rule(m, n):
        return sum(m.w[i] * m.x[i, n] for i in m.I) <= m.W * m.y[n]

    model.capacity = pyo.Constraint(model.N, rule=capacity_rule)

    return model


def solve(instance: CuttingStockInstance, solver: str = "appsi_highs") -> dict:
    """Solve instance and return results dictionary.

    Args:
        instance: Problem instance.
        solver: Pyomo solver name.

    Returns:
        Dict with 'status', 'rolls_used', 'patterns'.
    """
    model = build_model(instance)
    opt = pyo.SolverFactory(solver)
    result = opt.solve(model, tee=False)

    status = str(result.solver.termination_condition)
    rolls_used = int(round(pyo.value(model.obj)))

    patterns = {}
    for n in model.N:
        if pyo.value(model.y[n]) > 0.5:
            pattern = {}
            for i in model.I:
                qty = int(round(pyo.value(model.x[i, n])))
                if qty > 0:
                    pattern[i] = qty
            if pattern:
                patterns[n] = pattern

    return {"status": status, "rolls_used": rolls_used, "patterns": patterns}


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "../instances/small_3.json"
    inst = CuttingStockInstance.from_json(Path(path))
    res = solve(inst)
    print(f"Status : {res['status']}")
    print(f"Rolls  : {res['rolls_used']}")
    for n, pat in res["patterns"].items():
        print(f"  Roll {n}: {pat}")
