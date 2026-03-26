# Transportation Problem

> Type: Classical Linear Programming

---

## Description

Given $m$ suppliers (origins) with supply $s_i$ and $n$ customers
(destinations) with demand $d_j$, find the distribution plan that
**minimizes the total transportation cost** while satisfying all capacities.

---

## Mathematical Formulation

**Sets and Parameters**
- $I = \{1, \ldots, m\}$: suppliers
- $J = \{1, \ldots, n\}$: customers
- $s_i$: supply of supplier $i$
- $d_j$: demand of customer $j$
- $c_{ij}$: unit transportation cost from $i$ to $j$

**Variables**
- $x_{ij} \geq 0$: quantity shipped from $i$ to $j$

**Model**

$$\min \quad \sum_{i \in I} \sum_{j \in J} c_{ij} \, x_{ij}$$

$$\text{s.t.} \quad \sum_{j \in J} x_{ij} \leq s_i, \quad \forall i \in I \quad \text{(supply constraint)}$$

$$\sum_{i \in I} x_{ij} \geq d_j, \quad \forall j \in J \quad \text{(demand constraint)}$$

$$x_{ij} \geq 0, \quad \forall i \in I, j \in J$$

> When $\sum s_i = \sum d_j$ (balanced problem), supply constraints become equalities.

---

## Solving methods

| Category         | Tool               | File                          |
|------------------|--------------------|-------------------------------|
| Exact            | Pyomo + HiGHS      | `exact/model_pyomo.py`        |
| Exact            | Gurobi             | `exact/model_gurobi.py`       |
| Exact            | OR-Tools GLOP      | `exact/model_ortools.py`      |
| Exact            | JuMP + HiGHS       | `exact/model_jump.jl`         |
| Metaheuristic    | Simulated Annealing| `metaheuristics/sa.py`        |
| Metaheuristic    | GRASP              | `metaheuristics/grasp.py`     |
| Metaheuristic    | Genetic Algorithm  | `metaheuristics/ga.py`        |

---

## File structure

```
transportation/
├── README.md
├── exact/
│   ├── instance.py          ← dataclasses: Supplier, Customer, TransportInstance
│   ├── model_pyomo.py       ← Pyomo + HiGHS (default open-source solver)
│   ├── model_gurobi.py      ← gurobipy      (requires Gurobi license)
│   ├── model_ortools.py     ← OR-Tools GLOP (continuous LP)
│   └── model_jump.jl        ← JuMP + HiGHS  (Julia)
├── metaheuristics/
│   ├── sa.py                ← Simulated Annealing (NW init + square-loop perturbation)
│   ├── grasp.py             ← GRASP (min-cost RCL + flow reallocation)
│   └── ga.py                ← Genetic Algorithm (flat matrix + Sinkhorn repair)
├── notebooks/
├── instances/
│   ├── small_3x4.json       ← 3 suppliers, 4 customers (optimal = 520)
│   └── medium_5x8.json      ← 5 suppliers, 8 customers
└── results/
    └── benchmark.md
```

---

## How to run

### Python (Pyomo + HiGHS)

```bash
pip install pyomo highspy
cd exact/
python model_pyomo.py ../instances/small_3x4.json
```

### Julia (JuMP + HiGHS)

```julia
# Install dependencies (once):
# ] add JuMP HiGHS JSON3

julia exact/model_jump.jl instances/small_3x4.json
```

### Metaheuristics

```bash
python metaheuristics/sa.py instances/small_3x4.json
python metaheuristics/grasp.py instances/small_3x4.json
python metaheuristics/ga.py instances/small_3x4.json
```

---

## References

- Dantzig, G. B. (1963). *Linear Programming and Extensions*. Princeton UP.
- Hitchcock, F. L. (1941). The distribution of a product from several sources
  to numerous localities. *Journal of Mathematics and Physics*, 20(1), 224–230.
