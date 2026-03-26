# 1D Cutting Stock Problem

> Bundle: **FREE** · Type: Mixed Integer Programming

---

## Description

Given $m$ item types with width $w_i$ and demand $d_i$, and master rolls of width $W$,
the goal is to meet all demands **minimizing the number of master rolls used**.

---

## Mathematical Formulation

**Sets and Parameters**
- $I = \{1, \ldots, m\}$: item types
- $N = \{1, \ldots, N_{\max}\}$: available rolls (upper bound)
- $w_i$: width of item type $i$
- $d_i$: demand for item type $i$
- $W$: master roll width

**Decision Variables**
- $y_n \in \{0, 1\}$: 1 if roll $n$ is opened
- $x_{in} \in \mathbb{Z}_{\geq 0}$: number of items of type $i$ cut from roll $n$

**Model**

$$\min \quad \sum_{n \in N} y_n$$

$$\text{s.t.} \quad \sum_{n \in N} x_{in} \geq d_i, \quad \forall i \in I \quad \text{(demand)}$$

$$\sum_{i \in I} w_i \, x_{in} \leq W \, y_n, \quad \forall n \in N \quad \text{(capacity)}$$

$$y_n \in \{0, 1\}, \quad x_{in} \in \mathbb{Z}_{\geq 0}$$

> Upper bound: $N_{\max} = \sum_{i} d_i$ (worst case — one item per roll).

---

## Solving Methods

| File | Language | Approach |
|------|----------|----------|
| `exact/model_pyomo.py` | Python | Pyomo + HiGHS |
| `exact/model_gurobi.py` | Python | gurobipy + Gurobi |
| `exact/model_ortools.py` | Python | OR-Tools (CP-SAT) |
| `exact/model_jump.jl` | Julia | JuMP + HiGHS |
| `metaheuristics/sa.py` | Python | Simulated Annealing |
| `metaheuristics/grasp.py` | Python | GRASP |
| `metaheuristics/ga.py` | Python | Genetic Algorithm |

---

## File Structure

```
cutting-stock-1d/
├── README.md
├── exact/
│   ├── instance.py              ← dataclasses: ItemType, CuttingStockInstance
│   ├── model_pyomo.py           ← Pyomo + HiGHS
│   ├── model_gurobi.py          ← gurobipy  (requires license)
│   ├── model_ortools.py         ← OR-Tools CP-SAT
│   └── model_jump.jl            ← JuMP + HiGHS
├── metaheuristics/
│   ├── sa.py                    ← Simulated Annealing
│   ├── grasp.py                 ← GRASP
│   └── ga.py                   ← Genetic Algorithm
├── instances/
│   ├── small_3.json
│   └── medium_7.json
└── results/
    └── benchmark.md
```

---

## How to Run

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

### Metaheuristics

```bash
python metaheuristics/sa.py instances/small_3.json
python metaheuristics/grasp.py instances/small_3.json
python metaheuristics/ga.py instances/small_3.json
```

---

## Instance Format (JSON)

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

## References

- Kantorovich, L. V. (1960). Mathematical Methods of Organising and Planning Production.
- Wäscher, G., Haußner, H., Schumann, H. (2007). An improved typology of cutting
  and packing problems. *European Journal of Operational Research*, 183(3), 1109–1130.
