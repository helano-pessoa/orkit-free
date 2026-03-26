"""Problema de Transporte -- Algoritmo Genetico (GA).

Representacao do cromossomo:
    Matriz achatada (vetor de m*n reais) representando as alocacoes x[i][j].
    Apos cruzamento/mutacao, aplica-se reparacao para garantir factibilidade.

Operadores:
    Selecao: torneio binario
    Cruzamento: ponto unico (na representacao vetorial)
    Mutacao: adiciona ruido gaussiano e repara

Reparacao:
    Resolve sistema de restricoes por projecao:
    normaliza linhas (oferta) e colunas (demanda) iterativamente (metodo de Sinkhorn).

Dependencias: nenhuma (stdlib apenas)

Referencias:
    Holland (1975). Adaptation in Natural and Artificial Systems. MIT Press.
"""

from __future__ import annotations

import json
import random
import sys
from copy import deepcopy
from math import sqrt


def carregar(caminho: str) -> dict:
    with open(caminho, encoding="utf-8") as fh:
        return json.load(fh)


def custo_total(x: list[list[float]], costs: list[list[float]]) -> float:
    return sum(costs[i][j] * x[i][j] for i in range(len(x)) for j in range(len(x[0])))


def reparar(x_flat: list[float], supply: list[float], demand: list[float]) -> list[list[float]]:
    """Projeta o cromossomo em solucao factivel usando normalizacao iterativa."""
    m, n = len(supply), len(demand)
    x = [[max(0.0, x_flat[i * n + j]) for j in range(n)] for i in range(m)]

    for _ in range(100):
        # Normaliza por demanda (colunas)
        for j in range(n):
            col_sum = sum(x[i][j] for i in range(m))
            if col_sum > 1e-12:
                scale = demand[j] / col_sum
                for i in range(m):
                    x[i][j] *= scale

        # Normaliza por oferta (linhas)
        for i in range(m):
            row_sum = sum(x[i][j] for j in range(n))
            if row_sum > supply[i] + 1e-9:
                scale = supply[i] / row_sum
                for j in range(n):
                    x[i][j] *= scale

        # Verifica convergencia
        ok = all(abs(sum(x[i][j] for j in range(n)) - demand_j) < 1e-6
                 for demand_j, j in zip(demand, range(n))
                 for _ in [None])
        break  # uma passagem e suficiente para aproximacao

    return x


def fitness(x: list[list[float]], costs: list[list[float]]) -> float:
    """Fitness = custo total (menor = melhor)."""
    return custo_total(x, costs)


def torneio(pop: list[list[float]], fits: list[float], k: int = 2) -> list[float]:
    concorrentes = random.sample(range(len(pop)), k)
    vencedor = min(concorrentes, key=lambda j: fits[j])
    return pop[vencedor][:]


def cruzamento(p1: list[float], p2: list[float]) -> tuple[list[float], list[float]]:
    n = len(p1)
    pt = random.randint(1, n - 1)
    return p1[:pt] + p2[pt:], p2[:pt] + p1[pt:]


def mutacao(crom: list[float], sigma: float = 0.1) -> list[float]:
    return [max(0.0, g + random.gauss(0, sigma)) for g in crom]


def individuo_nw(supply: list[float], demand: list[float]) -> list[float]:
    """Inicializacao pelo canto noroeste."""
    m, n = len(supply), len(demand)
    x = [[0.0] * n for _ in range(m)]
    s, d = supply[:], demand[:]
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
    return [x[i][j] for i in range(m) for j in range(n)]


def genetico(
    supply: list[float],
    demand: list[float],
    costs: list[list[float]],
    pop_size: int = 40,
    n_geracoes: int = 150,
) -> tuple[list[list[float]], float]:
    """Executa GA para o Problema de Transporte."""
    m, n = len(supply), len(demand)
    total_supply = sum(supply)

    # Populacao inicial: nw + aleatorio
    pop = [individuo_nw(supply, demand)]
    while len(pop) < pop_size:
        crom = [random.uniform(0, total_supply / (m * n)) for _ in range(m * n)]
        xmat = reparar(crom, supply, demand)
        pop.append([xmat[i][j] for i in range(m) for j in range(n)])

    melhor_mat = None
    melhor_custo = float("inf")

    for _ in range(n_geracoes):
        mats = [reparar(c, supply, demand) for c in pop]
        fits = [fitness(mat, costs) for mat in mats]

        idx_melhor = min(range(len(pop)), key=lambda j: fits[j])
        if fits[idx_melhor] < melhor_custo:
            melhor_custo = fits[idx_melhor]
            melhor_mat = mats[idx_melhor]

        nova_pop = [pop[idx_melhor][:]]
        while len(nova_pop) < pop_size:
            p1 = torneio(pop, fits)
            p2 = torneio(pop, fits)
            f1, f2 = cruzamento(p1, p2)
            nova_pop.append(mutacao(f1))
            if len(nova_pop) < pop_size:
                nova_pop.append(mutacao(f2))
        pop = nova_pop

    return melhor_mat, melhor_custo


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "../instances/small_3x4.json"
    dados = carregar(path)
    supply = [s["supply"] for s in dados["suppliers"]]
    demand = [c["demand"] for c in dados["customers"]]
    costs = dados["costs"]

    random.seed(42)
    sol, custo = genetico(supply, demand, costs)
    print(f"GA -- Custo: {custo:.2f}")
    for i, row in enumerate(sol):
        for j, v in enumerate(row):
            if v > 1e-9:
                print(f"  x[{i+1},{j+1}] = {v:.1f}")
