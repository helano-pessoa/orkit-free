"""Mochila 0/1 -- GRASP (Greedy Randomized Adaptive Search Procedure).

Fase de construcao:
    Adiciona itens em ordem de razao lucro/peso, com aleatoriedade
    controlada por alpha (0=guloso, 1=totalmente aleatorio).

Fase de busca local:
    Tentativas de troca de itens (swap) para melhorar o lucro.

Dependencias: nenhuma (stdlib apenas)

Referencias:
    Feo, T. A., Resende, M. G. C. (1995). Greedy Randomized Adaptive Search
    Procedures. Journal of Global Optimization, 6(2), 109-133.
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


def construcao(C: float, weights: list[float], profits: list[float], alpha: float = 0.3) -> list[int]:
    """Fase de construcao: guloso randomizado pela razao lucro/peso."""
    n = len(weights)
    x = [0] * n
    restante = C
    nao_selecionados = list(range(n))

    while nao_selecionados:
        candidatos = [i for i in nao_selecionados if weights[i] <= restante]
        if not candidatos:
            break

        razoes = [profits[i] / max(weights[i], 1e-9) for i in candidatos]
        r_min, r_max = min(razoes), max(razoes)
        limite = r_max - alpha * (r_max - r_min)
        rcl = [candidatos[j] for j, r in enumerate(razoes) if r >= limite]

        escolhido = random.choice(rcl)
        x[escolhido] = 1
        restante -= weights[escolhido]
        nao_selecionados.remove(escolhido)

    return x


def busca_local(x: list[int], C: float, weights: list[float], profits: list[float]) -> list[int]:
    """Troca um item selecionado por um nao selecionado se melhorar o lucro."""
    melhorou = True
    while melhorou:
        melhorou = False
        selecionados = [i for i, xi in enumerate(x) if xi == 1]
        nao_sel = [i for i, xi in enumerate(x) if xi == 0]
        for i in selecionados:
            for j in nao_sel:
                # Tenta trocar i por j
                novo = x[:]
                novo[i] = 0
                novo[j] = 1
                if peso_total(novo, weights) <= C and lucro_total(novo, profits) > lucro_total(x, profits):
                    x = novo
                    melhorou = True
                    break
            if melhorou:
                break
    return x


def grasp(
    C: float,
    weights: list[float],
    profits: list[float],
    n_iter: int = 50,
    alpha: float = 0.3,
) -> tuple[list[int], float]:
    """Executa GRASP para a Mochila 0/1.

    Returns:
        (melhor_solucao, melhor_lucro)
    """
    melhor = None
    melhor_lucro = -1.0

    for _ in range(n_iter):
        sol = construcao(C, weights, profits, alpha)
        sol = busca_local(sol, C, weights, profits)
        l = lucro_total(sol, profits)
        if l > melhor_lucro:
            melhor = sol[:]
            melhor_lucro = l

    return melhor, melhor_lucro


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "../instances/small_5.json"
    dados = carregar(path)
    C = dados["capacity"]
    weights = [it["weight"] for it in dados["items"]]
    profits = [it["profit"] for it in dados["items"]]
    ids = [it["id"] for it in dados["items"]]

    random.seed(42)
    solucao, lucro = grasp(C, weights, profits)
    selecionados = [ids[i] for i, xi in enumerate(solucao) if xi == 1]
    print(f"GRASP — Lucro: {lucro:.0f} | Itens: {selecionados}")
