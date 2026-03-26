# Corte de Estoque 1D (1D Cutting Stock Problem)

> Bundle: **Gratuito (free)** · Tipo: Programação Inteira Mista

---

## Descrição

Dado um conjunto de $m$ tipos de peça com largura $w_i$ e demanda $d_i$, e
rolos-mestre de largura $W$, o objetivo é atender toda a demanda
**minimizando o número de rolos-mestre utilizados**.

---

## Formulação Matemática

**Conjuntos e Parâmetros**
- $I = \{1, \ldots, m\}$: tipos de peça
- $N = \{1, \ldots, N_{\max}\}$: rolos disponíveis (cota superior)
- $w_i$: largura da peça do tipo $i$
- $d_i$: demanda da peça do tipo $i$
- $W$: largura do rolo-mestre

**Variáveis de decisão**
- $y_n \in \{0, 1\}$: 1 se o rolo $n$ for aberto
- $x_{in} \in \mathbb{Z}_{\geq 0}$: quantidade de peças do tipo $i$ cortadas do rolo $n$

**Modelo**

$$\min \quad \sum_{n \in N} y_n$$

$$\text{s.a.} \quad \sum_{n \in N} x_{in} \geq d_i, \quad \forall i \in I \quad \text{(demanda)}$$

$$\sum_{i \in I} w_i \, x_{in} \leq W \, y_n, \quad \forall n \in N \quad \text{(capacidade)}$$

$$y_n \in \{0, 1\}, \quad x_{in} \in \mathbb{Z}_{\geq 0}$$

> Cota superior: $N_{\max} = \sum_{i} d_i$ (pior caso — cada peça em rolo separado).

---

## Métodos de Resolução

| Arquivo | Linguagem | Abordagem |
|---------|-----------|-----------|
| `exact/model_pyomo.py` | Python | Pyomo + HiGHS |
| `exact/model_gurobi.py` | Python | gurobipy + Gurobi |
| `exact/model_ortools.py` | Python | OR-Tools (CP-SAT) |
| `exact/model_jump.jl` | Julia | JuMP + HiGHS |
| `metaheuristics/sa.py` | Python | Simulated Annealing |
| `metaheuristics/grasp.py` | Python | GRASP |
| `metaheuristics/ga.py` | Python | Algoritmo Genético |

---

## Estrutura de Arquivos

```
cutting-stock-1d/
├── README.md
├── exact/
│   ├── instance.py              ← dataclasses: ItemType, CuttingStockInstance
│   ├── model_pyomo.py           ← Pyomo + HiGHS
│   ├── model_gurobi.py          ← gurobipy  (requer licença)
│   ├── model_ortools.py         ← OR-Tools CP-SAT
│   └── model_jump.jl            ← JuMP + HiGHS
├── metaheuristics/
│   ├── sa.py                    ← Simulated Annealing
│   ├── grasp.py                 ← GRASP
│   └── ga.py                   ← Algoritmo Genético
├── instances/
│   ├── small_3.json
│   └── medium_7.json
└── results/
    └── benchmark.md
```

---

## Como Executar

### Python (Pyomo + HiGHS)

```bash
pip install pyomo highspy
cd exact/
python model_pyomo.py ../instances/small_3.json
```

### Julia (JuMP + HiGHS)

```julia
# ] add JuMP HiGHS JSON3
julia exact/model_jump.jl instances/small_3.json
```

### Metaheurísticas

```bash
python metaheuristics/sa.py instances/small_3.json
python metaheuristics/grasp.py instances/small_3.json
python metaheuristics/ga.py instances/small_3.json
```

---

## Formato de Instância (JSON)

```json
{
  "name": "cutting_small_3",
  "master_roll": 100,
  "items": [
    {"id": 1, "width": 45, "demand": 4},
    {"id": 2, "width": 35, "demand": 3},
    {"id": 3, "width": 20, "demand": 6}
  ]
}
```

---

## Referências

- Kantorovich, L. V. (1960). Mathematical Methods of Organising and Planning Production.
- Wäscher, G., Haußner, H., Schumann, H. (2007). An improved typology of cutting
  and packing problems. *European Journal of Operational Research*, 183(3), 1109–1130.
