"""
    Mochila 0/1 — Modelo JuMP (Programação Inteira Binária)

Formulação:

    max  Σᵢ pᵢ xᵢ
    s.a. Σᵢ wᵢ xᵢ ≤ C
         xᵢ ∈ {0, 1},  ∀ i ∈ I

Solvers suportados (descomentar a linha desejada em `resolver`):
    HiGHS  — padrão (open-source, recomendado)
    GLPK   — alternativo para exemplos pequenos
    SCIP   — instâncias difíceis

Instalação de dependências (Julia REPL):
    ] add JuMP HiGHS JSON3

Gurobi (opcional, requer licença):
    ] add Gurobi
    # Em construir_modelo, substituir: HiGHS.Optimizer → Gurobi.Optimizer

Referências:
    Kellerer, H., Pferschy, U., Pisinger, D. (2004). Knapsack Problems. Springer.
    Martello, S., Toth, P. (1990). Knapsack Problems. Wiley.
"""
module Mochila01

using JuMP
using HiGHS
using JSON3

# ---------------------------------------------------------------------------
# Estruturas de dados
# ---------------------------------------------------------------------------

"""
    Item

Representa um item disponível para seleção na mochila.

# Campos
- `id::Int`: Identificador único do item.
- `weight::Float64`: Peso do item (mesma unidade da capacidade).
- `profit::Float64`: Lucro obtido ao selecionar o item.
"""
struct Item
    id::Int
    weight::Float64
    profit::Float64
end

"""
    Instancia

Dados completos de uma instância do Problema da Mochila 0/1.

# Campos
- `name::String`: Nome descritivo da instância.
- `capacity::Float64`: Capacidade máxima da mochila.
- `items::Vector{Item}`: Lista de itens disponíveis.
- `optimal_value::Union{Float64,Nothing}`: Ótimo conhecido (nada se desconhecido).
"""
struct Instancia
    name::String
    capacity::Float64
    items::Vector{Item}
    optimal_value::Union{Float64,Nothing}
end

"""
    Solucao

Solução do Problema da Mochila 0/1.

# Campos
- `itens_selecionados::Vector{Int}`: IDs dos itens selecionados.
- `lucro_total::Float64`: Lucro total da solução ótima.
- `peso_total::Float64`: Peso total dos itens selecionados.
- `status::String`: Status de terminação do solver.
"""
struct Solucao
    itens_selecionados::Vector{Int}
    lucro_total::Float64
    peso_total::Float64
    status::String
end

# ---------------------------------------------------------------------------
# Carregamento de instância
# ---------------------------------------------------------------------------

"""
    carregar_instancia(caminho::String) -> Instancia

Carrega uma instância a partir de um arquivo JSON.

# Argumentos
- `caminho`: Caminho para o arquivo `.json` da instância.

# Retorna
Objeto `Instancia` populado com os dados do arquivo.

# Exemplo
```julia
inst = Mochila01.carregar_instancia("instances/small_5.json")
println(inst.capacity)   # 10.0
```
"""
function carregar_instancia(caminho::String)::Instancia
    dados = JSON3.read(read(caminho, String))
    itens = [Item(it.id, Float64(it.weight), Float64(it.profit)) for it in dados.items]
    otimo = haskey(dados, :optimal_value) ? Float64(dados.optimal_value) : nothing
    return Instancia(String(dados.name), Float64(dados.capacity), itens, otimo)
end

# ---------------------------------------------------------------------------
# Modelo JuMP
# ---------------------------------------------------------------------------

"""
    construir_modelo(inst::Instancia; optimizer=HiGHS.Optimizer) -> Model

Constrói o modelo JuMP para o Problema da Mochila 0/1.

# Argumentos
- `inst`: Instância com capacidade e lista de itens.
- `optimizer`: Otimizador a ser usado. Padrão: `HiGHS.Optimizer`.
  Alternativas: `GLPK.Optimizer`, `SCIP.Optimizer`.
  Opcional (requer licença): `Gurobi.Optimizer`.

# Retorna
Modelo JuMP construído e pronto para ser resolvido.
"""
function construir_modelo(inst::Instancia; optimizer=HiGHS.Optimizer)::Model
    n = length(inst.items)
    model = Model(optimizer)
    set_silent(model)

    # Variáveis de decisão binárias: x[i] ∈ {0, 1}
    @variable(model, x[1:n], Bin)

    # Função objetivo: maximizar o lucro total
    @objective(model, Max, sum(inst.items[i].profit * x[i] for i in 1:n))

    # Restrição de capacidade
    @constraint(
        model,
        rest_capacidade,
        sum(inst.items[i].weight * x[i] for i in 1:n) <= inst.capacity
    )

    return model
end

# ---------------------------------------------------------------------------
# Resolução
# ---------------------------------------------------------------------------

"""
    resolver(inst::Instancia; optimizer=HiGHS.Optimizer, verbose::Bool=false) -> Solucao

Resolve a instância do Problema da Mochila 0/1.

# Argumentos
- `inst`: Instância a ser resolvida.
- `optimizer`: Otimizador JuMP. Padrão: `HiGHS.Optimizer`.
- `verbose`: Se `true`, exibe o log do solver. Padrão: `false`.

# Retorna
Objeto `Solucao` com os itens selecionados e o lucro ótimo.

# Lança
- `ErrorException` se o solver não encontrar solução ótima ou viável.

# Exemplo
```julia
inst = Mochila01.carregar_instancia("instances/small_5.json")
sol  = Mochila01.resolver(inst)
println("Lucro ótimo: \$(sol.lucro_total)")
```
"""
function resolver(
    inst::Instancia;
    optimizer=HiGHS.Optimizer,
    verbose::Bool=false,
)::Solucao
    model = construir_modelo(inst; optimizer=optimizer)
    verbose && unset_silent(model)

    optimize!(model)

    status = string(termination_status(model))
    if !(status in ["OPTIMAL", "FEASIBLE_POINT"])
        error("Solver encerrou com status '$status'. Verifique a instância.")
    end

    x_val = value.(model[:x])
    itens_sel = [inst.items[i].id for i in 1:length(inst.items) if x_val[i] > 0.5]
    lucro = objective_value(model)
    peso = sum(
        inst.items[i].weight
        for i in 1:length(inst.items)
        if x_val[i] > 0.5;
        init=0.0
    )

    return Solucao(itens_sel, lucro, peso, status)
end

# ---------------------------------------------------------------------------
# Utilidades de saída
# ---------------------------------------------------------------------------

"""
    imprimir_solucao(inst::Instancia, sol::Solucao)

Imprime um resumo formatado da solução no terminal.
"""
function imprimir_solucao(inst::Instancia, sol::Solucao)
    println("\nInstância  : $(inst.name)")
    println("Itens      : $(length(inst.items))   |   Capacidade: $(inst.capacity)")
    println("-"^45)
    println("Status     : $(sol.status)")
    println("Itens sel. : $(sol.itens_selecionados)")
    println("Peso total : $(sol.peso_total)")
    println("Lucro total: $(sol.lucro_total)")

    if inst.optimal_value !== nothing
        gap = (inst.optimal_value - sol.lucro_total) / inst.optimal_value * 100.0
        @printf("Gap ótimo  : %.2f%%  (referência: %.1f)\n", gap, inst.optimal_value)
    end
end

end  # module Mochila01

# ---------------------------------------------------------------------------
# Execução standalone: julia model_jump.jl [caminho_instancia]
# ---------------------------------------------------------------------------
if abspath(PROGRAM_FILE) == @__FILE__
    using Printf
    caminho = length(ARGS) > 0 ? ARGS[1] : "instances/small_5.json"
    inst = Mochila01.carregar_instancia(caminho)
    sol = Mochila01.resolver(inst)
    Mochila01.imprimir_solucao(inst, sol)
end
