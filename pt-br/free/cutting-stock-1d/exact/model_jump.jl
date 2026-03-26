"""
Corte de Estoque 1D -- Formulacao MIP Compacta com JuMP + HiGHS

Formulacao:
    min   sum_n  y_n
    s.a.  sum_n  x[i,n]  >= d[i]           para todo i  (demanda)
          sum_i  w[i] * x[i,n]  <= W*y[n]  para todo n  (capacidade)
          y[n] binario,  x[i,n] inteiro >= 0

N_max = sum(d[i]): cota superior trivial.

Dependencias:
    ] add JuMP HiGHS JSON3

Referencias:
    Kantorovich (1960). Mathematical Methods of Organising and Planning Production.
    Wascher et al. (2007). EJOR, 183(3), 1109-1130.
"""

using JuMP, HiGHS, JSON3

# ---------------------------------------------------------------------------
# Estruturas de dados
# ---------------------------------------------------------------------------

struct TipoPeca
    id::Int
    largura::Float64
    demanda::Int
end

struct InstanciaCS
    nome::String
    rolo_mestre::Float64
    pecas::Vector{TipoPeca}
end

function carregar_instancia(caminho::String)::InstanciaCS
    dados = JSON3.read(read(caminho, String))
    pecas = [TipoPeca(p.id, p.width, p.demand) for p in dados.items]
    InstanciaCS(dados.name, dados.master_roll, pecas)
end

# ---------------------------------------------------------------------------
# Modelo e resolucao
# ---------------------------------------------------------------------------

function resolver(inst::InstanciaCS; verbose::Bool = false)
    W = inst.rolo_mestre
    pecas = inst.pecas
    m = length(pecas)
    ids = [p.id for p in pecas]
    w = Dict(p.id => p.largura for p in pecas)
    d = Dict(p.id => p.demanda for p in pecas)
    n_max = sum(p.demanda for p in pecas)  # cota superior

    model = Model(HiGHS.Optimizer)
    !verbose && set_silent(model)

    # Variaveis
    @variable(model, y[1:n_max], Bin)                         # rolo n aberto?
    @variable(model, x[ids, 1:n_max] >= 0, Int)               # pecas por rolo

    # Objetivo: minimizar rolos usados
    @objective(model, Min, sum(y))

    # Restricoes de demanda
    for i in ids
        @constraint(model, sum(x[i, n] for n = 1:n_max) >= d[i])
    end

    # Restricoes de capacidade
    for n = 1:n_max
        @constraint(model, sum(w[i] * x[i, n] for i in ids) <= W * y[n])
    end

    optimize!(model)

    status = termination_status(model)
    rolos = Int(round(objective_value(model)))

    println("Status : $status")
    println("Rolos  : $rolos")
    for n = 1:n_max
        if value(y[n]) > 0.5
            pat = Dict(i => Int(round(value(x[i, n]))) for i in ids if value(x[i, n]) > 0.5)
            !isempty(pat) && println("  Rolo $n: $pat")
        end
    end
end

# ---------------------------------------------------------------------------
# Execucao
# ---------------------------------------------------------------------------

caminho = length(ARGS) >= 1 ? ARGS[1] : "../instances/small_3.json"
inst = carregar_instancia(caminho)
resolver(inst)
