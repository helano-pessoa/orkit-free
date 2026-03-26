"""Problema de Transporte -- Formulacao LP com OR-Tools GLOP.

Formulacao:
    min   sum_{ij}  c_{ij} * x_{ij}
    s.a.  sum_j  x_{ij}  <= s_i     para todo i  (oferta)
          sum_i  x_{ij}  >= d_j     para todo j  (demanda)
          x_{ij} >= 0

Dependencias:
    pip install ortools

Referencias:
    Hitchcock (1941). Journal of Mathematics and Physics, 20(1), 224-230.
"""

from __future__ import annotations

import sys
from pathlib import Path

from ortools.linear_solver import pywraplp

from instance import TransportInstance


def build_and_solve(instance: TransportInstance, time_limit_ms: int = 60_000) -> dict:
    """Constroi e resolve o LP de transporte com GLOP (OR-Tools).

    Args:
        instance: Instancia do problema.
        time_limit_ms: Limite de tempo em milissegundos.

    Returns:
        Dict com 'status', 'total_cost', 'plan'.
    """
    suppliers = instance.suppliers
    customers = instance.customers
    costs = instance.costs

    solver = pywraplp.Solver.CreateSolver("GLOP")
    solver.set_time_limit(time_limit_ms)

    I = [s.id for s in suppliers]
    J = [c.id for c in customers]
    supply = {s.id: s.supply for s in suppliers}
    demand = {c.id: c.demand for c in customers}

    # Variaveis
    x = {
        (suppliers[i].id, customers[j].id): solver.NumVar(0.0, solver.infinity(), f"x_{i}_{j}")
        for i in range(len(suppliers))
        for j in range(len(customers))
    }

    # Objetivo
    obj = solver.Objective()
    for i_idx, s in enumerate(suppliers):
        for j_idx, c in enumerate(customers):
            obj.SetCoefficient(x[s.id, c.id], costs[i_idx][j_idx])
    obj.SetMinimization()

    # Restricoes de oferta
    for i_idx, s in enumerate(suppliers):
        ct = solver.Constraint(-solver.infinity(), supply[s.id], f"supply_{s.id}")
        for c in customers:
            ct.SetCoefficient(x[s.id, c.id], 1.0)

    # Restricoes de demanda
    for c in customers:
        ct = solver.Constraint(demand[c.id], solver.infinity(), f"demand_{c.id}")
        for s in suppliers:
            ct.SetCoefficient(x[s.id, c.id], 1.0)

    status_code = solver.Solve()

    status_map = {
        pywraplp.Solver.OPTIMAL: "OPTIMAL",
        pywraplp.Solver.FEASIBLE: "FEASIBLE",
        pywraplp.Solver.INFEASIBLE: "INFEASIBLE",
        pywraplp.Solver.ABNORMAL: "ABNORMAL",
        pywraplp.Solver.NOT_SOLVED: "NOT_SOLVED",
    }
    status = status_map.get(status_code, "UNKNOWN")
    total_cost = solver.Objective().Value() if status in ("OPTIMAL", "FEASIBLE") else -1

    plan = {}
    if status in ("OPTIMAL", "FEASIBLE"):
        for s in suppliers:
            for c in customers:
                v = x[s.id, c.id].solution_value()
                if v > 1e-9:
                    plan[(s.id, c.id)] = v

    return {"status": status, "total_cost": total_cost, "plan": plan}


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "../instances/small_3x4.json"
    inst = TransportInstance.from_json(Path(path))
    res = build_and_solve(inst)
    print(f"Status     : {res['status']}")
    print(f"Custo Total: {res['total_cost']:.2f}")
    for (i, j), qty in sorted(res["plan"].items()):
        print(f"  x[{i},{j}] = {qty:.1f}")
