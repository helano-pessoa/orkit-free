"""Shared data structures — 0/1 Knapsack Problem.

This module defines the data types used by all models for the
0/1 Knapsack problem (model_pyomo.py, model_gurobi.py).

Typical usage:
    from instance import Item, KnapsackInstance, KnapsackSolution

    inst = KnapsackInstance.from_json("instances/small_5.json")
    print(inst.n_items, inst.capacity)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Item:
    """Represents an item available for selection in the knapsack.

    Attributes:
        id: Unique item identifier (positive integer).
        weight: Item weight (same unit as capacity).
        profit: Profit gained by selecting the item.
    """

    id: int
    weight: float
    profit: float


@dataclass
class KnapsackInstance:
    """Complete data for a 0/1 Knapsack problem instance.

    Attributes:
        name: Descriptive name of the instance.
        capacity: Maximum knapsack capacity.
        items: List of available items.
        optimal_value: Known optimal value (None if unknown).
    """

    name: str
    capacity: float
    items: list[Item] = field(default_factory=list)
    optimal_value: float | None = None

    @classmethod
    def from_json(cls, path: str | Path) -> "KnapsackInstance":
        """Load an instance from a JSON file.

        Args:
            path: Path to the instance JSON file.

        Returns:
            Populated KnapsackInstance object.

        Raises:
            FileNotFoundError: If the file does not exist.
            KeyError: If the JSON is missing required fields.

        Example:
            >>> inst = KnapsackInstance.from_json("instances/small_5.json")
            >>> print(inst.capacity, inst.n_items)
            10 5
        """
        path = Path(path)
        with path.open(encoding="utf-8") as fh:
            data = json.load(fh)

        items = [
            Item(id=it["id"], weight=it["weight"], profit=it["profit"])
            for it in data["items"]
        ]
        return cls(
            name=data["name"],
            capacity=data["capacity"],
            items=items,
            optimal_value=data.get("optimal_value"),
        )

    @property
    def n_items(self) -> int:
        """Total number of items in the instance."""
        return len(self.items)


@dataclass
class KnapsackSolution:
    """Solution to the 0/1 Knapsack problem.

    Attributes:
        selected_items: List of IDs of selected items.
        total_profit: Total profit of the solution.
        total_weight: Total weight of selected items.
        solver_status: Termination status returned by the solver.
    """

    selected_items: list[int]
    total_profit: float
    total_weight: float
    solver_status: str

    def gap_to_optimal(self, optimal: float) -> float:
        """Compute the percentage gap relative to a known optimum.

        Args:
            optimal: Reference optimal value.

        Returns:
            Percentage gap: (optimal - found) / optimal * 100.
        """
        if optimal <= 0:
            return 0.0
        return (optimal - self.total_profit) / optimal * 100.0
