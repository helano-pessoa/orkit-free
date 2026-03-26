"""
Transportation Problem -- OR-Tools GLOP (LP).

    min   sum_{i,j} c_ij * x_ij
    s.t.  sum_j x_ij <= s_i   for all i   (supply)
          sum_i x_ij >= d_j   for all j   (demand)
          x_ij >= 0

Run::

    python model_ortools.py ../instances/small_3x4.json
"""
from __future__ import annotations
import sys
from typing import Any, Dict

from ortools.linear_solver import pywraplp

from instance import TransportInstance


def build_and_solve(
    instance: TransportInstance,
    time_limit_ms: int = 60_000,
) -> Dict[str, Any]:
    m_idx = range(instance.m)
    n_idx = range(instance.n)
    s = [sup.supply for sup in instance.suppliers]
    d = [cus.demand for cus in instance.customers]
    c = instance.costs

    solver = pywraplp.Solver.CreateSolver("GLOP")
    solver.set_time_limit(time_limit_ms)
    infinity = solver.infinity()

    # Decision variables
    x = [[solver.NumVar(0, infinity, f"x_{i}_{j}") for j in n_idx] for i in m_idx]

    # Objective
    obj = solver.Objective()
    for i in m_idx:
        for j in n_idx:
            obj.SetCoefficient(x[i][j], c[i][j])
    obj.SetMinimization()

    # Supply constraints: sum_j x_ij <= s_i
    for i in m_idx:
        ct = solver.Constraint(-infinity, s[i], f"supply_{i}")
        for j in n_idx:
            ct.SetCoefficient(x[i][j], 1.0)

    # Demand constraints: sum_i x_ij >= d_j
    for j in n_idx:
        ct = solver.Constraint(d[j], infinity, f"demand_{j}")
        for i in m_idx:
            ct.SetCoefficient(x[i][j], 1.0)

    status_code = solver.Solve()
    status_map = {
        pywraplp.Solver.OPTIMAL: "optimal",
        pywraplp.Solver.FEASIBLE: "feasible",
        pywraplp.Solver.INFEASIBLE: "infeasible",
        pywraplp.Solver.UNBOUNDED: "unbounded",
    }
    status = status_map.get(status_code, "unknown")
    total_cost = solver.Objective().Value()
    plan = [[x[i][j].solution_value() for j in n_idx] for i in m_idx]
    return {"status": status, "total_cost": total_cost, "plan": plan}


def _main(path: str) -> None:
    inst = TransportInstance.from_json(path)
    result = build_and_solve(inst)
    print(f"Status    : {result['status']}")
    print(f"Total cost: {result['total_cost']:.2f}")
    for row in result["plan"]:
        print(" ".join(f"{v:7.2f}" for v in row))


if __name__ == "__main__":
    _main(sys.argv[1] if len(sys.argv) > 1 else "../instances/small_3x4.json")
