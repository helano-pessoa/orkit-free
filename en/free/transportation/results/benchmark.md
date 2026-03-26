# Benchmark -- Transportation Problem

| Instance       | Suppliers | Customers | Pyomo (s) | Gurobi (s) | OR-Tools (s) | JuMP (s) | SA   | GRASP | GA   |
|----------------|:---------:|:---------:|----------:|-----------:|-------------:|---------:|-----:|------:|-----:|
| small_3x4      |     3     |     4     |     —     |     —      |      —       |    —     |  —   |   —   |  —   |
| medium_5x8     |     5     |     8     |     —     |     —      |      —       |    —     |  —   |   —   |  —   |

> To fill this table, run each solver from the `exact/` folder with e.g. `python model_pyomo.py ../instances/small_3x4.json`.
