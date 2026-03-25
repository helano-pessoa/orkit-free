# 1D Cutting Stock Problem

> Bundle: **FREE** · Type: Linear Programming + Column Generation

---

## Description

Given a set of rolls/bars of width $W$ (master roll), and demands
$d_i$ for pieces of width $w_i$, the goal is to meet all demands
**minimizing the number of master rolls cut**.

This is a classic problem in the paper, steel, and glass industries.
The **Column Generation** approach (Gilmore & Gomory, 1961) decomposes the model into:

- **Master Problem** (LP relaxation): selects how many times each cutting
  pattern is used.
- **Subproblem** (Integer Knapsack): identifies the most promising column
  (pattern with most negative reduced cost).

---

## Mathematical Formulation

**Sets and Parameters**
- $I = \{1, \ldots, m\}$: item types
- $w_i$: width of item type $i$
- $d_i$: demand for item type $i$
- $W$: master roll width
- $\mathcal{P}$: set of feasible cutting patterns
- $a_{ij}$: number of items of type $i$ in pattern $j$

**Master Problem — LP relaxation**

$$\min \quad \sum_{j \in \mathcal{P}} x_j$$

$$\text{s.a.} \quad \sum_{j \in \mathcal{P}} a_{ij} \, x_j \geq d_i, \quad \forall i \in I$$

$$x_j \geq 0, \quad \forall j \in \mathcal{P}$$

**Subproblem — Integer Knapsack (optimality check)**

$$z^* = \max \quad \sum_{i \in I} \pi_i y_i$$

$$\text{s.a.} \quad \sum_{i \in I} w_i \, y_i \leq W$$

$$y_i \geq 0, \quad y_i \in \mathbb{Z}, \quad \forall i \in I$$

> A new column is added to the Master if $z^* > 1$.
> After convergence, the Integer Master (MIP) is solved with all generated columns.

---

## File Structure

```
cutting-stock-1d/
├── README.md
├── exact/
│   ├── instance.py              ← dataclasses: CuttingStockInstance, Solution
│   ├── model_pyomo.py           ← Column Generation with Pyomo + HiGHS
│   ├── model_jump.jl            ← Column Generation with JuMP + HiGHS
│   └── model_gurobi.py          ← gurobipy (optional — requires license)
├── notebooks/
│   ├── 01_formulation.ipynb
│   └── 02_column_generation.ipynb
├── instances/
│   ├── small_3.json             ← 3 item types
│   └── medium_7.json            ← 7 item types
└── results/
    └── benchmark.md
```

---

## How to Run

### Python (Pyomo + HiGHS)

```bash
pip install pyomo highspy numpy
python exact/model_pyomo.py instances/small_3.json
```

### Julia (JuMP + HiGHS)

```bash
julia -e 'using Pkg; Pkg.add(["JuMP", "HiGHS", "JSON3"])'
julia exact/model_jump.jl instances/small_3.json
```

### Gurobi (optional)

```bash
pip install gurobipy
python exact/model_gurobi.py instances/small_3.json
```

---

## Instance Format (JSON)

```json
{
  "name": "cutting_stock_small_3",
  "master_roll": 100,
  "items": [
    {"id": 1, "width": 25, "demand": 4},
    {"id": 2, "width": 40, "demand": 3},
    {"id": 3, "width": 15, "demand": 6}
  ]
}
```

---

## References

- Gilmore, P. C., Gomory, R. E. (1961). A linear programming approach to
  the cutting stock problem. *Operations Research*, 9(6), 849–859.
- Gilmore, P. C., Gomory, R. E. (1963). A linear programming approach to
  the cutting stock problem — Part II. *Operations Research*, 11(6), 863–888.
- Uchoa, E., Pessoa, A., Moreno, M. (2024). *Column Generation*. Springer.
