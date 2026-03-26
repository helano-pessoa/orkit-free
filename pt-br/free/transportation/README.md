# Problema de Transporte (Transportation Problem)

> Tipo: Programação Linear Clássica

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

## Métodos de resolução

| Categoria        | Ferramenta         | Arquivo                       |
|------------------|--------------------|-------------------------------|
| Exato            | Pyomo + HiGHS      | `exact/model_pyomo.py`        |
| Exato            | Gurobi             | `exact/model_gurobi.py`       |
| Exato            | OR-Tools GLOP      | `exact/model_ortools.py`      |
| Exato            | JuMP + HiGHS       | `exact/model_jump.jl`         |
| Meta-heurística  | Simulated Annealing| `metaheuristics/sa.py`        |
| Meta-heurística  | GRASP              | `metaheuristics/grasp.py`     |
| Meta-heurística  | Algoritmo Genético | `metaheuristics/ga.py`        |

---

## Estrutura de Arquivos

```
transportation/
├── README.md
├── exact/
│   ├── instance.py          ← dataclasses: Fornecedor, Cliente, InstanciaTransporte
│   ├── model_pyomo.py       ← Pyomo + HiGHS (solver padrão open-source)
│   ├── model_gurobi.py      ← gurobipy      (requer licença Gurobi)
│   ├── model_ortools.py     ← OR-Tools GLOP (LP contínuo)
│   └── model_jump.jl        ← JuMP + HiGHS  (Julia)
├── metaheuristics/
│   ├── sa.py                ← Simulated Annealing (init NW + perturbação em quadrado)
│   ├── grasp.py             ← GRASP (RCL custo mínimo + realocação de fluxo)
│   └── ga.py                ← Algoritmo Genético (cromossomo plano + reparo Sinkhorn)
├── notebooks/
├── instances/
│   ├── small_3x4.json       ← 3 fornecedores, 4 clientes (ótimo = 520)
│   └── medium_5x8.json      ← 5 fornecedores, 8 clientes
└── results/
    └── benchmark.md
```

---

## Como executar

### Python (Pyomo + HiGHS)

```bash
pip install pyomo highspy
cd exact/
python model_pyomo.py ../instances/small_3x4.json
```

### Julia (JuMP + HiGHS)

```julia
# Instalar dependências (uma vez):
# ] add JuMP HiGHS JSON3

julia exact/model_jump.jl instances/small_3x4.json
```

### Meta-heurísticas

```bash
python metaheuristics/sa.py instances/small_3x4.json
python metaheuristics/grasp.py instances/small_3x4.json
python metaheuristics/ga.py instances/small_3x4.json
```

---

## Referências

- Dantzig, G. B. (1963). *Linear Programming and Extensions*. Princeton UP.
- Hitchcock, F. L. (1941). The distribution of a product from several sources
  to numerous localities. *Journal of Mathematics and Physics*, 20(1), 224–230.
