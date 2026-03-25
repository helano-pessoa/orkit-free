# Problema de Transporte (Transportation Problem)

> Bundle: **Gratuito (free)** · Tipo: Programação Linear Clássica

---

## Descrição

Dado um conjunto de $m$ fornecedores (origens) com oferta $s_i$ e $n$ clientes
(destinos) com demanda $d_j$, determine o plano de distribuição que
**minimiza o custo total de transporte**, respeitando todas as capacidades.

---

## Formulação Matemática

**Conjuntos e Parâmetros**
- $I = \{1, \ldots, m\}$: fornecedores
- $J = \{1, \ldots, n\}$: clientes
- $s_i$: oferta do fornecedor $i$
- $d_j$: demanda do cliente $j$
- $c_{ij}$: custo unitário de transporte de $i$ para $j$

**Variáveis**
- $x_{ij} \geq 0$: quantidade transportada de $i$ para $j$

**Modelo**

$$\min \quad \sum_{i \in I} \sum_{j \in J} c_{ij} \, x_{ij}$$

$$\text{s.a.} \quad \sum_{j \in J} x_{ij} \leq s_i, \quad \forall i \in I \quad \text{(restrição de oferta)}$$

$$\sum_{i \in I} x_{ij} \geq d_j, \quad \forall j \in J \quad \text{(restrição de demanda)}$$

$$x_{ij} \geq 0, \quad \forall i \in I, j \in J$$

> Caso $\sum s_i = \sum d_j$ (problema balanceado), as restrições de oferta tornam-se igualdades.

---

## Estrutura de Arquivos

```
transportation/
├── README.md
├── exact/
│   ├── instance.py
│   ├── model_pyomo.py
│   ├── model_jump.jl
│   └── model_gurobi.py
├── notebooks/
├── instances/
│   ├── small_3x4.json
│   └── medium_5x8.json
└── results/
    └── benchmark.md
```

---

## Status

🚧 **Em desenvolvimento** — disponível em breve no pacote Gratuito.

---

## Referências

- Dantzig, G. B. (1963). *Linear Programming and Extensions*. Princeton UP.
- Hitchcock, F. L. (1941). The distribution of a product from several sources
  to numerous localities. *Journal of Mathematics and Physics*, 20(1), 224–230.
