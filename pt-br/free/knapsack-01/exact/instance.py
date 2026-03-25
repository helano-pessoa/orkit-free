"""Estruturas de dados compartilhadas — Mochila 0/1.

Este módulo define os tipos de dados utilizados por todos os modelos
do problema da Mochila 0/1 (model_pyomo.py, model_gurobi.py).

Uso típico:
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
    """Representa um item disponível para seleção na mochila.

    Attributes:
        id: Identificador único do item (inteiro positivo).
        weight: Peso do item (mesma unidade da capacidade).
        profit: Lucro obtido ao selecionar o item.
    """

    id: int
    weight: float
    profit: float


@dataclass
class KnapsackInstance:
    """Dados completos de uma instância do Problema da Mochila 0/1.

    Attributes:
        name: Nome descritivo da instância.
        capacity: Capacidade máxima da mochila.
        items: Lista de itens disponíveis.
        optimal_value: Valor ótimo conhecido (None se desconhecido).
    """

    name: str
    capacity: float
    items: list[Item] = field(default_factory=list)
    optimal_value: float | None = None

    @classmethod
    def from_json(cls, path: str | Path) -> "KnapsackInstance":
        """Carrega uma instância a partir de um arquivo JSON.

        Args:
            path: Caminho para o arquivo JSON da instância.

        Returns:
            Objeto KnapsackInstance populado.

        Raises:
            FileNotFoundError: Se o arquivo não existir.
            KeyError: Se o JSON não contiver os campos obrigatórios.

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
        """Número total de itens na instância."""
        return len(self.items)


@dataclass
class KnapsackSolution:
    """Solução do Problema da Mochila 0/1.

    Attributes:
        selected_items: Lista de IDs dos itens selecionados.
        total_profit: Lucro total da solução.
        total_weight: Peso total dos itens selecionados.
        solver_status: Status de terminação retornado pelo solver.
    """

    selected_items: list[int]
    total_profit: float
    total_weight: float
    solver_status: str

    def gap_to_optimal(self, optimal: float) -> float:
        """Calcula o gap percentual em relação ao ótimo conhecido.

        Args:
            optimal: Valor ótimo de referência.

        Returns:
            Gap percentual: (optimal - found) / optimal * 100.
        """
        if optimal <= 0:
            return 0.0
        return (optimal - self.total_profit) / optimal * 100.0
