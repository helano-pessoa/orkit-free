# 0/1 Knapsack Problem (Binary Knapsack)

> Bundle: **Free** · Type: Binary Integer Programming

---

## Description

Given a set of $n$ items, each with weight $w_i$ and profit $p_i$, and a
knapsack of capacity $C$, the goal is to select a subset of items that
**maximizes total profit** without exceeding the capacity.

This is one of the most studied combinatorial problems in the literature;
it also appears as a subproblem in Column Generation, Lagrangian Relaxation,
and Branch-and-Bound algorithms.

---

## Mathematical Formulation

**Sets**
- $I = \{1, \ldots, n\}$: set of available items

**Parameters**
- $p_i \geq 0$: profit of item $i$
- $w_i \geq 0$: weight of item $i$
- $C > 0$: knapsack capacity

**Decision variables**
- $x_i \in \{0, 1\}$: 1 if item $i$ is selected, 0 otherwise

**Model**

$$\max \quad \sum_{i \in I} p_i \, x_i$$

$$\text{s.t.} \quad \sum_{i \in I} w_i \, x_i \leq C$$

$$x_i \in \{0, 1\}, \quad \forall i \in I$$

---

## Variants covered in this bundle

| Variante | Arquivo |
|---|---|
| Classic 0/1 Knapsack (this problem) | `exact/model_pyomo.py`, `exact/model_jump.jl` |
| 0/1 Knapsack with Gurobi | `exact/model_gurobi.py` |

---

## File structure

```
knapsack-01/
├── README.md
├── exact/
│   ├── instance.py          ← dataclasses: Item, KnapsackInstance, KnapsackSolution
│   ├── model_pyomo.py       ← Pyomo + HiGHS (default open-source solver)
│   ├── model_jump.jl        ← JuMP + HiGHS  (Julia)
│   └── model_gurobi.py      ← gurobipy      (requires Gurobi license)
├── notebooks/
│   ├── 01_formulation.ipynb
│   └── 02_solution_and_analysis.ipynb
├── instances/
│   ├── small_5.json         ← 5 items, known optimum (40)
│   ├── medium_15.json       ← 15 items
│   └── large_50.json        ← 50 items
└── results/
    └── benchmark.md
```

---

## How to run

### Python (Pyomo + HiGHS)

```bash
pip install pyomo highspy
cd exact/
python model_pyomo.py ../instances/small_5.json
```

### Julia (JuMP + HiGHS)

```julia
# Install dependencies (once):
# ] add JuMP HiGHS JSON3

julia exact/model_jump.jl instances/small_5.json
```

### Gurobi (optional)

```bash
pip install gurobipy  # requires a valid Gurobi license
python exact/model_gurobi.py instances/small_5.json
```

---

## Instance format (JSON)

```json
{
  "name": "knapsack_small_5",
  "description": "Small instance with 5 items",
  "capacity": 10,
  "items": [
    {"id": 1, "weight": 2, "profit": 6},
    {"id": 2, "weight": 2, "profit": 10}
  ],
  "optimal_value": 40
}
```

---

## References

- Kellerer, H., Pferschy, U., Pisinger, D. (2004). *Knapsack Problems*. Springer.
- Martello, S., Toth, P. (1990). *Knapsack Problems: Algorithms and Computer
  Implementations*. Wiley.
- Pisinger, D. (1995). *Algorithms for Knapsack Problems*. PhD Thesis, University
  of Copenhagen.
