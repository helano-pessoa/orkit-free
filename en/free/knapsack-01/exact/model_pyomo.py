"""0/1 Knapsack — Pyomo Model (Binary Integer Programming).

Formulation:

    max  Σᵢ pᵢ xᵢ
    s.t. Σᵢ wᵢ xᵢ ≤ C
         xᵢ ∈ {0, 1},  ∀ i ∈ I

Supported solvers (via `solver` argument):
    "appsi_highs"  — HiGHS (default, open-source, recommended)
    "glpk"         — GLPK  (didactic, small examples)
    "cbc"          — CBC   (alternative fallback)
    "scip"         — SCIP  (hard instances)

Dependencies:
    pip install pyomo highspy

References:
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
    """Build the Pyomo model for the 0/1 Knapsack problem.

    Uses ConcreteModel: all data is provided directly,
    without needing AbstractModel + DataPortal.

    Args:
        instance: Problem instance with capacity and item list.

    Returns:
        Pyomo model ready to be solved.

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
        doc="Set of available items",
    )

    # --- Parameters ---
    model.p = pyo.Param(
        model.I,
        initialize={item.id: item.profit for item in instance.items},
        doc="Profit of item i",
    )
    model.w = pyo.Param(
        model.I,
        initialize={item.id: item.weight for item in instance.items},
        doc="Weight of item i",
    )
    model.C = pyo.Param(
        initialize=instance.capacity,
        doc="Maximum knapsack capacity",
    )

    # --- Decision variables ---
    model.x = pyo.Var(
        model.I,
        within=pyo.Binary,
        doc="x[i] = 1 if item i is selected, 0 otherwise",
    )

    # --- Objective function ---
    model.obj = pyo.Objective(
        expr=pyo.summation(model.p, model.x),
        sense=pyo.maximize,
        doc="Maximize total profit of selected items",
    )

    # --- Constraints ---
    model.rest_capacidade = pyo.Constraint(
        expr=pyo.summation(model.w, model.x) <= model.C,
        doc="Total weight must not exceed knapsack capacity",
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
    """Solve a 0/1 Knapsack instance.

    Args:
        instance: Problem data (capacity and items).
        solver: Pyomo solver name.
            Default: ``"appsi_highs"`` (HiGHS — open-source, recommended).
            Alternatives: ``"glpk"``, ``"cbc"``, ``"scip"``.
        verbose: If ``True``, stream solver log to stdout.

    Returns:
        KnapsackSolution with selected items and optimal profit.

    Raises:
        RuntimeError: If the solver does not find an optimal or feasible solution.

    Example:
        >>> inst = KnapsackInstance.from_json("instances/small_5.json")
        >>> sol = solve(inst)
        >>> print(f"Optimal profit: {sol.total_profit}")
        Optimal profit: 40.0
    """
    model = build_model(instance)
    opt = pyo.SolverFactory(solver)
    results = opt.solve(model, tee=verbose)

    status = str(results.solver.termination_condition)
    if status not in {"optimal", "feasible"}:
        raise RuntimeError(
            f"Solver terminated with status '{status}'. "
            "Verify that the solver is installed and the instance is valid."
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
    """Print a formatted solution summary to stdout."""
    print(f"\nInstance   : {instance.name}")
    print(f"Items      : {instance.n_items}   |   Capacity: {instance.capacity}")
    print("-" * 45)
    print(f"Status     : {sol.solver_status}")
    print(f"Selected   : {sol.selected_items}")
    print(f"Tot. weight: {sol.total_weight}")
    print(f"Tot. profit: {sol.total_profit}")

    if instance.optimal_value is not None:
        gap = sol.gap_to_optimal(instance.optimal_value)
        print(f"Gap        : {gap:.2f}%  (reference: {instance.optimal_value})")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "instances/small_5.json"
    inst = KnapsackInstance.from_json(Path(path))
    solution = solve(inst, verbose=False)
    _print_solution(inst, solution)
