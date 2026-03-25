# Benchmark — Mochila 0/1

> Resultados obtidos em: **a preencher após execução**
> Hardware: **a preencher**
> Solver padrão: HiGHS (via Pyomo `appsi_highs`)

---

## Instâncias

| Instância | Itens | Capacidade | Ótimo | Status |
|---|---|---|---|---|
| `small_5.json` | 5 | 10 | 40 | ✅ Verificado |
| `medium_15.json` | 15 | 50 | — | — |
| `large_50.json` | 50 | 200 | — | — |

---

## Resultados Pyomo + HiGHS

| Instância | Lucro encontrado | Gap (%) | Tempo (s) |
|---|---|---|---|
| small_5 | — | — | — |
| medium_15 | — | — | — |
| large_50 | — | — | — |

## Resultados JuMP + HiGHS (Julia)

| Instância | Lucro encontrado | Gap (%) | Tempo (s) |
|---|---|---|---|
| small_5 | — | — | — |
| medium_15 | — | — | — |
| large_50 | — | — | — |

---

## Como reproduzir

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
