"""Mochila 0/1 -- Simulated Annealing (SA).

Representacao da solucao:
    Vetor binario x onde x[i] in {0,1} indica se o item i foi selecionado.

Perturbacao:
    - Flip aleatorio: inverte o bit de um item aleatorio (insercao/remocao).
    - Se apos o flip a mochila estiver cheia demais, remove itens de menor
      razao lucro/peso ate restabelecer factibilidade.

Dependencias: nenhuma (stdlib apenas)

Referencias:
    Kirkpatrick, S., Gelatt, C. D., Vecchi, M. P. (1983). Optimization by
    Simulated Annealing. Science, 220(4598), 671-680.
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


def lucro_total(x: list[int], profits: list[float]) -> float:
    return sum(p * xi for p, xi in zip(profits, x))


def peso_total(x: list[int], weights: list[float]) -> float:
    return sum(w * xi for w, xi in zip(weights, x))


def reparar(x: list[int], weights: list[float], profits: list[float], C: float) -> list[int]:
    """Remove itens com menor razao lucro/peso ate a solucao ser factivel."""
    x = x[:]
    ordem = sorted(range(len(x)), key=lambda i: (profits[i] / max(weights[i], 1e-9)))
    for i in ordem:
        if peso_total(x, weights) <= C:
            break
        if x[i] == 1:
            x[i] = 0
    return x


def perturbar(x: list[int], weights: list[float], profits: list[float], C: float) -> list[int]:
    """Inverte um bit aleatorio e repara se necessario."""
    novo = x[:]
    idx = random.randrange(len(novo))
    novo[idx] = 1 - novo[idx]
    if peso_total(novo, weights) > C:
        novo = reparar(novo, weights, profits, C)
    return novo


def simulated_annealing(
    C: float,
    weights: list[float],
    profits: list[float],
    T0: float = 10.0,
    alpha: float = 0.99,
    iter_por_temp: int = 100,
    paradas: int = 300,
) -> tuple[list[int], float]:
    """Executa SA para a Mochila 0/1.

    Args:
        C: Capacidade da mochila.
        weights: Lista de pesos.
        profits: Lista de lucros.
        T0: Temperatura inicial.
        alpha: Taxa de resfriamento.
        iter_por_temp: Iteracoes por temperatura.
        paradas: Numero de reducoes de temperatura.

    Returns:
        (melhor_solucao, melhor_lucro)
    """
    n = len(weights)
    # Inicializacao gulosa: itens ordenados por razao lucro/peso
    ordem = sorted(range(n), key=lambda i: profits[i] / max(weights[i], 1e-9), reverse=True)
    atual = [0] * n
    cap_restante = C
    for i in ordem:
        if weights[i] <= cap_restante:
            atual[i] = 1
            cap_restante -= weights[i]

    melhor = atual[:]
    melhor_lucro = lucro_total(melhor, profits)
    T = T0

    for _ in range(paradas):
        for _ in range(iter_por_temp):
            vizinho = perturbar(atual, weights, profits, C)
            delta = lucro_total(vizinho, profits) - lucro_total(atual, profits)
            if delta > 0 or random.random() < math.exp(delta / max(T, 1e-10)):
                atual = vizinho
                if lucro_total(atual, profits) > melhor_lucro:
                    melhor = atual[:]
                    melhor_lucro = lucro_total(melhor, profits)
        T *= alpha

    return melhor, melhor_lucro


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "../instances/small_5.json"
    dados = carregar(path)
    C = dados["capacity"]
    weights = [it["weight"] for it in dados["items"]]
    profits = [it["profit"] for it in dados["items"]]
    ids = [it["id"] for it in dados["items"]]

    random.seed(42)
    solucao, lucro = simulated_annealing(C, weights, profits)
    selecionados = [ids[i] for i, xi in enumerate(solucao) if xi == 1]
    print(f"SA — Lucro: {lucro:.0f} | Itens: {selecionados}")
