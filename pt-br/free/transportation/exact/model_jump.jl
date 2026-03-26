"""
Problema de Transporte -- Formulacao LP com JuMP + HiGHS

Formulacao:
    min   sum_{i,j}  c[i,j] * x[i,j]
    s.a.  sum_j x[i,j] <= s[i]    para todo i  (oferta)
          sum_i x[i,j] >= d[j]    para todo j  (demanda)
          x[i,j] >= 0

Dependencias:
    ] add JuMP HiGHS JSON3

Referencias:
    Hitchcock (1941). Journal of Mathematics and Physics, 20(1), 224-230.
    Dantzig (1963). Linear Programming and Extensions. Princeton UP.
"""

using JuMP, HiGHS, JSON3

struct Fornecedor
    id::Int
    supply::Float64
end

struct Cliente
    id::Int
    demand::Float64
end

struct InstanciaTransporte
    name::String
    suppliers::Vector{Fornecedor}
    customers::Vector{Cliente}
    costs::Matrix{Float64}
end

function carregar_instancia(path::String)::InstanciaTransporte
    data = JSON3.read(read(path, String))
    suppliers = [Fornecedor(s.id, s.supply) for s in data.suppliers]
    customers = [Cliente(c.id, c.demand) for c in data.customers]
    m, n = length(suppliers), length(customers)
    costs = Matrix{Float64}(undef, m, n)
    for (i, row) in enumerate(data.costs)
        for (j, v) in enumerate(row)
            costs[i, j] = v
        end
    end
    InstanciaTransporte(data.name, suppliers, customers, costs)
end

function resolver(inst::InstanciaTransporte; verbose::Bool = false)
    m, n = length(inst.suppliers), length(inst.customers)
    supply = [s.supply for s in inst.suppliers]
    demand = [c.demand for c in inst.customers]
    c = inst.costs

    model = Model(HiGHS.Optimizer)
    !verbose && set_silent(model)

    @variable(model, x[1:m, 1:n] >= 0)

    @objective(model, Min, sum(c[i, j] * x[i, j] for i = 1:m, j = 1:n))

    for i = 1:m
        @constraint(model, sum(x[i, j] for j = 1:n) <= supply[i])
    end
    for j = 1:n
        @constraint(model, sum(x[i, j] for i = 1:m) >= demand[j])
    end

    optimize!(model)

    status = termination_status(model)
    custo = objective_value(model)

    println("Status     : $status")
    println("Custo Total: $(round(custo, digits=2))")
    for i = 1:m, j = 1:n
        v = value(x[i, j])
        v > 1e-9 && println("  x[$i,$j] = $(round(v, digits=1))")
    end
end

path = length(ARGS) >= 1 ? ARGS[1] : "../instances/small_3x4.json"
inst = carregar_instancia(path)
resolver(inst)
