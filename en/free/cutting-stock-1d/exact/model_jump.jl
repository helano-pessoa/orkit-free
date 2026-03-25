"""
    1D Cutting Stock Problem — JuMP Model with Column Generation

Algorithm (Gilmore & Gomory, 1961):
    1. Initialize with trivial patterns (one item type per pattern).
    2. Solve the LP-relaxed Master Problem → get shadow prices π.
    3. Solve the Subproblem (Integer Knapsack) with profits π.
    4. If z* > 1 + ε, add new column and repeat.
    5. Solve the Integer Master (MIP) with all generated columns.

Supported solvers (change `optimizer` in calls below):
    HiGHS  — default (open-source, recommended)
    GLPK   — didactic alternative
    Gurobi — optional (requires license)

Dependencies:
    Pkg.add(["JuMP", "HiGHS", "JSON3"])
"""
module CuttingStock1D

using JuMP
using HiGHS
using JSON3

const EPSILON = 1.0e-6

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

"""
    ItemType

Represents a piece type to be cut from the master roll.

# Fields
- `id::Int`: Unique identifier for this item type.
- `width::Float64`: Item width.
- `demand::Int`: Quantity demanded.
"""
struct ItemType
    id::Int
    width::Float64
    demand::Int
end

"""
    Instance

Full data for a 1D Cutting Stock Problem instance.

# Fields
- `name::String`: Descriptive instance name.
- `master_roll::Float64`: Master roll width.
- `items::Vector{ItemType}`: Item types with width and demand.
"""
struct Instance
    name::String
    master_roll::Float64
    items::Vector{ItemType}
end

"""
    Solution

Result of solving the 1D Cutting Stock Problem.

# Fields
- `n_rolls::Float64`: Number of master rolls cut.
- `patterns::Matrix{Float64}`: Pattern matrix (m × K).
- `quantities::Vector{Float64}`: Usage of each pattern.
- `status::String`: Solver termination status.
"""
struct Solution
    n_rolls::Float64
    patterns::Matrix{Float64}
    quantities::Vector{Float64}
    status::String
end

# ---------------------------------------------------------------------------
# Instance loading
# ---------------------------------------------------------------------------

"""
    load_instance(path::String) -> Instance

Load an instance from a JSON file.

# Example
```julia
inst = load_instance("instances/small_3.json")
```
"""
function load_instance(path::String)::Instance
    data = JSON3.read(read(path, String))
    items = [ItemType(p.id, p.width, p.demand) for p in data.items]
    return Instance(data.name, data.master_roll, items)
end

# ---------------------------------------------------------------------------
# LP-relaxed Master Problem
# ---------------------------------------------------------------------------

"""
    _solve_master_lp(patterns, demands, W; optimizer) -> (x, pi)

Solve the LP-relaxed Master Problem and return shadow prices.
"""
function _solve_master_lp(
    patterns::Matrix{Float64},
    demands::Vector{Int},
    W::Float64;
    optimizer=HiGHS.Optimizer,
)
    m, n_cols = size(patterns)
    mdl = Model(optimizer)
    set_silent(mdl)

    @variable(mdl, x[1:n_cols] >= 0)
    @objective(mdl, Min, sum(x))
    @constraint(mdl, dem[i=1:m], sum(patterns[i, j] * x[j] for j in 1:n_cols) >= demands[i])

    optimize!(mdl)

    x_vals = value.(x)
    pi_vals = dual.(dem)  # shadow prices

    return x_vals, pi_vals
end

# ---------------------------------------------------------------------------
# Subproblem: Integer Knapsack
# ---------------------------------------------------------------------------

"""
    _solve_subproblem(widths, pi, W; optimizer) -> (z_star, new_pattern)

Solve the Subproblem (Integer Knapsack) with shadow prices as profits.
"""
function _solve_subproblem(
    widths::Vector{Float64},
    pi_vals::Vector{Float64},
    W::Float64;
    optimizer=HiGHS.Optimizer,
)
    m = length(widths)
    mdl = Model(optimizer)
    set_silent(mdl)

    @variable(mdl, y[1:m] >= 0, Int)
    @objective(mdl, Max, sum(pi_vals[i] * y[i] for i in 1:m))
    @constraint(mdl, sum(widths[i] * y[i] for i in 1:m) <= W)

    optimize!(mdl)

    z_star = objective_value(mdl)
    new_pattern = value.(y)

    return z_star, new_pattern
end

# ---------------------------------------------------------------------------
# Main solver
# ---------------------------------------------------------------------------

"""
    solve(inst::Instance; optimizer=HiGHS.Optimizer, verbose::Bool=false) -> Solution

Solve the 1D Cutting Stock Problem via Column Generation.

# Arguments
- `inst`: Instance to solve.
- `optimizer`: JuMP optimizer. Default: `HiGHS.Optimizer`.
- `verbose`: If `true`, prints progress to the terminal. Default: `false`.

# Returns
`Solution` object with roll count and cutting patterns.

# Example
```julia
inst = load_instance("instances/small_3.json")
sol  = solve(inst)
println("Rolls cut: \$(sol.n_rolls)")
```
"""
function solve(
    inst::Instance;
    optimizer=HiGHS.Optimizer,
    verbose::Bool=false,
)::Solution
    m = length(inst.items)
    widths = [p.width for p in inst.items]
    demands = [p.demand for p in inst.items]
    W = inst.master_roll

    # Trivial initial patterns (diagonal)
    max_per_type = [Int(floor(W / l)) for l in widths]
    patterns = Float64.(Diagonal(max_per_type))

    iter = 0
    # --- Column Generation ---
    while true
        iter += 1
        _, pi = _solve_master_lp(patterns, demands, W; optimizer=optimizer)
        z_star, new_col = _solve_subproblem(widths, pi, W; optimizer=optimizer)

        verbose && println("  [CG iter $iter] z* = $(round(z_star; digits=4))  |  columns = $(size(patterns, 2))")

        if z_star <= 1.0 + EPSILON
            break
        end
        patterns = hcat(patterns, new_col)
    end

    verbose && println("[CG] Converged with $(size(patterns, 2)) patterns. Solving MIP...")

    # --- Final MIP ---
    n_cols = size(patterns, 2)
    mdl_mip = Model(optimizer)
    set_silent(mdl_mip)
    verbose && unset_silent(mdl_mip)

    @variable(mdl_mip, x[1:n_cols] >= 0, Int)
    @objective(mdl_mip, Min, sum(x))
    @constraint(mdl_mip, dem[i=1:m], sum(patterns[i, j] * x[j] for j in 1:n_cols) >= demands[i])

    optimize!(mdl_mip)

    status = string(termination_status(mdl_mip))
    n_rolls = objective_value(mdl_mip)
    qtds = value.(x)

    return Solution(n_rolls, patterns, qtds, status)
end

# ---------------------------------------------------------------------------
# Print results
# ---------------------------------------------------------------------------

"""
    print_solution(inst::Instance, sol::Solution)

Display cutting patterns and total rolls to the terminal.
"""
function print_solution(inst::Instance, sol::Solution)
    m, n_cols = size(sol.patterns)
    println("\nInstance     : $(inst.name)")
    println("Master roll  : $(inst.master_roll)")
    println("Item types   : $(length(inst.items))")
    println("-" ^ 45)
    println("Status       : $(sol.status)")
    println("Patterns gen.: $n_cols")
    println("Rolls cut    : $(Int(round(sol.n_rolls)))")
    println("\nPattern usage:")
    for j in 1:n_cols
        qty = sol.quantities[j]
        if qty > 0.5
            pattern = [Int(round(sol.patterns[i, j])) for i in 1:m]
            println("  Pattern $(lpad(j, 2)): $(pattern) × $(Int(round(qty)))")
        end
    end
end

end  # module CuttingStock1D


# ---------------------------------------------------------------------------
# Direct execution: julia model_jump.jl [instance.json]
# ---------------------------------------------------------------------------
using LinearAlgebra  # for Diagonal

if abspath(PROGRAM_FILE) == @__FILE__
    using .CuttingStock1D
    path = length(ARGS) > 0 ? ARGS[1] : "instances/small_3.json"
    inst = CuttingStock1D.load_instance(path)
    sol  = CuttingStock1D.solve(inst; verbose=true)
    CuttingStock1D.print_solution(inst, sol)
end


Algoritmo (Gilmore & Gomory, 1961):
    1. Iniciar com padrões triviais.
    2. Resolver Mestre LP relaxado → obter preços-sombra π.
    3. Resolver Sub-problema (Mochila Inteira) com lucros π.
    4. Se z* > 1 + ε, adicionar nova coluna e repetir.
    5. Resolver Mestre Inteiro (MIP) com todas as colunas.

Solvers suportados (alterar `optimizer` nas chamadas abaixo):
    HiGHS  — padrão (open-source, recomendado)
    GLPK   — alternativo didático
    Gurobi — opcional (requer licença)

Dependências:
    Pkg.add(["JuMP", "HiGHS", "JSON3"])
"""
module CorteEstoque1D

using JuMP
using HiGHS
using JSON3

const EPSILON = 1.0e-6

# ---------------------------------------------------------------------------
# Estruturas de dados
# ---------------------------------------------------------------------------

"""
    TipoPeca

Representa um tipo de peça a ser cortada do rolo-mestre.

# Campos
- `id::Int`: Identificador único do tipo.
- `largura::Float64`: Largura da peça.
- `demanda::Int`: Quantidade demandada.
"""
struct TipoPeca
    id::Int
    largura::Float64
    demanda::Int
end

"""
    Instancia

Dados completos da instância do Problema de Corte de Estoque 1D.

# Campos
- `nome::String`: Nome descritivo da instância.
- `rolo_mestre::Float64`: Largura do rolo-mestre.
- `pecas::Vector{TipoPeca}`: Tipos de peças demandadas.
"""
struct Instancia
    nome::String
    rolo_mestre::Float64
    pecas::Vector{TipoPeca}
end

"""
    Solucao

Resultado da resolução do Problema de Corte de Estoque 1D.

# Campos
- `n_rolos::Float64`: Número de rolos-mestre cortados.
- `padroes::Matrix{Float64}`: Matriz de padrões (m × K).
- `quantidades::Vector{Float64}`: Uso de cada padrão.
- `status::String`: Status de terminação do solver.
"""
struct Solucao
    n_rolos::Float64
    padroes::Matrix{Float64}
    quantidades::Vector{Float64}
    status::String
end

# ---------------------------------------------------------------------------
# Carregamento de instância
# ---------------------------------------------------------------------------

"""
    carregar_instancia(caminho::String) -> Instancia

Carrega uma instância a partir de um arquivo JSON.

# Exemplo
```julia
inst = carregar_instancia("instances/small_3.json")
```
"""
function carregar_instancia(caminho::String)::Instancia
    dados = JSON3.read(read(caminho, String))
    pecas = [TipoPeca(p.id, p.width, p.demand) for p in dados.items]
    return Instancia(dados.name, dados.master_roll, pecas)
end

# ---------------------------------------------------------------------------
# Problema Mestre LP relaxado
# ---------------------------------------------------------------------------

"""
    _resolver_mestre_lp(padroes, demandas, W; optimizer) -> (x, pi)

Resolve o Problema Mestre LP relaxado e retorna os preços-sombra.
"""
function _resolver_mestre_lp(
    padroes::Matrix{Float64},
    demandas::Vector{Int},
    W::Float64;
    optimizer=HiGHS.Optimizer,
)
    m, n_cols = size(padroes)
    mdl = Model(optimizer)
    set_silent(mdl)

    @variable(mdl, x[1:n_cols] >= 0)
    @objective(mdl, Min, sum(x))
    @constraint(mdl, dem[i=1:m], sum(padroes[i, j] * x[j] for j in 1:n_cols) >= demandas[i])

    optimize!(mdl)

    x_vals = value.(x)
    pi_vals = dual.(dem)  # preços-sombra

    return x_vals, pi_vals
end

# ---------------------------------------------------------------------------
# Sub-problema: Mochila Inteira
# ---------------------------------------------------------------------------

"""
    _resolver_subproblema(larguras, pi, W; optimizer) -> (z_star, novo_padrao)

Resolve o Sub-problema (Mochila Inteira) com os preços-sombra como lucros.
"""
function _resolver_subproblema(
    larguras::Vector{Float64},
    pi_vals::Vector{Float64},
    W::Float64;
    optimizer=HiGHS.Optimizer,
)
    m = length(larguras)
    mdl = Model(optimizer)
    set_silent(mdl)

    @variable(mdl, y[1:m] >= 0, Int)
    @objective(mdl, Max, sum(pi_vals[i] * y[i] for i in 1:m))
    @constraint(mdl, sum(larguras[i] * y[i] for i in 1:m) <= W)

    optimize!(mdl)

    z_star = objective_value(mdl)
    novo_padrao = value.(y)

    return z_star, novo_padrao
end

# ---------------------------------------------------------------------------
# Resolução principal
# ---------------------------------------------------------------------------

"""
    resolver(inst::Instancia; optimizer=HiGHS.Optimizer, verbose::Bool=false) -> Solucao

Resolve o Problema de Corte de Estoque 1D via Geração de Colunas.

# Argumentos
- `inst`: Instância a ser resolvida.
- `optimizer`: Otimizador JuMP. Padrão: `HiGHS.Optimizer`.
- `verbose`: Se `true`, exibe progresso no terminal.

# Retorna
Objeto `Solucao` com a quantidade de rolos e os padrões de corte.

# Exemplo
```julia
inst = carregar_instancia("instances/small_3.json")
sol  = resolver(inst)
println("Rolos cortados: \$(sol.n_rolos)")
```
"""
function resolver(
    inst::Instancia;
    optimizer=HiGHS.Optimizer,
    verbose::Bool=false,
)::Solucao
    m = length(inst.pecas)
    larguras = [p.largura for p in inst.pecas]
    demandas = [p.demanda for p in inst.pecas]
    W = inst.rolo_mestre

    # Padrões iniciais triviais (diagonal)
    max_por_tipo = [Int(floor(W / l)) for l in larguras]
    padroes = Float64.(Diagonal(max_por_tipo))

    iter = 0
    # --- Geração de Colunas ---
    while true
        iter += 1
        _, pi = _resolver_mestre_lp(padroes, demandas, W; optimizer=optimizer)
        z_star, novo = _resolver_subproblema(larguras, pi, W; optimizer=optimizer)

        verbose && println("  [CG iter $iter] z* = $(round(z_star; digits=4))  |  colunas = $(size(padroes, 2))")

        if z_star <= 1.0 + EPSILON
            break
        end
        padroes = hcat(padroes, novo)
    end

    verbose && println("[CG] Convergido com $(size(padroes, 2)) padrões. Resolvendo MIP...")

    # --- MIP final ---
    n_cols = size(padroes, 2)
    mdl_mip = Model(optimizer)
    set_silent(mdl_mip)
    verbose && unset_silent(mdl_mip)

    @variable(mdl_mip, x[1:n_cols] >= 0, Int)
    @objective(mdl_mip, Min, sum(x))
    @constraint(mdl_mip, dem[i=1:m], sum(padroes[i, j] * x[j] for j in 1:n_cols) >= demandas[i])

    optimize!(mdl_mip)

    status = string(termination_status(mdl_mip))
    n_rolos = objective_value(mdl_mip)
    qtds = value.(x)

    return Solucao(n_rolos, padroes, qtds, status)
end

# ---------------------------------------------------------------------------
# Impressão de resultados
# ---------------------------------------------------------------------------

"""
    imprimir_solucao(inst::Instancia, sol::Solucao)

Exibe os padrões de corte e o total de rolos cortados.
"""
function imprimir_solucao(inst::Instancia, sol::Solucao)
    m, n_cols = size(sol.padroes)
    println("\nInstância    : $(inst.nome)")
    println("Rolo-mestre  : $(inst.rolo_mestre)")
    println("Tipos de peça: $(length(inst.pecas))")
    println("-" ^ 45)
    println("Status       : $(sol.status)")
    println("Padrões ger. : $n_cols")
    println("Rolos cortad.: $(Int(round(sol.n_rolos)))")
    println("\nUso dos padrões:")
    for j in 1:n_cols
        qty = sol.quantidades[j]
        if qty > 0.5
            padrao = [Int(round(sol.padroes[i, j])) for i in 1:m]
            println("  Padrão $(lpad(j, 2)): $(padrao) × $(Int(round(qty)))")
        end
    end
end

end  # module CorteEstoque1D


# ---------------------------------------------------------------------------
# Execução direta: julia model_jump.jl [instancia.json]
# ---------------------------------------------------------------------------
using LinearAlgebra  # para Diagonal

if abspath(PROGRAM_FILE) == @__FILE__
    using .CorteEstoque1D
    caminho = length(ARGS) > 0 ? ARGS[1] : "instances/small_3.json"
    inst = CorteEstoque1D.carregar_instancia(caminho)
    sol  = CorteEstoque1D.resolver(inst; verbose=true)
    CorteEstoque1D.imprimir_solucao(inst, sol)
end
