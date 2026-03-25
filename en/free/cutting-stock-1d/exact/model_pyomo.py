"""1D Cutting Stock Problem — Column Generation with Pyomo + HiGHS.

Algorithm (Gilmore & Gomory, 1961):
    1. Initialize with trivial patterns (one item type per pattern).
    2. Solve the LP-relaxed Master Problem → get shadow prices π.
    3. Solve the Subproblem (Integer Knapsack) with profits π.
    4. If z* > 1 + ε, add new column and go to step 2.
    5. Solve the Integer Master (MIP) with all generated columns.

Supported solvers: "appsi_highs" (default), "glpk", "cbc", "scip".

Dependencies:
    pip install pyomo highspy numpy

References:
    Gilmore, P. C., Gomory, R. E. (1961). Operations Research, 9(6), 849-859.
    Gilmore, P. C., Gomory, R. E. (1963). Operations Research, 11(6), 863-888.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pyomo.environ as pyo

from instance import CuttingStockInstance, CuttingStockSolution

# Stopping tolerance for Column Generation
_EPSILON = 1.0e-6


# ---------------------------------------------------------------------------
# Problema Mestre (LP relaxado)
# ---------------------------------------------------------------------------


def _solve_master_lp(
    patterns: np.ndarray,
    demands: list[int],
    solver: str,
) -> tuple[list[float], list[float]]:
    """Solve the LP-relaxed Master Problem.

    Args:
        patterns: Cutting pattern matrix (m × K), where patterns[i, j]
            is the number of items of type i in pattern j.
        demands: List of demands per item type.
        solver: Pyomo solver name.

    Returns:
        Tuple (x, pi) where x is the Master LP solution and pi are the
        shadow prices (dual variables) of the demand constraints.
    """
    m, n_cols = patterns.shape
    model = pyo.ConcreteModel(name="Mestre_LP")

    model.M = pyo.RangeSet(1, m)
    model.N = pyo.RangeSet(1, n_cols)

    # Non-negative continuous variables (LP relaxation)
    model.x = pyo.Var(model.N, within=pyo.NonNegativeReals)

    # Parameters: patterns and demands
    model.a = pyo.Param(
        model.M,
        model.N,
        initialize=lambda _, i, j: float(patterns[i - 1, j - 1]),
    )
    model.d = pyo.Param(
        model.M,
        initialize=lambda _, i: float(demands[i - 1]),
    )

    # Objective: minimize total master rolls cut
    model.obj = pyo.Objective(
        expr=sum(model.x[j] for j in model.N),
        sense=pyo.minimize,
    )

    # Demand constraints: each type must be satisfied
    model.rest_demanda = pyo.Constraint(
        model.M,
        rule=lambda mod, i: sum(mod.a[i, j] * mod.x[j] for j in mod.N)
        >= mod.d[i],
    )

    # Suffix to extract dual variables
    model.dual = pyo.Suffix(direction=pyo.Suffix.IMPORT)

    opt = pyo.SolverFactory(solver)
    opt.solve(model, tee=False)

    x_vals = [pyo.value(model.x[j]) for j in model.N]
    # Shadow prices in the order of demand constraints (1..m)
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
    """Solve the Subproblem: Integer Knapsack with shadow prices as profits.

    Identifies the most negative reduced-cost pattern. If z* > 1,
    the pattern is promising and should be added to the Master.

    Args:
        widths: Widths of item types.
        shadow_prices: Shadow prices (π) of demand constraints.
        master_roll: Master roll width.
        solver: Pyomo solver name.

    Returns:
        Tuple (z_star, new_pattern) — optimal value and new cutting pattern.
    """
    m = len(widths)
    model = pyo.ConcreteModel(name="Sub_Mochila")

    model.M = pyo.RangeSet(1, m)

    # Non-negative integer decision variables
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

    # Maximize the reduced cost (shadow price × quantity)
    model.obj = pyo.Objective(
        expr=sum(model.pi[i] * model.y[i] for i in model.M),
        sense=pyo.maximize,
    )

    # Capacity constraint: pattern must fit within master roll
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
    """Run Column Generation and return the final pattern matrix.

    Starts with trivial patterns (one item type per pattern) and iterates
    until no improving pattern is found.

    Args:
        instance: Problem instance data.
        solver: Pyomo solver name.

    Returns:
        Pattern matrix (m × K) after convergence.
    """
    m = instance.n_items
    widths = instance.widths
    demands = instance.demands

    # Trivial initial patterns (diagonal: max items per type per roll)
    max_per_item = [int(instance.master_roll // w) for w in widths]
    patterns = np.diag(max_per_item).astype(float)

    while True:
        _, shadow_prices = _solve_master_lp(patterns, demands, solver)
        z_star, new_pattern = _solve_subproblem(
            widths, shadow_prices, instance.master_roll, solver
        )

        # Stopping criterion: no pattern improves the solution
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
    """Solve the Integer Master Problem with all generated columns.

    Args:
        patterns: Pattern matrix (m × K) from Column Generation.
        demands: List of demands per item type.
        solver: Pyomo solver name.

    Returns:
        Tuple (objective, quantities) — rolls cut and usage per pattern.
    """
    m, n_cols = patterns.shape
    model = pyo.ConcreteModel(name="Mestre_MIP")

    model.M = pyo.RangeSet(1, m)
    model.N = pyo.RangeSet(1, n_cols)

    # Non-negative integer decision variables
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

    # Minimize total master rolls cut
    model.obj = pyo.Objective(
        expr=sum(model.x[j] for j in model.N),
        sense=pyo.minimize,
    )

    # Meet all demand
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
    """Solve the 1D Cutting Stock Problem via Column Generation.

    Steps:
        1. Column Generation (iterative LP relaxation + integer knapsack).
        2. Integer Master (MIP) resolution with all generated columns.

    Args:
        instance: Instance data (master roll, widths, and demands).
        solver: Pyomo solver name.
            Default: ``"appsi_highs"`` (HiGHS — open-source, recommended).
            Alternatives: ``"glpk"``, ``"cbc"``, ``"scip"``.
        verbose: If ``True``, prints progress log to the terminal.

    Returns:
        CuttingStockSolution with number of rolls cut and patterns used.

    Raises:
        RuntimeError: If the solver fails to solve the final MIP.

    Example:
        >>> inst = CuttingStockInstance.from_json("instances/small_3.json")
        >>> sol = solve(inst)
        >>> print(f"Rolls cut: {sol.n_rolls_cut}")
    """
    if verbose:
        print(f"[CG] Starting Column Generation for '{instance.name}'...")

    # Passo 1: Geração de Colunas
    patterns = _column_generation(instance, solver)

    if verbose:
        print(f"[CG] Converged with {patterns.shape[1]} patterns.")
        print("[MIP] Solving Integer Master...")

    # Passo 2: MIP final
    obj_val, quantities, status = _solve_master_mip(
        patterns, instance.demands, solver
    )

    if verbose:
        print(f"[MIP] Rolls cut: {obj_val:.0f}  |  Status: {status}")

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
    """Print solution summary to the terminal."""
    print(f"\nInstance     : {instance.name}")
    print(f"Master roll  : {instance.master_roll}")
    print(f"Item types   : {instance.n_items}")
    print("-" * 45)
    print(f"Status       : {sol.solver_status}")
    print(f"Patterns gen.: {sol.n_patterns}")
    print(f"Rolls cut    : {sol.n_rolls_cut:.0f}")
    print("\nPattern usage:")
    patterns = np.array(sol.patterns)
    for j, qty in enumerate(sol.quantities):
        if qty > 0.5:
            print(f"  Pattern {j + 1:2d} (used {qty:.0f}×): {patterns[:, j].astype(int).tolist()}")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "instances/small_3.json"
    inst = CuttingStockInstance.from_json(Path(path))
    solution = solve(inst, verbose=True)
    _print_solution(inst, solution)
