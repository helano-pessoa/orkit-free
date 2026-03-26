"""Corte de Estoque 1D -- GRASP (Greedy Randomized Adaptive Search Procedure).

Fase de construcao:
    Greedy randomizado: adiciona pecas por ordem decrescente de largura,
    com aleatoriedade controlada pelo parametro alpha (0=guloso, 1=aleatorio).

Fase de busca local:
    Tenta mover pecas entre rolos para reduzir o numero de rolos usados.

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
from pathlib import Path


# ---------------------------------------------------------------------------
# Utilitarios
# ---------------------------------------------------------------------------

def carregar(caminho: str) -> dict:
    with open(caminho, encoding="utf-8") as fh:
        return json.load(fh)


def custo(rolos: list[dict]) -> int:
    return len(rolos)


def espaco_livre(rolo: dict, W: float, widths: dict) -> float:
    return W - sum(widths[i] * q for i, q in rolo.items())


# ---------------------------------------------------------------------------
# Construcao GRASP
# ---------------------------------------------------------------------------

def construcao(W: float, widths: dict, demands: dict, alpha: float = 0.3) -> list[dict]:
    """Fase de construcao: greedy randomizada.

    Args:
        W: Largura do rolo-mestre.
        widths: {item_id: largura}.
        demands: {item_id: demanda}.
        alpha: Grau de aleatoriedade (0=guloso, 1=totalmente aleatorio).

    Returns:
        Solucao construida (lista de rolos).
    """
    # Cria lista de pecas a alocar (item_id repetido por demanda)
    pendente = []
    for i, d in demands.items():
        pendente.extend([i] * d)

    # Ordena decrescentemente por largura, com perturbacao aleatoria
    pendente.sort(key=lambda i: widths[i], reverse=True)

    rolos: list[dict] = []
    espacos: list[float] = []

    while pendente:
        item = pendente.pop(0)

        # Lista de candidatos: rolos com espaco suficiente
        candidatos = [
            idx for idx, esp in enumerate(espacos) if esp >= widths[item]
        ]

        if candidatos:
            # Restricted Candidate List: melhores (menor espaco restante apos inserir)
            custo_insercao = sorted(
                candidatos,
                key=lambda idx: espacos[idx] - widths[item],
            )
            threshold = (custo_insercao[0] if custo_insercao else 0)
            min_esp = espacos[custo_insercao[0]] - widths[item] if custo_insercao else 0
            max_esp = espacos[custo_insercao[-1]] - widths[item] if custo_insercao else 0
            limite = min_esp + alpha * (max_esp - min_esp)
            rcl = [idx for idx in candidatos if (espacos[idx] - widths[item]) <= limite]
            dest = random.choice(rcl) if rcl else candidatos[0]

            rolos[dest][item] = rolos[dest].get(item, 0) + 1
            espacos[dest] -= widths[item]
        else:
            rolos.append({item: 1})
            espacos.append(W - widths[item])

    return rolos


# ---------------------------------------------------------------------------
# Busca local
# ---------------------------------------------------------------------------

def busca_local(rolos: list[dict], W: float, widths: dict) -> list[dict]:
    """Tenta reduzir numero de rolos movendo pecas de rolos quase-vazios."""
    melhorou = True
    while melhorou:
        melhorou = False
        rolos = [r for r in rolos if r]  # remove vazios
        # Ordena rolos por carga crescente (candidatos a esvaziar primeiro)
        ordem = sorted(range(len(rolos)), key=lambda j: sum(widths[i]*q for i,q in rolos[j].items()))
        for orig in ordem:
            rolo_orig = rolos[orig]
            if not rolo_orig:
                continue
            # Tenta mover todas as pecas do rolo orig para outros rolos
            temp = deepcopy(rolos)
            pecas_orig = [(i, q) for i, q in rolo_orig.items() for _ in range(q)]
            temp[orig] = {}
            for item, _ in pecas_orig:
                colocado = False
                for dest in range(len(temp)):
                    if dest == orig:
                        continue
                    esp = W - sum(widths[i]*q for i,q in temp[dest].items())
                    if esp >= widths[item]:
                        temp[dest][item] = temp[dest].get(item, 0) + 1
                        colocado = True
                        break
                if not colocado:
                    break  # nao conseguiu esvaziar o rolo
            else:
                # Sucesso: removeu o rolo orig
                temp = [r for r in temp if r]
                if len(temp) < len([r for r in rolos if r]):
                    rolos = temp
                    melhorou = True
                    break
    return [r for r in rolos if r]


# ---------------------------------------------------------------------------
# GRASP
# ---------------------------------------------------------------------------

def grasp(
    W: float,
    widths: dict,
    demands: dict,
    n_iter: int = 50,
    alpha: float = 0.3,
) -> tuple[list[dict], int]:
    """Executa GRASP para o Corte de Estoque 1D.

    Args:
        W: Largura do rolo-mestre.
        widths: {item_id: largura}.
        demands: {item_id: demanda}.
        n_iter: Numero de iteracoes GRASP.
        alpha: Grau de aleatoriedade na construcao.

    Returns:
        (melhor_solucao, melhor_custo)
    """
    melhor = None
    melhor_custo = float("inf")

    for _ in range(n_iter):
        sol = construcao(W, widths, demands, alpha)
        sol = busca_local(sol, W, widths)
        c = custo(sol)
        if c < melhor_custo:
            melhor = deepcopy(sol)
            melhor_custo = c

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
    solucao, n_rolos = grasp(W, widths, demands)
    print(f"GRASP — Rolos utilizados: {n_rolos}")
    for idx, rolo in enumerate(solucao, 1):
        print(f"  Rolo {idx}: {rolo}")
