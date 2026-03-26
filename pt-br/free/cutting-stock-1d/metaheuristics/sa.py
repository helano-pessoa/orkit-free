"""Corte de Estoque 1D -- Simulated Annealing (SA).

Representacao da solucao:
    Lista de rolos, cada rolo sendo um dict {item_id: quantidade}.
    Inicializacao: First-Fit Decreasing (FFD).

Perturbacao:
    - Mover uma unidade aleatoria de um rolo para outro (ou novo rolo).
    - Tentar consolidar rolos quase vazios.

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
from pathlib import Path


# ---------------------------------------------------------------------------
# Estrutura de dados leve (sem dependencia de instance.py)
# ---------------------------------------------------------------------------

def carregar(caminho: str) -> dict:
    with open(caminho, encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# Construcao da solucao inicial: First-Fit Decreasing
# ---------------------------------------------------------------------------

def ffd_inicial(W: float, widths: dict, demands: dict) -> list[dict]:
    """Constroi solucao inicial via First-Fit Decreasing."""
    pecas_ordenadas = sorted(widths.keys(), key=lambda i: widths[i], reverse=True)
    rolos: list[dict] = []
    espaco_livre: list[float] = []

    for i in pecas_ordenadas:
        for _ in range(demands[i]):
            colocado = False
            for idx, esp in enumerate(espaco_livre):
                if esp >= widths[i]:
                    rolos[idx][i] = rolos[idx].get(i, 0) + 1
                    espaco_livre[idx] -= widths[i]
                    colocado = True
                    break
            if not colocado:
                rolos.append({i: 1})
                espaco_livre.append(W - widths[i])

    return rolos


def custo(rolos: list[dict]) -> int:
    """Numero de rolos usados (funcao objetivo)."""
    return len(rolos)


def factivel(rolos: list[dict], W: float, widths: dict, demands: dict) -> bool:
    """Verifica factibilidade: demanda e capacidade."""
    # capacidade
    for rolo in rolos:
        if sum(widths[i] * q for i, q in rolo.items()) > W + 1e-9:
            return False
    # demanda
    contagem = {}
    for rolo in rolos:
        for i, q in rolo.items():
            contagem[i] = contagem.get(i, 0) + q
    return all(contagem.get(i, 0) >= demands[i] for i in demands)


# ---------------------------------------------------------------------------
# Perturbacao
# ---------------------------------------------------------------------------

def perturbar(rolos: list[dict], W: float, widths: dict) -> list[dict]:
    """Gera vizinho: tenta mover 1 unidade de peca entre rolos."""
    novo = deepcopy(rolos)
    if len(novo) == 0:
        return novo

    # Escolhe rolo origem com pelo menos 1 peca
    tentativas = 0
    while tentativas < 20:
        tentativas += 1
        orig = random.randrange(len(novo))
        if not novo[orig]:
            continue
        item = random.choice(list(novo[orig].keys()))

        # Remove do origem
        novo[orig][item] -= 1
        if novo[orig][item] == 0:
            del novo[orig][item]

        espaco_orig = W - sum(widths[i] * q for i, q in novo[orig].items())

        # Tenta colocar em outro rolo existente
        destinos = [j for j in range(len(novo)) if j != orig]
        random.shuffle(destinos)
        colocado = False
        for dest in destinos:
            esp_dest = W - sum(widths[i] * q for i, q in novo[dest].items())
            if esp_dest >= widths[item]:
                novo[dest][item] = novo[dest].get(item, 0) + 1
                colocado = True
                break

        if not colocado:
            # Abre novo rolo
            novo.append({item: 1})

        # Remove rolos vazios
        novo = [r for r in novo if r]
        return novo

    return rolos


# ---------------------------------------------------------------------------
# Simulated Annealing
# ---------------------------------------------------------------------------

def simulated_annealing(
    W: float,
    widths: dict,
    demands: dict,
    T0: float = 10.0,
    alpha: float = 0.995,
    iter_por_temp: int = 100,
    paradas: int = 500,
) -> tuple[list[dict], int]:
    """Executa SA para o Corte de Estoque 1D.

    Args:
        W: Largura do rolo-mestre.
        widths: {item_id: largura}.
        demands: {item_id: demanda}.
        T0: Temperatura inicial.
        alpha: Taxa de resfriamento.
        iter_por_temp: Iteracoes por nivel de temperatura.
        paradas: Numero de reducoes de temperatura.

    Returns:
        (melhor_solucao, melhor_custo)
    """
    atual = ffd_inicial(W, widths, demands)
    melhor = deepcopy(atual)
    melhor_custo = custo(melhor)
    T = T0

    for _ in range(paradas):
        for _ in range(iter_por_temp):
            vizinho = perturbar(atual, W, widths)
            if not factivel(vizinho, W, widths, demands):
                continue
            delta = custo(vizinho) - custo(atual)
            if delta < 0 or random.random() < math.exp(-delta / max(T, 1e-10)):
                atual = vizinho
                if custo(atual) < melhor_custo:
                    melhor = deepcopy(atual)
                    melhor_custo = custo(melhor)
        T *= alpha

    return melhor, melhor_custo


# ---------------------------------------------------------------------------
# Ponto de entrada
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "../instances/small_3.json"
    dados = carregar(path)
    W = dados["master_roll"]
    widths = {it["id"]: it["width"] for it in dados["items"]}
    demands = {it["id"]: it["demand"] for it in dados["items"]}

    random.seed(42)
    solucao, n_rolos = simulated_annealing(W, widths, demands)
    print(f"SA — Rolos utilizados: {n_rolos}")
    for idx, rolo in enumerate(solucao, 1):
        print(f"  Rolo {idx}: {rolo}")
