"""Estruturas de dados compartilhadas -- Problema de Transporte.

Este modulo define os tipos de dados utilizados por todos os modelos
do Problema de Transporte Classico (model_pyomo.py, model_gurobi.py, etc.).

Uso tipico:
    from instance import TransportInstance
    inst = TransportInstance.from_json("instances/small_3x4.json")
    print(inst.m, inst.n)  # fornecedores, clientes
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Supplier:
    """Fornecedor com oferta disponivel."""
    id: int
    supply: float


@dataclass
class Customer:
    """Cliente com demanda a satisfazer."""
    id: int
    demand: float


@dataclass
class TransportInstance:
    """Dados completos de uma instancia do Problema de Transporte.

    Attributes:
        name: Nome descritivo.
        suppliers: Lista de fornecedores.
        customers: Lista de clientes.
        costs: Matriz de custos costs[i][j] = custo de fornecedor i para cliente j.
    """
    name: str
    suppliers: list[Supplier] = field(default_factory=list)
    customers: list[Customer] = field(default_factory=list)
    costs: list[list[float]] = field(default_factory=list)

    @property
    def m(self) -> int:
        return len(self.suppliers)

    @property
    def n(self) -> int:
        return len(self.customers)

    @classmethod
    def from_json(cls, path: Path | str) -> "TransportInstance":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        suppliers = [Supplier(**s) for s in data["suppliers"]]
        customers = [Customer(**c) for c in data["customers"]]
        return cls(
            name=data["name"],
            suppliers=suppliers,
            customers=customers,
            costs=data["costs"],
        )
