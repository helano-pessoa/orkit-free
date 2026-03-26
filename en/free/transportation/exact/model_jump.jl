"""
Transportation Problem -- JuMP + HiGHS (LP).

    min   sum_{i,j} c[i,j] * x[i,j]
    s.t.  sum_j x[i,j] <= s[i]   for all i   (supply)
          sum_i x[i,j] >= d[j]   for all j   (demand)
          x[i,j] >= 0

Run:
    julia model_jump.jl ../instances/small_3x4.json
"""

using JuMP, HiGHS, JSON3

struct Supplier
    id::Int
    supply::Float64
end

struct Customer
    id::Int
    demand::Float64
end

struct TransportInstance
    name::String
    suppliers::Vector{Supplier}
    customers::Vector{Customer}
    costs::Matrix{Float64}
end

function load_instance(path::String)::TransportInstance
    data = JSON3.read(read(path, String))
    suppliers = [Supplier(s.id, s.supply) for s in data.suppliers]
    customers = [Customer(c.id, c.demand) for c in data.customers]
    m, n = length(suppliers), length(customers)
    costs = [Float64(data.costs[i][j]) for i in 1:m, j in 1:n]
    return TransportInstance(data.name, suppliers, customers, costs)
end

function solve(inst::TransportInstance)
    m, n = length(inst.suppliers), length(inst.customers)
    s = [inst.suppliers[i].supply for i in 1:m]
    d = [inst.customers[j].demand for j in 1:n]
    c = inst.costs

    model = Model(HiGHS.Optimizer)
    set_silent(model)

    @variable(model, x[1:m, 1:n] >= 0)
    @objective(model, Min, sum(c[i, j] * x[i, j] for i in 1:m, j in 1:n))

    # Supply constraints
    @constraint(model, supply[i in 1:m], sum(x[i, j] for j in 1:n) <= s[i])
    # Demand constraints
    @constraint(model, demand[j in 1:n], sum(x[i, j] for i in 1:m) >= d[j])

    optimize!(model)

    status = string(termination_status(model))
    total_cost = objective_value(model)
    plan = value.(x)
    return (status=status, total_cost=total_cost, plan=plan)
end

function main()
    path = length(ARGS) > 0 ? ARGS[1] : "../instances/small_3x4.json"
    inst = load_instance(path)
    result = solve(inst)
    println("Status    : $(result.status)")
    println("Total cost: $(round(result.total_cost, digits=2))")
    println("Plan (rows=suppliers, cols=customers):")
    for i in 1:size(result.plan, 1)
        println(join([@sprintf("%7.2f", result.plan[i, j]) for j in 1:size(result.plan, 2)], " "))
    end
end

main()
