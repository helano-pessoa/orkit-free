# Transportation Problem

> Bundle: **FREE** · Type: Classical Linear Programming

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

## File Structure

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

🚧 **Under development** — coming soon in the FREE bundle.

---

## References

- Dantzig, G. B. (1963). *Linear Programming and Extensions*. Princeton UP.
- Hitchcock, F. L. (1941). The distribution of a product from several sources
  to numerous localities. *Journal of Mathematics and Physics*, 20(1), 224–230.
