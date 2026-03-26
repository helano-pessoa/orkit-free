# Benchmark — Problema de Transporte

| Instancia      | Fornecedores | Clientes | Pyomo (s) | Gurobi (s) | OR-Tools (s) | JuMP (s) | SA   | GRASP | GA   |
|----------------|:---:|:---:|------:|-------:|--------:|-----:|-----:|------:|-----:|
| small_3x4      |  3  |  4  |   —   |    —   |    —    |  —   |  —   |   —   |  —   |
| medium_5x8     |  5  |  8  |   —   |    —   |    —    |  —   |  —   |   —   |  —   |

> Para preencher esta tabela, execute cada solver com `python model_pyomo.py ../instances/small_3x4.json` a partir de `exact/`.
