# Corte de Estoque 1D (1D Cutting Stock Problem)

> Bundle: **Gratuito (free)** · Tipo: Programação Linear + Geração de Colunas

---

## Descrição

Dado um conjunto de bobinas/barras de tamanho $W$ (rolo-mestre), e demandas
$d_i$ por peças de tamanho $w_i$, o objetivo é atender toda a demanda
**minimizando o número de rolos-mestre cortados**.

Este problema é clássico na indústria de papel, aço e vidro. A abordagem
via **Geração de Colunas** (Gilmore & Gomory, 1961) decompõe o modelo em:

- **Problema Mestre** (LP relaxado): seleciona quantas vezes cada padrão de
  corte é usado
- **Sub-problema** (Mochila Inteira): identifica o padrão de maior custo
  reduzido (coluna promissora)

---

## Formulação Matemática

**Conjuntos e Parâmetros**
- $I = \{1, \ldots, m\}$: tipos de peça
- $w_i$: largura da peça do tipo $i$
- $d_i$: demanda pela peça do tipo $i$
- $W$: largura do rolo-mestre
- $\mathcal{P}$: conjunto de padrões de corte viáveis
- $a_{ij}$: número de peças do tipo $i$ no padrão $j$

**Problema Mestre — LP relaxado**

$$\min \quad \sum_{j \in \mathcal{P}} x_j$$

$$\text{s.a.} \quad \sum_{j \in \mathcal{P}} a_{ij} \, x_j \geq d_i, \quad \forall i \in I$$

$$x_j \geq 0, \quad \forall j \in \mathcal{P}$$

**Sub-problema — Mochila Inteira (teste de otimalidade)**

$$z^* = \max \quad \sum_{i \in I} \pi_i y_i$$

$$\text{s.a.} \quad \sum_{i \in I} w_i \, y_i \leq W$$

$$y_i \geq 0, \quad y_i \in \mathbb{Z}, \quad \forall i \in I$$

> Nova coluna é adicionada ao Mestre se $z^* > 1$.
> Após convergência, resolve-se o Mestre inteiro (MIP) com todas as colunas geradas.

---

## Estrutura de arquivos

```
cutting-stock-1d/
├── README.md
├── exact/
│   ├── instance.py              ← dataclasses: CuttingStockInstance, Solution
│   ├── model_pyomo.py           ← Geração de Colunas com Pyomo + HiGHS
│   └── model_gurobi.py          ← gurobipy (opcional — requer licença)
├── notebooks/
│   ├── 01_formulacao.ipynb
│   └── 02_geracao_de_colunas.ipynb
├── instances/
│   ├── small_3.json             ← 3 tipos de peça
│   └── medium_7.json            ← 7 tipos de peça
└── results/
    └── benchmark.md
```

---

## Como executar

### Python (Pyomo + HiGHS)

```bash
pip install pyomo highspy numpy
python exact/model_pyomo.py instances/small_3.json
```

### Gurobi (opcional)

```bash
pip install gurobipy
python exact/model_gurobi.py instances/small_3.json
```

---

## Formato de instância (JSON)

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

## Referências

- Gilmore, P. C., Gomory, R. E. (1961). A linear programming approach to
  the cutting stock problem. *Operations Research*, 9(6), 849–859.
- Gilmore, P. C., Gomory, R. E. (1963). A linear programming approach to
  the cutting stock problem — Part II. *Operations Research*, 11(6), 863–888.
- Uchoa, E., Pessoa, A., Moreno, M. (2024). *Column Generation*. Springer.
