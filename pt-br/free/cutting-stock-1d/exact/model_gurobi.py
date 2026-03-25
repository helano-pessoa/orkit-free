"""Corte de Estoque 1D — Geração de Colunas com gurobipy.

ATENÇÃO: Este arquivo requer instalação e licença válida do Gurobi.
         Use apenas se tiver licença acadêmica ou comercial ativa.

Instalação:
    pip install gurobipy
    # Licença: https://www.gurobi.com/academia/academic-program-and-licenses/

A lógica de Geração de Colunas é idêntica à implementação em Pyomo
(``model_pyomo.py``). A diferença está no backend de otimização.

Referências:
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
    """Resolve o Problema Mestre LP relaxado com Gurobi.

    Args:
        patterns: Matriz de padrões (m × K).
        demands: Demandas por tipo de peça.
        env: Ambiente Gurobi compartilhado.

    Returns:
        Tupla (x, pi) — valores primais e preços-sombra (π).
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
        # getDual disponível somente em LP (sem variáveis inteiras)
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
    """Resolve o Sub-problema (Mochila Inteira) com Gurobi.

    Args:
        widths: Larguras dos tipos de peça.
        shadow_prices: Preços-sombra das restrições de demanda.
        master_roll: Largura do rolo-mestre.
        env: Ambiente Gurobi compartilhado.

    Returns:
        Tupla (z_star, novo_padrao).
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
    """Resolve o Problema de Corte de Estoque 1D via Geração de Colunas (Gurobi).

    Args:
        instance: Dados da instância.
        verbose: Se ``True``, exibe log de progresso.
        time_limit: Limite de tempo em segundos para o MIP final (None = sem limite).

    Returns:
        CuttingStockSolution com padrões e quantidades usadas.

    Raises:
        gp.GurobiError: Se o Gurobi não estiver licenciado ou instalado.
    """
    silent_env = gp.Env(empty=True)
    silent_env.setParam("OutputFlag", 0)
    silent_env.start()

    widths = instance.widths
    demands = instance.demands
    m = instance.n_items

    # Padrões iniciais triviais
    max_per_item = [int(instance.master_roll // w) for w in widths]
    patterns = np.diag(max_per_item).astype(float)

    # --- Geração de Colunas ---
    iteration = 0
    while True:
        iteration += 1
        _, pi = _solve_master_lp_gurobi(patterns, demands, silent_env)
        z_star, new_col = _solve_subproblem_gurobi(widths, pi, instance.master_roll, silent_env)

        if verbose:
            print(f"  [CG iter {iteration:3d}] z* = {z_star:.4f}  |  padrões = {patterns.shape[1]}")

        if z_star <= 1.0 + _EPSILON:
            break
        patterns = np.column_stack([patterns, new_col])

    if verbose:
        print(f"[CG] Convergido com {patterns.shape[1]} padrões. Resolvendo MIP...")

    # --- MIP final ---
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

    print(f"\nInstância    : {inst.name}")
    print(f"Rolo-mestre  : {inst.master_roll}")
    print(f"Tipos de peça: {inst.n_items}")

    sol = solve_gurobi(inst, verbose=True)

    print(f"\n--- Solução (Gurobi) ---")
    print(f"Status       : {sol.solver_status}")
    print(f"Padrões ger. : {sol.n_patterns}")
    print(f"Rolos cortad.: {sol.n_rolls_cut:.0f}")
