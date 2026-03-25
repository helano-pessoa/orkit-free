"""1D Cutting Stock Problem — Column Generation with gurobipy.

WARNING: This file requires a valid Gurobi installation and license.
         Use only if you have an active academic or commercial license.

Installation:
    pip install gurobipy
    # License: https://www.gurobi.com/academia/academic-program-and-licenses/

The Column Generation logic is identical to the Pyomo implementation
(``model_pyomo.py``). The only difference is the optimization backend.

References:
    Gilmore, P. C., Gomory, R. E. (1961). Operations Research, 9(6), 849-859.
"""

from __future__ import annotations

import sys
from pathlib import Path

import gurobipy as gp
import numpy as np
from gurobipy import GRB

from instance import CuttingStockInstance, CuttingStockSolution

_EPSILON = 1.0e-6


# ---------------------------------------------------------------------------
# Problema Mestre LP relaxado (Gurobi)
# ---------------------------------------------------------------------------


def _solve_master_lp_gurobi(
    patterns: np.ndarray,
    demands: list[int],
    env: gp.Env,
) -> tuple[list[float], list[float]]:
    """Solve the LP-relaxed Master Problem with Gurobi.

    Args:
        patterns: Pattern matrix (m × K).
        demands: Demands per item type.
        env: Shared Gurobi environment.

    Returns:
        Tuple (x, pi) — primal values and shadow prices (π).
    """
    m, n_cols = patterns.shape
    with gp.Model(name="Mestre_LP", env=env) as mdl:
        mdl.Params.OutputFlag = 0

        x = mdl.addVars(n_cols, lb=0.0, name="x")
        mdl.setObjective(gp.quicksum(x[j] for j in range(n_cols)), GRB.MINIMIZE)

        constrs = [
            mdl.addConstr(
                gp.quicksum(float(patterns[i, j]) * x[j] for j in range(n_cols))
                >= float(demands[i]),
                name=f"d_{i}",
            )
            for i in range(m)
        ]

        mdl.optimize()

        x_vals = [x[j].X for j in range(n_cols)]
        # getDual only available in LP (no integer variables)
        pi = [c.Pi for c in constrs]

    return x_vals, pi


# ---------------------------------------------------------------------------
# Sub-problema Mochila Inteira (Gurobi)
# ---------------------------------------------------------------------------


def _solve_subproblem_gurobi(
    widths: list[float],
    shadow_prices: list[float],
    master_roll: float,
    env: gp.Env,
) -> tuple[float, list[float]]:
    """Solve the Subproblem (Integer Knapsack) with Gurobi.

    Args:
        widths: Widths of item types.
        shadow_prices: Shadow prices of demand constraints.
        master_roll: Master roll width.
        env: Shared Gurobi environment.

    Returns:
        Tuple (z_star, new_pattern).
    """
    m = len(widths)
    with gp.Model(name="Sub_Mochila", env=env) as mdl:
        mdl.Params.OutputFlag = 0

        y = mdl.addVars(m, vtype=GRB.INTEGER, lb=0, name="y")
        mdl.setObjective(
            gp.quicksum(float(shadow_prices[i]) * y[i] for i in range(m)),
            GRB.MAXIMIZE,
        )
        mdl.addConstr(
            gp.quicksum(float(widths[i]) * y[i] for i in range(m)) <= float(master_roll),
            name="cap",
        )

        mdl.optimize()

        z_star = float(mdl.ObjVal)
        new_pattern = [float(y[i].X) for i in range(m)]

    return z_star, new_pattern


# ---------------------------------------------------------------------------
# Geração de Colunas + MIP final (Gurobi)
# ---------------------------------------------------------------------------


def solve_gurobi(
    instance: CuttingStockInstance,
    verbose: bool = False,
    time_limit: float | None = None,
) -> CuttingStockSolution:
    """Solve the 1D Cutting Stock Problem via Column Generation (Gurobi).

    Args:
        instance: Instance data.
        verbose: If ``True``, prints progress log.
        time_limit: Time limit in seconds for the final MIP (None = no limit).

    Returns:
        CuttingStockSolution with patterns and quantities used.

    Raises:
        gp.GurobiError: If Gurobi is not licensed or installed.
    """
    silent_env = gp.Env(empty=True)
    silent_env.setParam("OutputFlag", 0)
    silent_env.start()

    widths = instance.widths
    demands = instance.demands
    m = instance.n_items

    # Trivial initial patterns
    max_per_item = [int(instance.master_roll // w) for w in widths]
    patterns = np.diag(max_per_item).astype(float)

    # --- Column Generation ---
    iteration = 0
    while True:
        iteration += 1
        _, pi = _solve_master_lp_gurobi(patterns, demands, silent_env)
        z_star, new_col = _solve_subproblem_gurobi(widths, pi, instance.master_roll, silent_env)

        if verbose:
            print(f"  [CG iter {iteration:3d}] z* = {z_star:.4f}  |  patterns = {patterns.shape[1]}")

        if z_star <= 1.0 + _EPSILON:
            break
        patterns = np.column_stack([patterns, new_col])

    if verbose:
        print(f"[CG] Converged with {patterns.shape[1]} patterns. Solving MIP...")

    # --- Final MIP ---
    n_cols = patterns.shape[1]
    with gp.Model(name="Mestre_MIP", env=silent_env) as mdl:
        if time_limit is not None:
            mdl.Params.TimeLimit = time_limit
        if verbose:
            mdl.Params.OutputFlag = 1

        x = mdl.addVars(n_cols, vtype=GRB.INTEGER, lb=0, name="x")
        mdl.setObjective(gp.quicksum(x[j] for j in range(n_cols)), GRB.MINIMIZE)

        for i in range(m):
            mdl.addConstr(
                gp.quicksum(float(patterns[i, j]) * x[j] for j in range(n_cols))
                >= float(demands[i]),
                name=f"d_{i}",
            )

        mdl.optimize()

        status = (
            "optimal" if mdl.Status == GRB.OPTIMAL
            else "time_limit" if mdl.Status == GRB.TIME_LIMIT
            else f"status_{mdl.Status}"
        )
        obj_val = float(mdl.ObjVal)
        quantities = [float(x[j].X) for j in range(n_cols)]

    return CuttingStockSolution(
        n_rolls_cut=obj_val,
        patterns=patterns.tolist(),
        quantities=quantities,
        solver_status=status,
    )


# ---------------------------------------------------------------------------
# Execução standalone
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "instances/small_3.json"
    inst = CuttingStockInstance.from_json(Path(path))

    print(f"\nInstance     : {inst.name}")
    print(f"Master roll  : {inst.master_roll}")
    print(f"Item types   : {inst.n_items}")

    sol = solve_gurobi(inst, verbose=True)

    print(f"\n--- Solution (Gurobi) ---")
    print(f"Status       : {sol.solver_status}")
    print(f"Patterns gen.: {sol.n_patterns}")
    print(f"Rolls cut    : {sol.n_rolls_cut:.0f}")
