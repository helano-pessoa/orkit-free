"""
Transportation Problem -- Gurobi (LP).

    min   sum_{i,j} c_ij * x_ij
    s.t.  sum_j x_ij <= s_i   for all i   (supply)
          sum_i x_ij >= d_j   for all j   (demand)
          x_ij >= 0

Run::

    python model_gurobi.py ../instances/small_3x4.json
"""
from __future__ import annotations
import sys
from typing import Any, Dict

import gurobipy as gp
from gurobipy import GRB

from instance import TransportInstance


def build_and_solve(
    instance: TransportInstance,
    verbose: bool = False,
    time_limit: float = 120.0,
) -> Dict[str, Any]:
    m_idx = range(instance.m)
    n_idx = range(instance.n)
    s = [sup.supply for sup in instance.suppliers]
    d = [cus.demand for cus in instance.customers]
    c = instance.costs

    model = gp.Model("transportation")
    if not verbose:
        model.Params.OutputFlag = 0
    model.Params.TimeLimit = time_limit

    x = model.addVars(m_idx, n_idx, lb=0.0, name="x")
    model.setObjective(
        gp.quicksum(c[i][j] * x[i, j] for i in m_idx for j in n_idx),
        GRB.MINIMIZE,
    )

    for i in m_idx:
        model.addConstr(
            gp.quicksum(x[i, j] for j in n_idx) <= s[i], name=f"supply_{i}"
        )
    for j in n_idx:
        model.addConstr(
            gp.quicksum(x[i, j] for i in m_idx) >= d[j], name=f"demand_{j}"
        )

    model.optimize()

    status = model.Status
    total_cost = model.ObjVal if status == GRB.OPTIMAL else float("inf")
    plan = [
        [x[i, j].X for j in n_idx] for i in m_idx
    ]
    return {"status": status, "total_cost": total_cost, "plan": plan}


def _main(path: str) -> None:
    from instance import TransportInstance
    inst = TransportInstance.from_json(path)
    result = build_and_solve(inst)
    print(f"Status    : {result['status']}")
    print(f"Total cost: {result['total_cost']:.2f}")
    for row in result["plan"]:
        print(" ".join(f"{v:7.2f}" for v in row))


if __name__ == "__main__":
    import sys
    _main(sys.argv[1] if len(sys.argv) > 1 else "../instances/small_3x4.json")
