"""Problema de Transporte -- Simulated Annealing (SA).

Representacao da solucao:
    Matriz x[i][j] >= 0 (quantidades transportadas).
    Inicializacao: metodo do canto noroeste.

Perturbacao:
    Seleciona dois pares (i1,j1) e (i2,j2) e transfere uma quantidade
    delta (aleatoria) de x[i1,j1] para x[i1,j2] e ajusta x[i2,j2]
    e x[i2,j1] para manter factibilidade (ciclo basico).

Dependencias: nenhuma (stdlib apenas)

Referencias:
    Kirkpatrick, Gelatt, Vecchi (1983). Science, 220(4598), 671-680.
"""

from __future__ import annotations

import json
import math
import random
import sys
from copy import deepcopy


def carregar(caminho: str) -> dict:
    with open(caminho, encoding="utf-8") as fh:
        return json.load(fh)


def custo_total(x: list[list[float]], costs: list[list[float]]) -> float:
    return sum(costs[i][j] * x[i][j] for i in range(len(x)) for j in range(len(x[0])))


def inicializar_nw(supply: list[float], demand: list[float]) -> list[list[float]]:
    """Metodo do canto noroeste para solucao inicial factivel."""
    m, n = len(supply), len(demand)
    x = [[0.0] * n for _ in range(m)]
    s = supply[:]
    d = demand[:]
    i = j = 0
    while i < m and j < n:
        amt = min(s[i], d[j])
        x[i][j] = amt
        s[i] -= amt
        d[j] -= amt
        if s[i] < 1e-9:
            i += 1
        else:
            j += 1
    return x


def perturbar(x: list[list[float]], costs: list[list[float]]) -> list[list[float]]:
    """Perturba solucao: rearranja fluxo em um quadrado (i1,j1)-(i1,j2)-(i2,j2)-(i2,j1)."""
    m, n = len(x), len(x[0])
    novo = deepcopy(x)

    for _ in range(50):
        i1, i2 = random.sample(range(m), 2)
        j1, j2 = random.sample(range(n), 2)
        delta = min(novo[i1][j1], novo[i2][j2])
        if delta < 1e-9:
            continue
        delta = random.uniform(0, delta)
        novo[i1][j1] -= delta
        novo[i2][j2] -= delta
        novo[i1][j2] += delta
        novo[i2][j1] += delta
        if all(novo[i][j] >= -1e-9 for i in range(m) for j in range(n)):
            novo = [[max(0.0, v) for v in row] for row in novo]
            return novo
        # Reverte
        novo[i1][j1] += delta
        novo[i2][j2] += delta
        novo[i1][j2] -= delta
        novo[i2][j1] -= delta

    return x


def simulated_annealing(
    supply: list[float],
    demand: list[float],
    costs: list[list[float]],
    T0: float = 50.0,
    alpha: float = 0.99,
    iter_por_temp: int = 100,
    paradas: int = 300,
) -> tuple[list[list[float]], float]:
    """Executa SA para o Problema de Transporte.

    Returns:
        (melhor_solucao, melhor_custo)
    """
    atual = inicializar_nw(supply, demand)
    melhor = deepcopy(atual)
    melhor_custo = custo_total(melhor, costs)
    T = T0

    for _ in range(paradas):
        for _ in range(iter_por_temp):
            vizinho = perturbar(atual, costs)
            delta = custo_total(vizinho, costs) - custo_total(atual, costs)
            if delta < 0 or random.random() < math.exp(-delta / max(T, 1e-10)):
                atual = vizinho
                if custo_total(atual, costs) < melhor_custo:
                    melhor = deepcopy(atual)
                    melhor_custo = custo_total(melhor, costs)
        T *= alpha

    return melhor, melhor_custo


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "../instances/small_3x4.json"
    dados = carregar(path)
    supply = [s["supply"] for s in dados["suppliers"]]
    demand = [c["demand"] for c in dados["customers"]]
    costs = dados["costs"]

    random.seed(42)
    sol, custo = simulated_annealing(supply, demand, costs)
    print(f"SA -- Custo: {custo:.2f}")
    for i, row in enumerate(sol):
        for j, v in enumerate(row):
            if v > 1e-9:
                print(f"  x[{i+1},{j+1}] = {v:.1f}")
