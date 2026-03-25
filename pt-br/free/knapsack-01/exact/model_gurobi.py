"""Mochila 0/1 — Implementação com gurobipy.

ATENÇÃO: Este arquivo requer instalação e licença válida do Gurobi.
         Obtenha uma licença gratuita para uso acadêmico em:
         https://www.gurobi.com/academia/academic-program-and-licenses/

Instalação:
    pip install gurobipy

Formulação:
    max  Σᵢ pᵢ xᵢ
    s.a. Σᵢ wᵢ xᵢ ≤ C
         xᵢ ∈ {0, 1},  ∀ i ∈ I

Para a versão open-source (sem licença Gurobi), use model_pyomo.py.
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
    """Resolve o Problema da Mochila 0/1 usando gurobipy.

    Args:
        instance: Dados da instância (capacidade e itens).
        verbose: Se ``True``, exibe o log completo do Gurobi no terminal.
        time_limit: Limite de tempo em segundos (``None`` = sem limite).

    Returns:
        KnapsackSolution com os itens selecionados e o lucro ótimo.

    Raises:
        gp.GurobiError: Se o Gurobi não estiver instalado ou licenciado.
        RuntimeError: Se não houver solução ótima ou viável.

    Example:
        >>> inst = KnapsackInstance.from_json("instances/small_5.json")
        >>> sol = solve_gurobi(inst)
        >>> print(f"Lucro ótimo: {sol.total_profit}")
        Lucro ótimo: 40.0
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
                f"Gurobi encerrou com status {model.Status}. "
                "Verifique se a instância possui solução viável."
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

    print(f"\nInstância  : {inst.name}")
    print(f"Itens      : {inst.n_items}   |   Capacidade: {inst.capacity}")
    print("-" * 45)

    sol = solve_gurobi(inst, verbose=False)
    print(f"Status     : {sol.solver_status}")
    print(f"Itens sel. : {sol.selected_items}")
    print(f"Peso total : {sol.total_weight}")
    print(f"Lucro total: {sol.total_profit}")

    if inst.optimal_value is not None:
        gap = sol.gap_to_optimal(inst.optimal_value)
        print(f"Gap ótimo  : {gap:.2f}%  (referência: {inst.optimal_value})")
