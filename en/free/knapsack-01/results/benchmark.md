# Benchmark — 0/1 Knapsack

> Results obtained on: **fill in after running**
> Hardware: **fill in**
> Default solver: HiGHS (via Pyomo `appsi_highs`)

---

## Instances

| Instance | Items | Capacity | Optimum | Status |
|---|---|---|---|---|
| `small_5.json` | 5 | 10 | 40 | ✅ Verified |
| `medium_15.json` | 15 | 50 | — | — |
| `large_50.json` | 50 | 200 | — | — |

---

## Results — Pyomo + HiGHS

| Instance | Profit found | Gap (%) | Time (s) |
|---|---|---|---|
| small_5 | — | — | — |
| medium_15 | — | — | — |
| large_50 | — | — | — |

## Results — JuMP + HiGHS (Julia)

| Instance | Profit found | Gap (%) | Time (s) |
|---|---|---|---|
| small_5 | — | — | — |
| medium_15 | — | — | — |
| large_50 | — | — | — |

---

## How to reproduce

```bash
# Python
python exact/model_pyomo.py instances/small_5.json
python exact/model_pyomo.py instances/medium_15.json
python exact/model_pyomo.py instances/large_50.json

# Julia
julia exact/model_jump.jl instances/small_5.json
julia exact/model_jump.jl instances/medium_15.json
julia exact/model_jump.jl instances/large_50.json
```
