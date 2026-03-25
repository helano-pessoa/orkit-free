# Mochila 0/1 (Binary Knapsack Problem)

> Bundle: **Gratuito (free)** · Tipo: Programação Inteira Binária

---

## Descrição

Dado um conjunto de $n$ itens, cada um com peso $w_i$ e lucro $p_i$, e uma
mochila com capacidade $C$, o objetivo é selecionar um subconjunto de itens
que **maximize o lucro total** sem exceder a capacidade.

É um dos problemas combinatórios mais estudados na literatura, serve como
sub-problema de Geração de Colunas, Relaxação Lagrangeana e Branch-and-Bound.

---

## Formulação Matemática

**Conjuntos**
- $I = \{1, \ldots, n\}$: conjunto de itens disponíveis

**Parâmetros**
- $p_i \geq 0$: lucro do item $i$
- $w_i \geq 0$: peso do item $i$
- $C > 0$: capacidade da mochila

**Variáveis de decisão**
- $x_i \in \{0, 1\}$: 1 se o item $i$ for selecionado, 0 caso contrário

**Modelo**

$$\max \quad \sum_{i \in I} p_i \, x_i$$

$$\text{s.a.} \quad \sum_{i \in I} w_i \, x_i \leq C$$

$$x_i \in \{0, 1\}, \quad \forall i \in I$$

---

## Variantes cobertas neste bundle

| Variante | Arquivo |
|---|---|
| Mochila 0/1 clássica (este problema) | `exact/model_pyomo.py`, `exact/model_jump.jl` |
| Mochila 0/1 com Gurobi | `exact/model_gurobi.py` |

---

## Estrutura de arquivos

```
knapsack-01/
├── README.md
├── exact/
│   ├── instance.py          ← dataclasses: Item, KnapsackInstance, KnapsackSolution
│   ├── model_pyomo.py       ← Pyomo + HiGHS (solver padrão open-source)
│   ├── model_jump.jl        ← JuMP + HiGHS  (Julia)
│   └── model_gurobi.py      ← gurobipy      (requer licença Gurobi)
├── notebooks/
│   ├── 01_formulacao.ipynb
│   └── 02_solucao_e_analise.ipynb
├── instances/
│   ├── small_5.json         ← 5 itens, ótimo conhecido (40)
│   ├── medium_15.json       ← 15 itens
│   └── large_50.json        ← 50 itens
└── results/
    └── benchmark.md
```

---

## Como executar

### Python (Pyomo + HiGHS)

```bash
pip install pyomo highspy
cd exact/
python model_pyomo.py ../instances/small_5.json
```

### Julia (JuMP + HiGHS)

```julia
# Instalar dependências (uma vez):
# ] add JuMP HiGHS JSON3

julia exact/model_jump.jl instances/small_5.json
```

### Gurobi (opcional)

```bash
pip install gurobipy  # requer licença ativa
python exact/model_gurobi.py instances/small_5.json
```

---

## Formato de instância (JSON)

```json
{
  "name": "knapsack_small_5",
  "description": "Instância com 5 itens",
  "capacity": 10,
  "items": [
    {"id": 1, "weight": 2, "profit": 6},
    {"id": 2, "weight": 2, "profit": 10}
  ],
  "optimal_value": 40
}
```

---

## Referências

- Kellerer, H., Pferschy, U., Pisinger, D. (2004). *Knapsack Problems*. Springer.
- Martello, S., Toth, P. (1990). *Knapsack Problems: Algorithms and Computer
  Implementations*. Wiley.
- Pisinger, D. (1995). *Algorithms for Knapsack Problems*. PhD Thesis, University
  of Copenhagen.
