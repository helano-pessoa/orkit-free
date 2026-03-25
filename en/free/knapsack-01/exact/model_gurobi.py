"""0/1 Knapsack — gurobipy implementation.

WARNING: This file requires a valid Gurobi installation and license.
         Get a free academic license at:
         https://www.gurobi.com/academia/academic-program-and-licenses/

Installation:
    pip install gurobipy

Formulation:
    max  Σᵢ pᵢ xᵢ
    s.t. Σᵢ wᵢ xᵢ ≤ C
         xᵢ ∈ {0, 1},  ∀ i ∈ I

For the open-source version (no Gurobi license required), use model_pyomo.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

import gurobipy as gp
from gurobipy import GRB

from instance import KnapsackInstance, KnapsackSolution


def solve_gurobi(
    instance: KnapsackInstance,
    verbose: bool = False,
    time_limit: float | None = None,
) -> KnapsackSolution:
    """Solve the 0/1 Knapsack problem using gurobipy.

    Args:
        instance: Problem data (capacity and items).
        verbose: If ``True``, stream full Gurobi log to stdout.
        time_limit: Time limit in seconds (``None`` = no limit).

    Returns:
        KnapsackSolution with selected items and optimal profit.

    Raises:
        gp.GurobiError: If Gurobi is not installed or not licensed.
        RuntimeError: If no optimal or feasible solution is found.

    Example:
        >>> inst = KnapsackInstance.from_json("instances/small_5.json")
        >>> sol = solve_gurobi(inst)
        >>> print(f"Optimal profit: {sol.total_profit}")
        Optimal profit: 40.0
    """
    # Ambiente sem saída padrão quando verbose=False
    env = gp.Env(empty=True)
    env.setParam("OutputFlag", 1 if verbose else 0)
    env.start()

    with gp.Model(name="Mochila_01", env=env) as model:
        if time_limit is not None:
            model.Params.TimeLimit = time_limit

        items = instance.items
        n = len(items)

        # Variáveis binárias: x[i] ∈ {0, 1}
        x = model.addVars(n, vtype=GRB.BINARY, name="x")

        # Função objetivo: maximizar lucro total
        model.setObjective(
            gp.quicksum(items[i].profit * x[i] for i in range(n)),
            GRB.MAXIMIZE,
        )

        # Restrição de capacidade
        model.addConstr(
            gp.quicksum(items[i].weight * x[i] for i in range(n)) <= instance.capacity,
            name="rest_capacidade",
        )

        model.optimize()

        # Verificação do status
        if model.Status not in (GRB.OPTIMAL, GRB.TIME_LIMIT):
            raise RuntimeError(
                f"Gurobi terminated with status {model.Status}. "
                "Verify that the instance has a feasible solution."
            )

        selected = [items[i].id for i in range(n) if x[i].X > 0.5]
        total_profit = model.ObjVal
        total_weight = sum(items[i].weight for i in range(n) if x[i].X > 0.5)

        status_str = "optimal" if model.Status == GRB.OPTIMAL else "time_limit"
        return KnapsackSolution(
            selected_items=selected,
            total_profit=total_profit,
            total_weight=total_weight,
            solver_status=status_str,
        )


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "instances/small_5.json"
    inst = KnapsackInstance.from_json(Path(path))

    print(f"\nInstance   : {inst.name}")
    print(f"Items      : {inst.n_items}   |   Capacity: {inst.capacity}")
    print("-" * 45)

    sol = solve_gurobi(inst, verbose=False)
    print(f"Status     : {sol.solver_status}")
    print(f"Selected   : {sol.selected_items}")
    print(f"Tot. weight: {sol.total_weight}")
    print(f"Tot. profit: {sol.total_profit}")

    if inst.optimal_value is not None:
        gap = sol.gap_to_optimal(inst.optimal_value)
        print(f"Gap        : {gap:.2f}%  (reference: {inst.optimal_value})")
