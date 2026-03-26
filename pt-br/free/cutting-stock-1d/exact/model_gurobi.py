"""Corte de Estoque 1D -- Formulacao MIP Compacta com gurobipy.

ATENCAO: Requer instalacao e licenca valida do Gurobi.

Formulacao:
    min   sum_n  y_n
    s.a.  sum_n  x_{in}  >= d_i          para todo i  (demanda)
          sum_i  w_i * x_{in}  <= W*y_n  para todo n  (capacidade)
          y_n in {0,1},  x_{in} in Z+

N_max = sum(d_i): cota superior trivial.

Instalacao:
    pip install gurobipy
    # Licenca: https://www.gurobi.com/academia/academic-program-and-licenses/

Referencias:
    Kantorovich, L. V. (1960). Mathematical Methods of Organising and Planning Production.
    Wascher et al. (2007). European Journal of Operational Research, 183(3).
"""

from __future__ import annotations

import sys
from pathlib import Path

import gurobipy as gp
from gurobipy import GRB

from instance import CuttingStockInstance


def build_and_solve(
    instance: CuttingStockInstance,
    verbose: bool = False,
    time_limit: float | None = None,
) -> dict:
    """Constroi e resolve o MIP compacto com Gurobi.

    Args:
        instance: Instancia do problema.
        verbose: Exibe log do Gurobi se True.
        time_limit: Limite de tempo em segundos (None = sem limite).

    Returns:
        Dict com 'status', 'rolls_used', 'patterns'.
    """
    W = instance.master_roll
    items = instance.items
    item_ids = [it.id for it in items]
    widths = {it.id: it.width for it in items}
    demands = {it.id: it.demand for it in items}
    n_max = sum(it.demand for it in items)
    rolls = range(1, n_max + 1)

    env = gp.Env(empty=True)
    env.setParam("OutputFlag", 1 if verbose else 0)
    if time_limit is not None:
        env.setParam("TimeLimit", time_limit)
    env.start()

    with gp.Model(name="CuttingStock_MIP", env=env) as mdl:
        # Variaveis
        y = mdl.addVars(rolls, vtype=GRB.BINARY, name="y")
        x = mdl.addVars(item_ids, rolls, vtype=GRB.INTEGER, lb=0, name="x")

        # Objetivo: minimizar rolos abertos
        mdl.setObjective(gp.quicksum(y[n] for n in rolls), GRB.MINIMIZE)

        # Restricoes de demanda
        for i in item_ids:
            mdl.addConstr(
                gp.quicksum(x[i, n] for n in rolls) >= demands[i],
                name=f"dem_{i}",
            )

        # Restricoes de capacidade
        for n in rolls:
            mdl.addConstr(
                gp.quicksum(widths[i] * x[i, n] for i in item_ids) <= W * y[n],
                name=f"cap_{n}",
            )

        mdl.optimize()

        status = mdl.Status
        rolls_used = int(round(mdl.ObjVal)) if status == GRB.OPTIMAL else -1

        patterns = {}
        if status == GRB.OPTIMAL:
            for n in rolls:
                if y[n].X > 0.5:
                    pat = {i: int(round(x[i, n].X)) for i in item_ids if x[i, n].X > 0.5}
                    if pat:
                        patterns[n] = pat

    return {"status": status, "rolls_used": rolls_used, "patterns": patterns}


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "../instances/small_3.json"
    inst = CuttingStockInstance.from_json(Path(path))
    res = build_and_solve(inst)
    print(f"Status : {res['status']}")
    print(f"Rolos  : {res['rolls_used']}")
    for n, pat in res["patterns"].items():
        print(f"  Rolo {n}: {pat}")
