"""
1D Cutting Stock -- Compact MIP formulation with JuMP + HiGHS

Formulation:
    min   sum_n  y_n
    s.t.  sum_n  x[i,n]  >= d[i]           for all i  (demand)
          sum_i  w[i] * x[i,n]  <= W*y[n]  for all n  (capacity)
          y[n] binary,  x[i,n] integer >= 0

N_max = sum(d[i]): trivial upper bound.

Dependencies:
    ] add JuMP HiGHS JSON3

References:
    Kantorovich (1960). Mathematical Methods of Organising and Planning Production.
    Wascher et al. (2007). EJOR, 183(3), 1109-1130.
"""

using JuMP, HiGHS, JSON3

struct ItemType
    id::Int
    width::Float64
    demand::Int
end

struct CuttingStockInstance
    name::String
    master_roll::Float64
    items::Vector{ItemType}
end

function load_instance(path::String)::CuttingStockInstance
    data = JSON3.read(read(path, String))
    items = [ItemType(it.id, it.width, it.demand) for it in data.items]
    CuttingStockInstance(data.name, data.master_roll, items)
end

function solve(inst::CuttingStockInstance; verbose::Bool = false)
    W = inst.master_roll
    items = inst.items
    ids = [it.id for it in items]
    w = Dict(it.id => it.width for it in items)
    d = Dict(it.id => it.demand for it in items)
    n_max = sum(it.demand for it in items)

    model = Model(HiGHS.Optimizer)
    !verbose && set_silent(model)

    @variable(model, y[1:n_max], Bin)
    @variable(model, x[ids, 1:n_max] >= 0, Int)

    @objective(model, Min, sum(y))

    for i in ids
        @constraint(model, sum(x[i, n] for n = 1:n_max) >= d[i])
    end

    for n = 1:n_max
        @constraint(model, sum(w[i] * x[i, n] for i in ids) <= W * y[n])
    end

    optimize!(model)

    status = termination_status(model)
    rolls = Int(round(objective_value(model)))

    println("Status : $status")
    println("Rolls  : $rolls")
    for n = 1:n_max
        if value(y[n]) > 0.5
            pat = Dict(i => Int(round(value(x[i, n]))) for i in ids if value(x[i, n]) > 0.5)
            !isempty(pat) && println("  Roll $n: $pat")
        end
    end
end

path = length(ARGS) >= 1 ? ARGS[1] : "../instances/small_3.json"
inst = load_instance(path)
solve(inst)
