"""Mochila 0/1 -- Formulacao MIP com OR-Tools CP-SAT.

Formulacao:
    max  sum_i  p_i * x_i
    s.a. sum_i  w_i * x_i  <= C
         x_i in {0, 1}

CP-SAT apenas aceita inteiros -- pesos e capacidade sao escalados por SCALE=100.

Dependencias:
    pip install ortools

Referencias:
    Kellerer, H., Pferschy, U., Pisinger, D. (2004). Knapsack Problems. Springer.
"""

from __future__ import annotations

import sys
from pathlib import Path

from ortools.sat.python import cp_model

from instance import KnapsackInstance

SCALE = 100  # escala para converter pesos para inteiros


def build_and_solve(instance: KnapsackInstance, time_limit: float = 60.0) -> dict:
    """Constroi e resolve a Mochila 0/1 com CP-SAT.

    Args:
        instance: Instancia do problema.
        time_limit: Limite de tempo em segundos.

    Returns:
        Dict com 'status', 'objective', 'selected_items'.
    """
    C = int(round(instance.capacity * SCALE))
    items = instance.items
    item_ids = [it.id for it in items]
    weights = {it.id: int(round(it.weight * SCALE)) for it in items}
    profits = {it.id: int(round(it.profit)) for it in items}

    model = cp_model.CpModel()

    x = {i: model.new_bool_var(f"x_{i}") for i in item_ids}

    # Objetivo: maximizar lucro
    model.maximize(sum(profits[i] * x[i] for i in item_ids))

    # Restricao de capacidade
    model.add(sum(weights[i] * x[i] for i in item_ids) <= C)

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
    obj = int(solver.objective_value) if status in ("OPTIMAL", "FEASIBLE") else -1
    selected = [i for i in item_ids if status in ("OPTIMAL", "FEASIBLE") and solver.value(x[i]) > 0]

    return {"status": status, "objective": obj, "selected_items": selected}


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "../instances/small_5.json"
    inst = KnapsackInstance.from_json(Path(path))
    res = build_and_solve(inst)
    print(f"Status  : {res['status']}")
    print(f"Objetivo: {res['objective']}")
    print(f"Itens   : {res['selected_items']}")
