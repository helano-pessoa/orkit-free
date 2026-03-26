"""Problema de Transporte -- GRASP.

Fase de construcao:
    Aloca demandas usando rota de menor custo, com aleatoriedade
    controlada por alpha (RCL baseada em custo).

Fase de busca local:
    Tenta realocar fluxo entre rotas para reduzir o custo total.

Dependencias: nenhuma (stdlib apenas)

Referencias:
    Feo, Resende (1995). Journal of Global Optimization, 6(2), 109-133.
"""

from __future__ import annotations

import json
import random
import sys
from copy import deepcopy


def carregar(caminho: str) -> dict:
    with open(caminho, encoding="utf-8") as fh:
        return json.load(fh)


def custo_total(x: list[list[float]], costs: list[list[float]]) -> float:
    return sum(costs[i][j] * x[i][j] for i in range(len(x)) for j in range(len(x[0])))


def construcao(
    supply: list[float],
    demand: list[float],
    costs: list[list[float]],
    alpha: float = 0.2,
) -> list[list[float]]:
    """Construcao GRASP: aloca por custo minimo com RCL."""
    m, n = len(supply), len(demand)
    x = [[0.0] * n for _ in range(m)]
    s = supply[:]
    d = demand[:]

    arcos = [(i, j) for i in range(m) for j in range(n)]

    while any(d[j] > 1e-9 for j in range(n)):
        # Candidatos: rotas com oferta e demanda disponiveis
        candidatos = [(i, j) for (i, j) in arcos if s[i] > 1e-9 and d[j] > 1e-9]
        if not candidatos:
            break
        custos_cand = [costs[i][j] for i, j in candidatos]
        c_min, c_max = min(custos_cand), max(custos_cand)
        limite = c_min + alpha * (c_max - c_min)
        rcl = [(i, j) for (i, j), c in zip(candidatos, custos_cand) if c <= limite]

        i, j = random.choice(rcl)
        amt = min(s[i], d[j])
        x[i][j] += amt
        s[i] -= amt
        d[j] -= amt

    return x


def busca_local(
    x: list[list[float]],
    costs: list[list[float]],
    supply: list[float],
    demand: list[float],
) -> list[list[float]]:
    """Tenta mover fluxo entre rotas para reduzir custo total."""
    m, n = len(x), len(x[0])
    melhorou = True
    while melhorou:
        melhorou = False
        custo_atual = custo_total(x, costs)
        for i1 in range(m):
            for j1 in range(n):
                if x[i1][j1] < 1e-9:
                    continue
                for j2 in range(n):
                    if j2 == j1:
                        continue
                    # Tenta mover fluxo de (i1,j1) para (i1,j2)
                    # Precisa de rota (i?,j1) que absorva
                    for i2 in range(m):
                        if i2 == i1:
                            continue
                        delta = min(x[i1][j1], x[i2][j2]) if x[i2][j2] > 1e-9 else 0
                        if delta < 1e-9:
                            continue
                        novo = deepcopy(x)
                        novo[i1][j1] -= delta
                        novo[i2][j2] -= delta
                        novo[i1][j2] += delta
                        novo[i2][j1] += delta
                        if custo_total(novo, costs) < custo_atual - 1e-9:
                            x = novo
                            custo_atual = custo_total(x, costs)
                            melhorou = True
                            break
                    if melhorou:
                        break
                if melhorou:
                    break
            if melhorou:
                break
    return x


def grasp(
    supply: list[float],
    demand: list[float],
    costs: list[list[float]],
    n_iter: int = 30,
    alpha: float = 0.2,
) -> tuple[list[list[float]], float]:
    """Executa GRASP para o Problema de Transporte."""
    melhor = None
    melhor_custo = float("inf")

    for _ in range(n_iter):
        sol = construcao(supply, demand, costs, alpha)
        sol = busca_local(sol, costs, supply, demand)
        c = custo_total(sol, costs)
        if c < melhor_custo:
            melhor = deepcopy(sol)
            melhor_custo = c

    return melhor, melhor_custo


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "../instances/small_3x4.json"
    dados = carregar(path)
    supply = [s["supply"] for s in dados["suppliers"]]
    demand = [c["demand"] for c in dados["customers"]]
    costs = dados["costs"]

    random.seed(42)
    sol, custo = grasp(supply, demand, costs)
    print(f"GRASP -- Custo: {custo:.2f}")
    for i, row in enumerate(sol):
        for j, v in enumerate(row):
            if v > 1e-9:
                print(f"  x[{i+1},{j+1}] = {v:.1f}")
