"""Corte de Estoque 1D -- Algoritmo Genetico (GA).

Representacao do cromossomo:
    Lista de comprimento sum(demanda), onde cromossomo[k] indica
    a qual rolo a k-esima unidade de peca (ordenada) foi atribuida.

Operadores:
    Selecao: torneio binario
    Cruzamento: ponto unico
    Mutacao: troca de rolo de uma peca aleatoria

Dependencias: nenhuma (stdlib apenas)

Referencias:
    Holland, J. H. (1975). Adaptation in Natural and Artificial Systems. MIT Press.
    Falkenauer, E. (1996). A hybrid grouping genetic algorithm for bin packing.
    Journal of Heuristics, 2(1), 5-30.
"""

from __future__ import annotations

import json
import random
import sys
from copy import deepcopy
from math import ceil


# ---------------------------------------------------------------------------
# Utilitarios
# ---------------------------------------------------------------------------

def carregar(caminho: str) -> dict:
    with open(caminho, encoding="utf-8") as fh:
        return json.load(fh)


def decodificar(cromossomo: list[int], widths: dict, ordem_pecas: list[int]) -> list[dict]:
    """Converte cromossomo em lista de rolos.

    Args:
        cromossomo: cromossomo[k] = indice do rolo da k-esima peca.
        widths: {item_id: largura}.
        ordem_pecas: sequencia de item_ids (repetidos por demanda).

    Returns:
        Lista de rolos (dicts {item_id: qtd}).
    """
    rolos: dict[int, dict] = {}
    for k, rolo_id in enumerate(cromossomo):
        i = ordem_pecas[k]
        if rolo_id not in rolos:
            rolos[rolo_id] = {}
        rolos[rolo_id][i] = rolos[rolo_id].get(i, 0) + 1
    return list(rolos.values())


def fitness(cromossomo: list[int], widths: dict, ordem_pecas: list[int], W: float) -> float:
    """Calcula fitness (menor = melhor). Penaliza violacoes de capacidade."""
    rolos_dict: dict[int, float] = {}
    for k, rolo_id in enumerate(cromossomo):
        i = ordem_pecas[k]
        rolos_dict[rolo_id] = rolos_dict.get(rolo_id, 0.0) + widths[i]

    n_rolos = len(rolos_dict)
    penalidade = sum(max(0, uso - W) for uso in rolos_dict.values()) * 1000.0
    return float(n_rolos) + penalidade


def cromossomo_aleatorio(n_pecas: int, n_rolos_max: int) -> list[int]:
    return [random.randint(0, n_rolos_max - 1) for _ in range(n_pecas)]


# Inicializacao por FFD para semear populacao
def cromossomo_ffd(W: float, widths: dict, ordem_pecas: list[int]) -> list[int]:
    rolos: list[float] = []
    atribuicao: list[int] = []
    for i in ordem_pecas:
        colocado = False
        for j, esp in enumerate(rolos):
            if esp + widths[i] <= W:
                rolos[j] += widths[i]
                atribuicao.append(j)
                colocado = True
                break
        if not colocado:
            atribuicao.append(len(rolos))
            rolos.append(widths[i])
    return atribuicao


# ---------------------------------------------------------------------------
# Operadores geneticos
# ---------------------------------------------------------------------------

def torneio(pop: list[list[int]], fits: list[float], k: int = 2) -> list[int]:
    concorrentes = random.sample(range(len(pop)), k)
    vencedor = min(concorrentes, key=lambda j: fits[j])
    return pop[vencedor][:]


def cruzamento(pai1: list[int], pai2: list[int]) -> tuple[list[int], list[int]]:
    n = len(pai1)
    ponto = random.randint(1, n - 1)
    return pai1[:ponto] + pai2[ponto:], pai2[:ponto] + pai1[ponto:]


def mutacao(crom: list[int], n_rolos_max: int, taxa: float = 0.05) -> list[int]:
    return [
        random.randint(0, n_rolos_max - 1) if random.random() < taxa else g
        for g in crom
    ]


# ---------------------------------------------------------------------------
# Algoritmo Genetico
# ---------------------------------------------------------------------------

def genetico(
    W: float,
    widths: dict,
    demands: dict,
    pop_size: int = 50,
    n_geracoes: int = 200,
    taxa_mutacao: float = 0.05,
) -> tuple[list[dict], int]:
    """Executa GA para o Corte de Estoque 1D.

    Returns:
        (melhor_solucao_decodificada, numero_de_rolos)
    """
    # Prepara sequencia de pecas (repetida por demanda, ordenada desc por largura)
    ordem_pecas = sorted(
        [i for i, d in demands.items() for _ in range(d)],
        key=lambda i: widths[i],
        reverse=True,
    )
    n_pecas = len(ordem_pecas)
    n_rolos_max = n_pecas  # cota superior

    # Populacao inicial: 50% FFD + 50% aleatorio
    pop = [cromossomo_ffd(W, widths, ordem_pecas)]
    while len(pop) < pop_size:
        pop.append(cromossomo_aleatorio(n_pecas, n_rolos_max))

    melhor_crom = None
    melhor_fit = float("inf")

    for geracao in range(n_geracoes):
        fits = [fitness(c, widths, ordem_pecas, W) for c in pop]

        # Elitismo: guarda o melhor
        idx_melhor = min(range(len(pop)), key=lambda j: fits[j])
        if fits[idx_melhor] < melhor_fit:
            melhor_fit = fits[idx_melhor]
            melhor_crom = pop[idx_melhor][:]

        # Nova geracao
        nova_pop = [melhor_crom[:]]  # elitismo
        while len(nova_pop) < pop_size:
            p1 = torneio(pop, fits)
            p2 = torneio(pop, fits)
            f1, f2 = cruzamento(p1, p2)
            nova_pop.append(mutacao(f1, n_rolos_max, taxa_mutacao))
            if len(nova_pop) < pop_size:
                nova_pop.append(mutacao(f2, n_rolos_max, taxa_mutacao))
        pop = nova_pop

    rolos = decodificar(melhor_crom, widths, ordem_pecas)
    n_rolos = len(rolos)
    return rolos, n_rolos


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
    solucao, n_rolos = genetico(W, widths, demands)
    print(f"GA — Rolos utilizados: {n_rolos}")
    for idx, rolo in enumerate(solucao, 1):
        print(f"  Rolo {idx}: {rolo}")
