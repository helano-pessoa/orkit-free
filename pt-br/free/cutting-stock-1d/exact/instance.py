"""Estruturas de dados compartilhadas — Corte de Estoque 1D.

Este módulo define os tipos de dados utilizados por model_pyomo.py
e model_gurobi.py para o Problema de Corte de Estoque 1D.

Uso típico:
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
    """Representa um tipo de peça a ser cortada.

    Attributes:
        id: Identificador único do tipo de peça.
        width: Largura da peça (mesma unidade do rolo-mestre).
        demand: Demanda (quantidade mínima requerida).
    """

    id: int
    width: float
    demand: int


@dataclass
class CuttingStockInstance:
    """Dados completos de uma instância do Problema de Corte de Estoque 1D.

    Attributes:
        name: Nome descritivo da instância.
        master_roll: Largura do rolo-mestre (W).
        items: Lista de tipos de peça com largura e demanda.
    """

    name: str
    master_roll: float
    items: list[ItemType] = field(default_factory=list)

    @classmethod
    def from_json(cls, path: str | Path) -> "CuttingStockInstance":
        """Carrega uma instância a partir de um arquivo JSON.

        Args:
            path: Caminho para o arquivo JSON da instância.

        Returns:
            Objeto CuttingStockInstance populado.

        Raises:
            FileNotFoundError: Se o arquivo não existir.
            KeyError: Se o JSON não contiver os campos obrigatórios.

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
        """Número de tipos de peça na instância."""
        return len(self.items)

    @property
    def widths(self) -> list[float]:
        """Lista de larguras na ordem dos itens."""
        return [it.width for it in self.items]

    @property
    def demands(self) -> list[int]:
        """Lista de demandas na ordem dos itens."""
        return [it.demand for it in self.items]


@dataclass
class CuttingStockSolution:
    """Solução do Problema de Corte de Estoque 1D.

    Attributes:
        n_rolls_cut: Número total de rolos-mestre cortados.
        patterns: Matriz de padrões (m × K) — patterns[i][j] = nº de peças
            do tipo i no padrão j.
        quantities: Quantidade de vezes que cada padrão é usado.
        solver_status: Status de terminação do solver.
    """

    n_rolls_cut: float
    patterns: list[list[float]]
    quantities: list[float]
    solver_status: str

    @property
    def n_patterns(self) -> int:
        """Número de padrões de corte gerados."""
        return len(self.quantities)
