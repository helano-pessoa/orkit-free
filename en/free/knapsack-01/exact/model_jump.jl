"""
    Knapsack 0/1 — JuMP Model (Binary Integer Programming)

Formulation:

    max  Σᵢ pᵢ xᵢ
    s.t. Σᵢ wᵢ xᵢ ≤ C
         xᵢ ∈ {0, 1},  ∀ i ∈ I

Supported solvers (uncomment the desired optimizer in `build_model`):
    HiGHS  — default (open-source, recommended)
    GLPK   — alternative for small didactic examples
    SCIP   — hard instances

Install dependencies (Julia REPL):
    ] add JuMP HiGHS JSON3

Gurobi (optional, requires license):
    ] add Gurobi
    # In build_model, replace: HiGHS.Optimizer → Gurobi.Optimizer

References:
    Kellerer, H., Pferschy, U., Pisinger, D. (2004). Knapsack Problems. Springer.
    Martello, S., Toth, P. (1990). Knapsack Problems. Wiley.
"""
module Knapsack01

using JuMP
using HiGHS
using JSON3

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

"""
    Item

Represents an item available for selection in the knapsack.

# Fields
- `id::Int`: Unique item identifier.
- `weight::Float64`: Item weight (same unit as capacity).
- `profit::Float64`: Profit gained by selecting the item.
"""
struct Item
    id::Int
    weight::Float64
    profit::Float64
end

"""
    Instance

Complete data for a 0/1 Knapsack problem instance.

# Fields
- `name::String`: Descriptive instance name.
- `capacity::Float64`: Maximum knapsack capacity.
- `items::Vector{Item}`: List of available items.
- `optimal_value::Union{Float64,Nothing}`: Known optimal value (nothing if unknown).
"""
struct Instance
    name::String
    capacity::Float64
    items::Vector{Item}
    optimal_value::Union{Float64,Nothing}
end

"""
    Solution

Solution of the 0/1 Knapsack problem.

# Fields
- `selected_items::Vector{Int}`: IDs of selected items.
- `total_profit::Float64`: Total profit of the optimal solution.
- `total_weight::Float64`: Total weight of selected items.
- `status::String`: Solver termination status.
"""
struct Solution
    selected_items::Vector{Int}
    total_profit::Float64
    total_weight::Float64
    status::String
end

# ---------------------------------------------------------------------------
# Instance loading
# ---------------------------------------------------------------------------

"""
    load_instance(path::String) -> Instance

Load an instance from a JSON file.

# Arguments
- `path`: Path to the `.json` instance file.

# Returns
Populated `Instance` object.

# Example
```julia
inst = Knapsack01.load_instance("instances/small_5.json")
println(inst.capacity)   # 10.0
```
"""
function load_instance(path::String)::Instance
    data = JSON3.read(read(path, String))
    items = [Item(it.id, Float64(it.weight), Float64(it.profit)) for it in data.items]
    optimal = haskey(data, :optimal_value) ? Float64(data.optimal_value) : nothing
    return Instance(String(data.name), Float64(data.capacity), items, optimal)
end

# ---------------------------------------------------------------------------
# JuMP model
# ---------------------------------------------------------------------------

"""
    build_model(inst::Instance; optimizer=HiGHS.Optimizer) -> Model

Build the JuMP model for the 0/1 Knapsack problem.

# Arguments
- `inst`: Instance with capacity and item list.
- `optimizer`: JuMP optimizer. Default: `HiGHS.Optimizer`.
  Alternatives: `GLPK.Optimizer`, `SCIP.Optimizer`.
  Optional (requires license): `Gurobi.Optimizer`.

# Returns
JuMP model ready to be solved.
"""
function build_model(inst::Instance; optimizer=HiGHS.Optimizer)::Model
    n = length(inst.items)
    model = Model(optimizer)
    set_silent(model)

    # Binary decision variables: x[i] ∈ {0, 1}
    @variable(model, x[1:n], Bin)

    # Objective: maximize total profit
    @objective(model, Max, sum(inst.items[i].profit * x[i] for i in 1:n))

    # Capacity constraint
    @constraint(
        model,
        capacity_constraint,
        sum(inst.items[i].weight * x[i] for i in 1:n) <= inst.capacity
    )

    return model
end

# ---------------------------------------------------------------------------
# Solve
# ---------------------------------------------------------------------------

"""
    solve(inst::Instance; optimizer=HiGHS.Optimizer, verbose::Bool=false) -> Solution

Solve the 0/1 Knapsack instance.

# Arguments
- `inst`: Instance to be solved.
- `optimizer`: JuMP optimizer. Default: `HiGHS.Optimizer`.
- `verbose`: If `true`, stream solver log to stdout. Default: `false`.

# Returns
`Solution` object with selected items and optimal profit.

# Throws
- `ErrorException` if the solver does not find an optimal or feasible solution.

# Example
```julia
inst = Knapsack01.load_instance("instances/small_5.json")
sol  = Knapsack01.solve(inst)
println("Optimal profit: \$(sol.total_profit)")
```
"""
function solve(
    inst::Instance;
    optimizer=HiGHS.Optimizer,
    verbose::Bool=false,
)::Solution
    model = build_model(inst; optimizer=optimizer)
    verbose && unset_silent(model)

    optimize!(model)

    status = string(termination_status(model))
    if !(status in ["OPTIMAL", "FEASIBLE_POINT"])
        error("Solver terminated with status '$status'. Check the instance.")
    end

    x_val = value.(model[:x])
    selected = [inst.items[i].id for i in 1:length(inst.items) if x_val[i] > 0.5]
    profit = objective_value(model)
    weight = sum(
        inst.items[i].weight
        for i in 1:length(inst.items)
        if x_val[i] > 0.5;
        init=0.0
    )

    return Solution(selected, profit, weight, status)
end

# ---------------------------------------------------------------------------
# Output utilities
# ---------------------------------------------------------------------------

"""
    print_solution(inst::Instance, sol::Solution)

Print a formatted solution summary to stdout.
"""
function print_solution(inst::Instance, sol::Solution)
    println("\nInstance   : $(inst.name)")
    println("Items      : $(length(inst.items))   |   Capacity: $(inst.capacity)")
    println("-"^45)
    println("Status     : $(sol.status)")
    println("Selected   : $(sol.selected_items)")
    println("Tot. weight: $(sol.total_weight)")
    println("Tot. profit: $(sol.total_profit)")

    if inst.optimal_value !== nothing
        gap = (inst.optimal_value - sol.total_profit) / inst.optimal_value * 100.0
        @printf("Gap        : %.2f%%  (reference: %.1f)\n", gap, inst.optimal_value)
    end
end

end  # module Knapsack01

# ---------------------------------------------------------------------------
# Standalone execution: julia model_jump.jl [instance_path]
# ---------------------------------------------------------------------------
if abspath(PROGRAM_FILE) == @__FILE__
    using Printf
    path = length(ARGS) > 0 ? ARGS[1] : "instances/small_5.json"
    inst = Knapsack01.load_instance(path)
    sol = Knapsack01.solve(inst)
    Knapsack01.print_solution(inst, sol)
end
