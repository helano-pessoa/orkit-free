"""Mochila 0/1 — Modelo Pyomo (Programação Inteira Binária).

Formulação:

    max  Σᵢ pᵢ xᵢ
    s.a. Σᵢ wᵢ xᵢ ≤ C
         xᵢ ∈ {0, 1},  ∀ i ∈ I

Solvers suportados (via argumento `solver`):
    "appsi_highs"  — HiGHS (padrão, open-source, recomendado)
    "glpk"         — GLPK  (didático, exemplos pequenos)
    "cbc"          — CBC   (fallback alternativo)
    "scip"         — SCIP  (instâncias difíceis)

Dependências:
    pip install pyomo highspy

Referências:
    Kellerer, H., Pferschy, U., Pisinger, D. (2004). Knapsack Problems. Springer.
    Martello, S., Toth, P. (1990). Knapsack Problems. Wiley.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pyomo.environ as pyo

from instance import KnapsackInstance, KnapsackSolution


# ---------------------------------------------------------------------------
# Construção do modelo
# ---------------------------------------------------------------------------


def build_model(instance: KnapsackInstance) -> pyo.ConcreteModel:
    """Constrói o modelo Pyomo para o Problema da Mochila 0/1.

    O modelo usa ConcreteModel: todos os dados são fornecidos diretamente,
    sem necessidade de AbstractModel + DataPortal.

    Args:
        instance: Instância do problema com capacidade e lista de itens.

    Returns:
        Modelo Pyomo construído e pronto para ser resolvido.

    Example:
        >>> inst = KnapsackInstance.from_json("instances/small_5.json")
        >>> model = build_model(inst)
        >>> print(model.I.data())
        {1, 2, 3, 4, 5}
    """
    model = pyo.ConcreteModel(name="Mochila_01")

    # --- Conjuntos ---
    model.I = pyo.Set(
        initialize=[item.id for item in instance.items],
        doc="Conjunto de itens disponíveis",
    )

    # --- Parâmetros ---
    model.p = pyo.Param(
        model.I,
        initialize={item.id: item.profit for item in instance.items},
        doc="Lucro do item i",
    )
    model.w = pyo.Param(
        model.I,
        initialize={item.id: item.weight for item in instance.items},
        doc="Peso do item i",
    )
    model.C = pyo.Param(
        initialize=instance.capacity,
        doc="Capacidade máxima da mochila",
    )

    # --- Variáveis de decisão ---
    model.x = pyo.Var(
        model.I,
        within=pyo.Binary,
        doc="x[i] = 1 se o item i for selecionado, 0 caso contrário",
    )

    # --- Função objetivo ---
    model.obj = pyo.Objective(
        expr=pyo.summation(model.p, model.x),
        sense=pyo.maximize,
        doc="Maximizar o lucro total dos itens selecionados",
    )

    # --- Restrições ---
    model.rest_capacidade = pyo.Constraint(
        expr=pyo.summation(model.w, model.x) <= model.C,
        doc="Peso total não pode exceder a capacidade da mochila",
    )

    return model


# ---------------------------------------------------------------------------
# Resolução
# ---------------------------------------------------------------------------


def solve(
    instance: KnapsackInstance,
    solver: str = "appsi_highs",
    verbose: bool = False,
) -> KnapsackSolution:
    """Resolve a instância do Problema da Mochila 0/1.

    Args:
        instance: Dados da instância (capacidade e itens).
        solver: Nome do solver Pyomo.
            Padrão: ``"appsi_highs"`` (HiGHS — open-source, recomendado).
            Alternativas: ``"glpk"``, ``"cbc"``, ``"scip"``.
        verbose: Se ``True``, exibe o log do solver no terminal.

    Returns:
        KnapsackSolution com os itens selecionados e o valor ótimo.

    Raises:
        RuntimeError: Se o solver não encontrar solução ótima ou viável.

    Example:
        >>> inst = KnapsackInstance.from_json("instances/small_5.json")
        >>> sol = solve(inst)
        >>> print(f"Lucro ótimo: {sol.total_profit}")
        Lucro ótimo: 40.0
    """
    model = build_model(instance)
    opt = pyo.SolverFactory(solver)
    results = opt.solve(model, tee=verbose)

    status = str(results.solver.termination_condition)
    if status not in {"optimal", "feasible"}:
        raise RuntimeError(
            f"Solver encerrou com status '{status}'. "
            "Verifique se o solver está instalado e a instância é válida."
        )

    # Coleta da solução
    selected = [i for i in model.I if pyo.value(model.x[i]) > 0.5]
    total_profit = float(pyo.value(model.obj))
    total_weight = sum(
        instance.items[i - 1].weight
        for i in selected
    )

    return KnapsackSolution(
        selected_items=selected,
        total_profit=total_profit,
        total_weight=total_weight,
        solver_status=status,
    )


# ---------------------------------------------------------------------------
# Execução standalone
# ---------------------------------------------------------------------------


def _print_solution(instance: KnapsackInstance, sol: KnapsackSolution) -> None:
    """Imprime o resumo da solução no terminal."""
    print(f"\nInstância  : {instance.name}")
    print(f"Itens      : {instance.n_items}   |   Capacidade: {instance.capacity}")
    print("-" * 45)
    print(f"Status     : {sol.solver_status}")
    print(f"Itens sel. : {sol.selected_items}")
    print(f"Peso total : {sol.total_weight}")
    print(f"Lucro total: {sol.total_profit}")

    if instance.optimal_value is not None:
        gap = sol.gap_to_optimal(instance.optimal_value)
        print(f"Gap ótimo  : {gap:.2f}%  (referência: {instance.optimal_value})")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "instances/small_5.json"
    inst = KnapsackInstance.from_json(Path(path))
    solution = solve(inst, verbose=False)
    _print_solution(inst, solution)
