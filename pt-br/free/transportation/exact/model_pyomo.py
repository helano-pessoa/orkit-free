"""Problema de Transporte -- Formulacao LP com Pyomo + HiGHS.

Formulacao:
    min   sum_{ij}  c_{ij} * x_{ij}
    s.a.  sum_j  x_{ij}  <= s_i     para todo i  (oferta)
          sum_i  x_{ij}  >= d_j     para todo j  (demanda)
          x_{ij} >= 0

Dependencias:
    pip install pyomo highspy

Referencias:
    Hitchcock, F. L. (1941). Journal of Mathematics and Physics, 20(1), 224-230.
    Dantzig, G. B. (1963). Linear Programming and Extensions. Princeton UP.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pyomo.environ as pyo

from instance import TransportInstance


def build_model(instance: TransportInstance) -> pyo.ConcreteModel:
    """Constroi o modelo LP para o Problema de Transporte."""
    suppliers = instance.suppliers
    customers = instance.customers
    costs = instance.costs

    I = [s.id for s in suppliers]
    J = [c.id for c in customers]
    supply = {s.id: s.supply for s in suppliers}
    demand = {c.id: c.demand for c in customers}
    c = {(suppliers[i].id, customers[j].id): costs[i][j] for i in range(len(suppliers)) for j in range(len(customers))}

    model = pyo.ConcreteModel(name="Transportation_LP")
    model.I = pyo.Set(initialize=I)
    model.J = pyo.Set(initialize=J)
    model.c = pyo.Param(model.I, model.J, initialize=c)
    model.s = pyo.Param(model.I, initialize=supply)
    model.d = pyo.Param(model.J, initialize=demand)
    model.x = pyo.Var(model.I, model.J, within=pyo.NonNegativeReals)

    model.obj = pyo.Objective(
        expr=sum(model.c[i, j] * model.x[i, j] for i in model.I for j in model.J),
        sense=pyo.minimize,
    )

    def supply_rule(m, i):
        return sum(m.x[i, j] for j in m.J) <= m.s[i]

    model.supply_con = pyo.Constraint(model.I, rule=supply_rule)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in m.I) >= m.d[j]

    model.demand_con = pyo.Constraint(model.J, rule=demand_rule)

    return model


def solve(instance: TransportInstance, solver: str = "appsi_highs") -> dict:
    """Resolve a instancia e retorna dicionario de resultados."""
    model = build_model(instance)
    opt = pyo.SolverFactory(solver)
    result = opt.solve(model, tee=False)

    status = str(result.solver.termination_condition)
    total_cost = pyo.value(model.obj)

    suppliers = instance.suppliers
    customers = instance.customers
    plan = {}
    for s in suppliers:
        for c in customers:
            v = pyo.value(model.x[s.id, c.id])
            if v > 1e-9:
                plan[(s.id, c.id)] = v

    return {"status": status, "total_cost": total_cost, "plan": plan}


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "../instances/small_3x4.json"
    inst = TransportInstance.from_json(Path(path))
    res = solve(inst)
    print(f"Status     : {res['status']}")
    print(f"Custo Total: {res['total_cost']:.2f}")
    for (i, j), qty in sorted(res["plan"].items()):
        print(f"  x[{i},{j}] = {qty:.1f}")
