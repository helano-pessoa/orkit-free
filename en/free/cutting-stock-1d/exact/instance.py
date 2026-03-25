"""Shared data structures for the 1D Cutting Stock Problem.

This module defines the data types used by model_pyomo.py
and model_gurobi.py for the 1D Cutting Stock Problem.

Typical usage:
    from instance import CuttingStockInstance, CuttingStockSolution

    inst = CuttingStockInstance.from_json("instances/small_3.json")
    print(inst.master_roll, inst.n_items)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ItemType:
    """Represents a piece type to be cut from the master roll.

    Attributes:
        id: Unique identifier for this piece type.
        width: Piece width (same units as master roll).
        demand: Minimum quantity required.
    """

    id: int
    width: float
    demand: int


@dataclass
class CuttingStockInstance:
    """Full data for a 1D Cutting Stock Problem instance.

    Attributes:
        name: Descriptive name for the instance.
        master_roll: Master roll width (W).
        items: List of piece types with width and demand.
    """

    name: str
    master_roll: float
    items: list[ItemType] = field(default_factory=list)

    @classmethod
    def from_json(cls, path: str | Path) -> "CuttingStockInstance":
        """Load an instance from a JSON file.

        Args:
            path: Path to the JSON instance file.

        Returns:
            Populated CuttingStockInstance object.

        Raises:
            FileNotFoundError: If the file does not exist.
            KeyError: If the JSON is missing required fields.

        Example:
            >>> inst = CuttingStockInstance.from_json("instances/small_3.json")
            >>> print(inst.master_roll, inst.n_items)
            100 3
        """
        path = Path(path)
        with path.open(encoding="utf-8") as fh:
            data = json.load(fh)

        items = [
            ItemType(id=it["id"], width=it["width"], demand=it["demand"])
            for it in data["items"]
        ]
        return cls(
            name=data["name"],
            master_roll=data["master_roll"],
            items=items,
        )

    @property
    def n_items(self) -> int:
        """Number of item types in the instance."""
        return len(self.items)

    @property
    def widths(self) -> list[float]:
        """List of widths in item order."""
        return [it.width for it in self.items]

    @property
    def demands(self) -> list[int]:
        """List of demands in item order."""
        return [it.demand for it in self.items]


@dataclass
class CuttingStockSolution:
    """Solution to the 1D Cutting Stock Problem.

    Attributes:
        n_rolls_cut: Total number of master rolls cut.
        patterns: Pattern matrix (m × K) — patterns[i][j] = number of items
            of type i in pattern j.
        quantities: Number of times each pattern is used.
        solver_status: Solver termination status.
    """

    n_rolls_cut: float
    patterns: list[list[float]]
    quantities: list[float]
    solver_status: str

    @property
    def n_patterns(self) -> int:
        """Number of cutting patterns generated."""
        return len(self.quantities)
