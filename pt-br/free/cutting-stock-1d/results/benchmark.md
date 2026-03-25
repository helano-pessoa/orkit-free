# Benchmark — Corte de Estoque 1D

Geração de Colunas (Gilmore & Gomory) + MIP final.

| Instância              | Tipos | Rolo-mestre | Padrões gerados | Rolos cortados | Pyomo/HiGHS (s) | JuMP/HiGHS (s) |
|------------------------|-------|-------------|-----------------|----------------|-----------------|----------------|
| `small_3.json`         | 3     | 100         | —               | —              | —               | —              |
| `medium_7.json`        | 7     | 200         | —               | —              | —               | —              |

> Execute os modelos e preencha a tabela com seus resultados.
>
> ```bash
> python exact/model_pyomo.py instances/small_3.json
> python exact/model_pyomo.py instances/medium_7.json
> ```
>
> ```bash
> julia exact/model_jump.jl instances/small_3.json
> julia exact/model_jump.jl instances/medium_7.json
> ```

## Notas

- **Padrões gerados**: total de colunas (padrões de corte) ao final da Geração de Colunas.
- **Rolos cortados**: valor ótimo do MIP final — número mínimo de rolos-mestre necessários.
- O Problema Mestre LP relaxado fornece o limitante inferior (fracional).
- A solução inteira pode ter `gap ≤ 1` em relação ao limitante (fenômeno do *integrality gap*).
