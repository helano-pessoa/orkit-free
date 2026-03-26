"""
Transportation Problem -- Pyomo + HiGHS (LP).

    min   sum_{i,j} c_ij * x_ij
    s.t.  sum_j x_ij <= s_i   for all i   (supply)
          sum_i x_ij >= d_j   for all j   (demand)
          x_ij >= 0

Run::

    python model_pyomo.py ../instances/small_3x4.json
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
from typing import Any, Dict

import pyomo.environ as pyo

from instance import TransportInstance


def build_model(instance: TransportInstance) -> pyo.ConcreteModel:
    m_idx = range(instance.m)
    n_idx = range(instance.n)
    s = [sup.supply for sup in instance.suppliers]
    d = [cus.demand for cus in instance.customers]
    c = instance.costs

    model = pyo.ConcreteModel()
    model.I = pyo.Set(initialize=m_idx)
    model.J = pyo.Set(initialize=n_idx)
    model.x = pyo.Var(model.I, model.J, domain=pyo.NonNegativeReals)

    model.obj = pyo.Objective(
        expr=sum(c[i][j] * model.x[i, j] for i in m_idx for j in n_idx),
        sense=pyo.minimize,
    )

    model.supply = pyo.Constraint(
        model.I, rule=lambda mdl, i: sum(mdl.x[i, j] for j in n_idx) <= s[i]
    )
    model.demand = pyo.Constraint(
        model.J, rule=lambda mdl, j: sum(mdl.x[i, j] for i in m_idx) >= d[j]
    )
    return model


def solve(instance: TransportInstance, solver: str = "highs") -> Dict[str, Any]:
    model = build_model(instance)
    opt = pyo.SolverFactory(solver)
    result = opt.solve(model, tee=False)

    status = str(result.solver.termination_condition)
    total_cost = pyo.value(model.obj)
    plan = [
        [pyo.value(model.x[i, j]) for j in range(instance.n)]
        for i in range(instance.m)
    ]
    return {"status": status, "total_cost": total_cost, "plan": plan}


def _main(path: str) -> None:
    inst = TransportInstance.from_json(path)
    result = solve(inst)
    print(f"Status    : {result['status']}")
    print(f"Total cost: {result['total_cost']:.2f}")
    print("Plan (rows=suppliers, cols=customers):")
    for row in result["plan"]:
        print(" ".join(f"{v:7.2f}" for v in row))


if __name__ == "__main__":
    _main(sys.argv[1] if len(sys.argv) > 1 else "../instances/small_3x4.json")
