"""Problema de Transporte -- Formulacao LP com gurobipy.

WARNING: Requer uma licenca Gurobi valida.

Formulacao:
    min   sum_{ij}  c_{ij} * x_{ij}
    s.a.  sum_j  x_{ij}  <= s_i     para todo i  (oferta)
          sum_i  x_{ij}  >= d_j     para todo j  (demanda)
          x_{ij} >= 0

Dependencias:
    pip install gurobipy

Referencias:
    Hitchcock (1941). Journal of Mathematics and Physics, 20(1), 224-230.
"""

from __future__ import annotations

import sys
from pathlib import Path

import gurobipy as gp
from gurobipy import GRB

from instance import TransportInstance


def build_and_solve(
    instance: TransportInstance,
    verbose: bool = False,
    time_limit: float | None = None,
) -> dict:
    """Constroi e resolve o LP de transporte com Gurobi."""
    suppliers = instance.suppliers
    customers = instance.customers
    costs = instance.costs

    I = [s.id for s in suppliers]
    J = [c.id for c in customers]
    supply = {s.id: s.supply for s in suppliers}
    demand = {c.id: c.demand for c in customers}
    c_dict = {(suppliers[i].id, customers[j].id): costs[i][j] for i in range(len(suppliers)) for j in range(len(customers))}

    env = gp.Env(empty=True)
    env.setParam("OutputFlag", 1 if verbose else 0)
    if time_limit is not None:
        env.setParam("TimeLimit", time_limit)
    env.start()

    with gp.Model(name="Transportation_LP", env=env) as mdl:
        x = mdl.addVars(I, J, lb=0, name="x")

        mdl.setObjective(gp.quicksum(c_dict[i, j] * x[i, j] for i in I for j in J), GRB.MINIMIZE)

        for i in I:
            mdl.addConstr(gp.quicksum(x[i, j] for j in J) <= supply[i], name=f"supply_{i}")
        for j in J:
            mdl.addConstr(gp.quicksum(x[i, j] for i in I) >= demand[j], name=f"demand_{j}")

        mdl.optimize()

        status = mdl.Status
        total_cost = mdl.ObjVal if status == GRB.OPTIMAL else -1
        plan = {(i, j): x[i, j].X for i in I for j in J if x[i, j].X > 1e-9} if status == GRB.OPTIMAL else {}

    return {"status": status, "total_cost": total_cost, "plan": plan}


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "../instances/small_3x4.json"
    inst = TransportInstance.from_json(Path(path))
    res = build_and_solve(inst)
    print(f"Status     : {res['status']}")
    print(f"Custo Total: {res['total_cost']:.2f}")
    for (i, j), qty in sorted(res["plan"].items()):
        print(f"  x[{i},{j}] = {qty:.1f}")
