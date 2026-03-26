"""
Transportation Problem -- instance data model.

JSON format expected::

    {
        "name": "...",
        "suppliers": [{"id": 1, "supply": 120}, ...],
        "customers": [{"id": 1, "demand": 70}, ...],
        "costs": [[2, 3, 1, 5], ...]
    }
"""
from __future__ import annotations
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class Supplier:
    id: int
    supply: float


@dataclass
class Customer:
    id: int
    demand: float


@dataclass
class TransportInstance:
    name: str
    suppliers: List[Supplier]
    customers: List[Customer]
    costs: List[List[float]] = field(default_factory=list)

    @property
    def m(self) -> int:
        """Number of suppliers."""
        return len(self.suppliers)

    @property
    def n(self) -> int:
        """Number of customers."""
        return len(self.customers)

    @classmethod
    def from_json(cls, path: str | Path) -> "TransportInstance":
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        suppliers = [Supplier(**s) for s in data["suppliers"]]
        customers = [Customer(**c) for c in data["customers"]]
        return cls(
            name=data.get("name", Path(path).stem),
            suppliers=suppliers,
            customers=customers,
            costs=data["costs"],
        )
