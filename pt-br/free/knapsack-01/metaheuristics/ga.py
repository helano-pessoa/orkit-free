"""Mochila 0/1 -- Algoritmo Genetico (GA).

Representacao do cromossomo:
    Vetor binario de comprimento n_itens.
    Cromossomo sao filhos de x[i] in {0,1}.

Operadores:
    Selecao: torneio binario
    Cruzamento: ponto unico
    Mutacao: flip de um bit (com reparacao de capacidade)

Dependencias: nenhuma (stdlib apenas)

Referencias:
    Holland, J. H. (1975). Adaptation in Natural and Artificial Systems. MIT Press.
"""

from __future__ import annotations

import json
import random
import sys
from copy import deepcopy


def carregar(caminho: str) -> dict:
    with open(caminho, encoding="utf-8") as fh:
        return json.load(fh)


def lucro_total(x: list[int], profits: list[float]) -> float:
    return sum(p * xi for p, xi in zip(profits, x))


def peso_total(x: list[int], weights: list[float]) -> float:
    return sum(w * xi for w, xi in zip(weights, x))


def reparar(x: list[int], weights: list[float], profits: list[float], C: float) -> list[int]:
    x = x[:]
    ordem = sorted(range(len(x)), key=lambda i: profits[i] / max(weights[i], 1e-9))
    for i in ordem:
        if peso_total(x, weights) <= C:
            break
        if x[i] == 1:
            x[i] = 0
    return x


def fitness(x: list[int], weights: list[float], profits: list[float], C: float) -> float:
    """Fitness = lucro (penalizado se infactivel)."""
    peso = peso_total(x, weights)
    if peso > C:
        return lucro_total(x, profits) - 1000.0 * (peso - C)
    return lucro_total(x, profits)


def torneio(pop: list[list[int]], fits: list[float], k: int = 2) -> list[int]:
    concorrentes = random.sample(range(len(pop)), k)
    vencedor = max(concorrentes, key=lambda j: fits[j])
    return pop[vencedor][:]


def cruzamento(p1: list[int], p2: list[int]) -> tuple[list[int], list[int]]:
    n = len(p1)
    pt = random.randint(1, n - 1)
    return p1[:pt] + p2[pt:], p2[:pt] + p1[pt:]


def mutacao(x: list[int], taxa: float = 0.05) -> list[int]:
    return [1 - xi if random.random() < taxa else xi for xi in x]


def genetico(
    C: float,
    weights: list[float],
    profits: list[float],
    pop_size: int = 50,
    n_geracoes: int = 200,
    taxa_mutacao: float = 0.05,
) -> tuple[list[int], float]:
    """Executa GA para a Mochila 0/1.

    Returns:
        (melhor_solucao, melhor_lucro)
    """
    n = len(weights)

    # Populacao inicial: guloso + aleatorio
    def individuo_guloso():
        ordem = sorted(range(n), key=lambda i: profits[i] / max(weights[i], 1e-9), reverse=True)
        x = [0] * n
        cap = C
        for i in ordem:
            if weights[i] <= cap:
                x[i] = 1
                cap -= weights[i]
        return x

    pop = [individuo_guloso()]
    while len(pop) < pop_size:
        pop.append([random.randint(0, 1) for _ in range(n)])

    melhor = None
    melhor_lucro = -float("inf")

    for _ in range(n_geracoes):
        pop = [reparar(c, weights, profits, C) for c in pop]
        fits = [fitness(c, weights, profits, C) for c in pop]

        idx_melhor = max(range(len(pop)), key=lambda j: fits[j])
        if fits[idx_melhor] > melhor_lucro:
            melhor_lucro = fits[idx_melhor]
            melhor = pop[idx_melhor][:]

        nova_pop = [melhor[:]]  # elitismo
        while len(nova_pop) < pop_size:
            p1 = torneio(pop, fits)
            p2 = torneio(pop, fits)
            f1, f2 = cruzamento(p1, p2)
            nova_pop.append(mutacao(f1, taxa_mutacao))
            if len(nova_pop) < pop_size:
                nova_pop.append(mutacao(f2, taxa_mutacao))
        pop = nova_pop

    return melhor, lucro_total(melhor, profits)


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "../instances/small_5.json"
    dados = carregar(path)
    C = dados["capacity"]
    weights = [it["weight"] for it in dados["items"]]
    profits = [it["profit"] for it in dados["items"]]
    ids = [it["id"] for it in dados["items"]]

    random.seed(42)
    solucao, lucro = genetico(C, weights, profits)
    selecionados = [ids[i] for i, xi in enumerate(solucao) if xi == 1]
    print(f"GA — Lucro: {lucro:.0f} | Itens: {selecionados}")
