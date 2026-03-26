"""Corte de Estoque 1D — Formulacao MIP Compacta com Pyomo + HiGHS.

Formulacao:

    min   sum_n  y_n
    s.a.  sum_n  x_{in}  >= d_i          para todo i  (demanda)
          sum_i  w_i * x_{in}  <= W*y_n  para todo n  (capacidade)
          y_n in {0,1},  x_{in} in Z+

N_max = sum(d_i): cota superior trivial (uma peca por rolo no pior caso).

Solvers suportados: "appsi_highs" (padrao), "glpk", "cbc", "scip".

Dependencias:
    pip install pyomo highspy

Referencias:
    Kantorovich, L. V. (1960). Mathematical Methods of Organising and Planning Production.
    Wascher et al. (2007). European Journal of Operational Research, 183(3), 1109-1130.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pyomo.environ as pyo

from instance import CuttingStockInstance


def build_model(instance: CuttingStockInstance) -> pyo.ConcreteModel:
    """Constroi o modelo MIP compacto para o Corte de Estoque 1D.

    Args:
        instance: Instancia do problema (master_roll, items com width e demand).

    Returns:
        Modelo Pyomo construido e pronto para resolver.
    """
    W = instance.master_roll
    items = instance.items
    n_max = sum(it.demand for it in items)  # cota superior trivial

    model = pyo.ConcreteModel(name="CuttingStock_MIP")

    # --- Conjuntos ---
    model.I = pyo.Set(initialize=[it.id for it in items])
    model.N = pyo.RangeSet(1, n_max)

    # --- Parametros ---
    model.w = pyo.Param(model.I, initialize={it.id: it.width for it in items})
    model.d = pyo.Param(model.I, initialize={it.id: it.demand for it in items})
    model.W = pyo.Param(initialize=W)

    # --- Variaveis ---
    model.y = pyo.Var(model.N, within=pyo.Binary)           # rolo n aberto?
    model.x = pyo.Var(model.I, model.N, within=pyo.NonNegativeIntegers)

    # --- Objetivo ---
    model.obj = pyo.Objective(
        expr=sum(model.y[n] for n in model.N),
        sense=pyo.minimize,
    )

    # --- Restricoes de demanda ---
    def demanda_rule(m, i):
        return sum(m.x[i, n] for n in m.N) >= m.d[i]

    model.demanda = pyo.Constraint(model.I, rule=demanda_rule)

    # --- Restricoes de capacidade ---
    def capacidade_rule(m, n):
        return sum(m.w[i] * m.x[i, n] for i in m.I) <= m.W * m.y[n]

    model.capacidade = pyo.Constraint(model.N, rule=capacidade_rule)

    return model


def solve(instance: CuttingStockInstance, solver: str = "appsi_highs") -> dict:
    """Resolve a instancia e retorna dicionario com resultados.

    Args:
        instance: Instancia do problema.
        solver: Nome do solver Pyomo.

    Returns:
        Dict com 'status', 'rolls_used', 'patterns'.
    """
    model = build_model(instance)
    opt = pyo.SolverFactory(solver)
    result = opt.solve(model, tee=False)

    status = str(result.solver.termination_condition)
    rolls_used = int(round(pyo.value(model.obj)))

    # Padroes de corte utilizados
    patterns = {}
    for n in model.N:
        if pyo.value(model.y[n]) > 0.5:
            pattern = {}
            for i in model.I:
                qty = int(round(pyo.value(model.x[i, n])))
                if qty > 0:
                    pattern[i] = qty
            if pattern:
                patterns[n] = pattern

    return {"status": status, "rolls_used": rolls_used, "patterns": patterns}


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "../instances/small_3.json"
    inst = CuttingStockInstance.from_json(Path(path))
    res = solve(inst)
    print(f"Status : {res['status']}")
    print(f"Rolos  : {res['rolls_used']}")
    for n, pat in res["patterns"].items():
        print(f"  Rolo {n}: {pat}")


from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pyomo.environ as pyo

from instance import CuttingStockInstance, CuttingStockSolution

# Tolerância para critério de parada da Geração de Colunas
_EPSILON = 1.0e-6


# ---------------------------------------------------------------------------
# Problema Mestre (LP relaxado)
# ---------------------------------------------------------------------------


def _solve_master_lp(
    patterns: np.ndarray,
    demands: list[int],
    solver: str,
) -> tuple[list[float], list[float]]:
    """Resolve o Problema Mestre LP relaxado.

    Args:
        patterns: Matriz de padrões de corte (m × K), onde patterns[i, j]
            é o número de peças do tipo i no padrão j.
        demands: Lista de demandas por tipo de peça.
        solver: Nome do solver Pyomo.

    Returns:
        Tupla (x, pi) onde x é a solução do Mestre LP e pi são os
        preços-sombra (variáveis duais) das restrições de demanda.
    """
    m, n_cols = patterns.shape
    model = pyo.ConcreteModel(name="Mestre_LP")

    model.M = pyo.RangeSet(1, m)
    model.N = pyo.RangeSet(1, n_cols)

    # Variáveis contínuas não negativas (LP relaxado)
    model.x = pyo.Var(model.N, within=pyo.NonNegativeReals)

    # Parâmetros: padrões e demandas
    model.a = pyo.Param(
        model.M,
        model.N,
        initialize=lambda _, i, j: float(patterns[i - 1, j - 1]),
    )
    model.d = pyo.Param(
        model.M,
        initialize=lambda _, i: float(demands[i - 1]),
    )

    # Função objetivo: minimizar número total de rolos cortados
    model.obj = pyo.Objective(
        expr=sum(model.x[j] for j in model.N),
        sense=pyo.minimize,
    )

    # Restrições de demanda: cada tipo deve ser atendido
    model.rest_demanda = pyo.Constraint(
        model.M,
        rule=lambda mod, i: sum(mod.a[i, j] * mod.x[j] for j in mod.N)
        >= mod.d[i],
    )

    # Sufixo para extrair variáveis duais
    model.dual = pyo.Suffix(direction=pyo.Suffix.IMPORT)

    opt = pyo.SolverFactory(solver)
    opt.solve(model, tee=False)

    x_vals = [pyo.value(model.x[j]) for j in model.N]
    # Preços-sombra na ordem das restrições de demanda (1..m)
    pi = [model.dual.get(model.rest_demanda[i], 0.0) for i in model.M]

    return x_vals, pi


# ---------------------------------------------------------------------------
# Sub-problema (Mochila Inteira)
# ---------------------------------------------------------------------------


def _solve_subproblem(
    widths: list[float],
    shadow_prices: list[float],
    master_roll: float,
    solver: str,
) -> tuple[float, list[float]]:
    """Resolve o Sub-problema: Mochila Inteira com preços-sombra como lucros.

    Identifica o padrão de maior custo reduzido. Se o valor ótimo z* > 1,
    o padrão é promissor e deve ser adicionado ao Mestre.

    Args:
        widths: Larguras dos tipos de peça.
        shadow_prices: Preços-sombra (π) das restrições de demanda.
        master_roll: Largura do rolo-mestre.
        solver: Nome do solver Pyomo.

    Returns:
        Tupla (z_star, novo_padrao) — valor ótimo e novo padrão de corte.
    """
    m = len(widths)
    model = pyo.ConcreteModel(name="Sub_Mochila")

    model.M = pyo.RangeSet(1, m)

    # Variáveis inteiras não negativas
    model.y = pyo.Var(model.M, within=pyo.NonNegativeIntegers)

    model.pi = pyo.Param(
        model.M,
        initialize=lambda _, i: float(shadow_prices[i - 1]),
    )
    model.w = pyo.Param(
        model.M,
        initialize=lambda _, i: float(widths[i - 1]),
    )
    model.W = pyo.Param(initialize=float(master_roll))

    # Maximizar o custo reduzido (preço-sombra × quantidade)
    model.obj = pyo.Objective(
        expr=sum(model.pi[i] * model.y[i] for i in model.M),
        sense=pyo.maximize,
    )

    # Restrição de capacidade: padrão deve caber no rolo-mestre
    model.rest_cap = pyo.Constraint(
        expr=sum(model.w[i] * model.y[i] for i in model.M) <= model.W,
    )

    opt = pyo.SolverFactory(solver)
    opt.solve(model, tee=False)

    z_star = float(pyo.value(model.obj))
    new_pattern = [float(pyo.value(model.y[i])) for i in model.M]

    return z_star, new_pattern


# ---------------------------------------------------------------------------
# Geração de Colunas completa
# ---------------------------------------------------------------------------


def _column_generation(
    instance: CuttingStockInstance,
    solver: str,
) -> np.ndarray:
    """Executa a Geração de Colunas e retorna a matriz de padrões final.

    Inicia com padrões triviais (um tipo por padrão) e itera até que
    nenhum padrão promissor seja encontrado.

    Args:
        instance: Dados da instância.
        solver: Nome do solver Pyomo.

    Returns:
        Matriz de padrões (m × K) após convergência.
    """
    m = instance.n_items
    widths = instance.widths
    demands = instance.demands

    # Padrões iniciais: diagonal com quantidades máximas de cada tipo
    max_per_item = [int(instance.master_roll // w) for w in widths]
    patterns = np.diag(max_per_item).astype(float)

    while True:
        _, shadow_prices = _solve_master_lp(patterns, demands, solver)
        z_star, new_pattern = _solve_subproblem(
            widths, shadow_prices, instance.master_roll, solver
        )

        # Critério de parada: nenhum padrão melhora a solução
        if z_star <= 1.0 + _EPSILON:
            break

        patterns = np.column_stack([patterns, new_pattern])

    return patterns


# ---------------------------------------------------------------------------
# Modelo Inteiro Final (MIP)
# ---------------------------------------------------------------------------


def _solve_master_mip(
    patterns: np.ndarray,
    demands: list[int],
    solver: str,
) -> tuple[float, list[float]]:
    """Resolve o Problema Mestre Inteiro com todas as colunas geradas.

    Args:
        patterns: Matriz de padrões (m × K) resultante da Geração de Colunas.
        demands: Lista de demandas por tipo de peça.
        solver: Nome do solver Pyomo.

    Returns:
        Tupla (objetivo, quantidades) — rolos cortados e uso de cada padrão.
    """
    m, n_cols = patterns.shape
    model = pyo.ConcreteModel(name="Mestre_MIP")

    model.M = pyo.RangeSet(1, m)
    model.N = pyo.RangeSet(1, n_cols)

    # Variáveis inteiras não negativas
    model.x = pyo.Var(model.N, within=pyo.NonNegativeIntegers)

    model.a = pyo.Param(
        model.M,
        model.N,
        initialize=lambda _, i, j: float(patterns[i - 1, j - 1]),
    )
    model.d = pyo.Param(
        model.M,
        initialize=lambda _, i: float(demands[i - 1]),
    )

    # Minimizar total de rolos cortados
    model.obj = pyo.Objective(
        expr=sum(model.x[j] for j in model.N),
        sense=pyo.minimize,
    )

    # Atender toda a demanda
    model.rest_demanda = pyo.Constraint(
        model.M,
        rule=lambda mod, i: sum(mod.a[i, j] * mod.x[j] for j in mod.N)
        >= mod.d[i],
    )

    opt = pyo.SolverFactory(solver)
    results = opt.solve(model, tee=False)

    status = str(results.solver.termination_condition)
    obj_val = float(pyo.value(model.obj))
    quantities = [float(pyo.value(model.x[j])) for j in model.N]

    return obj_val, quantities, status


# ---------------------------------------------------------------------------
# Interface principal
# ---------------------------------------------------------------------------


def solve(
    instance: CuttingStockInstance,
    solver: str = "appsi_highs",
    verbose: bool = False,
) -> CuttingStockSolution:
    """Resolve o Problema de Corte de Estoque 1D via Geração de Colunas.

    Executa:
        1. Geração de Colunas (LP relaxado iterativo + mochila inteira).
        2. Resolução do Mestre Inteiro (MIP) com todas as colunas geradas.

    Args:
        instance: Dados da instância (rolo-mestre, larguras e demandas).
        solver: Nome do solver Pyomo.
            Padrão: ``"appsi_highs"`` (HiGHS — open-source, recomendado).
            Alternativas: ``"glpk"``, ``"cbc"``, ``"scip"``.
        verbose: Se ``True``, exibe log de progresso no terminal.

    Returns:
        CuttingStockSolution com o número de rolos cortados e os padrões usados.

    Raises:
        RuntimeError: Se o solver falhar ao resolver o MIP final.

    Example:
        >>> inst = CuttingStockInstance.from_json("instances/small_3.json")
        >>> sol = solve(inst)
        >>> print(f"Rolos cortados: {sol.n_rolls_cut}")
    """
    if verbose:
        print(f"[CG] Iniciando Geração de Colunas para '{instance.name}'...")

    # Passo 1: Geração de Colunas
    patterns = _column_generation(instance, solver)

    if verbose:
        print(f"[CG] Convergido com {patterns.shape[1]} padrões.")
        print("[MIP] Resolvendo Mestre Inteiro...")

    # Passo 2: MIP final
    obj_val, quantities, status = _solve_master_mip(
        patterns, instance.demands, solver
    )

    if verbose:
        print(f"[MIP] Rolos cortados: {obj_val:.0f}  |  Status: {status}")

    return CuttingStockSolution(
        n_rolls_cut=obj_val,
        patterns=patterns.tolist(),
        quantities=quantities,
        solver_status=status,
    )


# ---------------------------------------------------------------------------
# Execução standalone
# ---------------------------------------------------------------------------


def _print_solution(
    instance: CuttingStockInstance, sol: CuttingStockSolution
) -> None:
    """Imprime o resumo da solução no terminal."""
    print(f"\nInstância    : {instance.name}")
    print(f"Rolo-mestre  : {instance.master_roll}")
    print(f"Tipos de peça: {instance.n_items}")
    print("-" * 45)
    print(f"Status       : {sol.solver_status}")
    print(f"Padrões ger. : {sol.n_patterns}")
    print(f"Rolos cortad.: {sol.n_rolls_cut:.0f}")
    print("\nUso dos padrões:")
    patterns = np.array(sol.patterns)
    for j, qty in enumerate(sol.quantities):
        if qty > 0.5:
            print(f"  Padrão {j + 1:2d} (usado {qty:.0f}×): {patterns[:, j].astype(int).tolist()}")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "instances/small_3.json"
    inst = CuttingStockInstance.from_json(Path(path))
    solution = solve(inst, verbose=True)
    _print_solution(inst, solution)
