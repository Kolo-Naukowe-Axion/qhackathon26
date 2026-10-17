"""Native optional-interval master for the declared complete program domain.

Resources are enforced from raw operation intervals, not QUBO pair penalties.
Program generation is shared and independently audited; this is not a native
unrestricted batch-slot model or the ambitious flagship.
"""
import math
import time
from collections import defaultdict
from .check import check_plan
from .contracts import method_result
from .decode import decode
from .domain import make_plan, residual_demand
from .qubo import energy


def bits_for_selection(bundle, selected):
    n = bundle["size"]["binary_variables"]
    bits = [0] * n
    for i in selected:
        bits[i] = 1
    chosen = [bundle["options"][i] for i in selected]
    for r in bundle["registers"]:
        remaining = residual_demand(bundle["snapshot"])[r["demand_group"]]
        remaining -= sum(p["allocation_order"].count(r["demand_group"]) for p in chosen)
        if not 0 <= remaining <= r["maximum"]:
            raise ValueError("Selection over-serves demand")
        # Deterministic encoding. Bounded binary lengths are small.
        found = False
        for mask in range(1 << len(r["indices"])):
            code = [(mask >> j) & 1 for j in range(len(r["indices"]))]
            if sum(a*b for a, b in zip(code, r["weights"])) == remaining:
                for i, value in zip(r["indices"], code):
                    bits[i] = value
                found = True
                break
        if not found:
            raise AssertionError("Unrepresentable bounded value")
    return bits


def solve_program_master(bundle, budget=None, method_config=None, output_dir=None):
    from ortools.sat.python import cp_model
    start = time.monotonic()
    budget = budget or {}
    limit = float(budget.get("wall_time_limit_s", 10))
    if not math.isfinite(limit) or limit <= 0:
        raise ValueError("Positive finite time limit required")
    instance, state = bundle["instance"], bundle["snapshot"]
    model = cp_model.CpModel()
    choices = [model.NewBoolVar(f"option-{i}") for i in range(len(bundle["options"]))]
    occupancy = defaultdict(list)
    fixed = make_plan(instance, state["fixed_batches"])
    if not check_plan(instance, state, fixed)["valid"]:
        raise ValueError("Invalid committed boundary")
    def add_operations(plan, presence, prefix):
        for op in plan["operations"]:
            for resource, end in [(op["resource"], op["end"]), (op["worker"], op["attended_end"])]:
                name = prefix + op["id"] + resource
                if presence is None:
                    interval = model.NewIntervalVar(op["start"], end-op["start"], end, name)
                else:
                    interval = model.NewOptionalIntervalVar(op["start"], end-op["start"], end, presence, name)
                occupancy[resource].append(interval)
    add_operations(fixed, None, "fixed:")
    for i, program in enumerate(bundle["options"]):
        # Recheck raw calendar/qualifications/material behavior; no conflict-list use.
        if not check_plan(instance, state, make_plan(instance, state["fixed_batches"] + [program]))["valid"]:
            raise ValueError("Invalid offered raw program")
        add_operations(make_plan(instance, [program]), choices[i], "new:")
    for intervals in occupancy.values():
        model.AddNoOverlap(intervals)
    objective = int(bundle["objective"]["constant"])
    objective += sum(int(bundle["objective"]["linear"][i])*x for i, x in enumerate(choices))
    priorities = {d["id"]: d["priority"] for d in state["demand_groups"]}
    for group, amount in residual_demand(state).items():
        missed = model.NewIntVar(0, amount, "missed:" + group)
        model.Add(sum(p["allocation_order"].count(group)*choices[i] for i, p in enumerate(bundle["options"])) + missed == amount)
        objective += bundle["objective"]["weights"]["U"] * priorities[group] * missed
    model.Minimize(objective)
    build_time = time.monotonic() - start
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = limit
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = int((method_config or {}).get("seed", 2026))
    status = solver.Solve(model)
    name = solver.StatusName(status)
    samples, optimum = [], None
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        bits = bits_for_selection(bundle, [i for i, x in enumerate(choices) if solver.Value(x)])
        checked = decode(bundle, bits)
        if not checked["valid"]:
            raise AssertionError("Native result failed literal/independent checks")
        optimum = energy(bundle, bits)
        samples = [dict(bits=bits, count=1, reported_energy=str(optimum))]
    ref = dict(status=name, objective=None if optimum is None else str(optimum),
               bound=str(optimum) if name == "OPTIMAL" else str(solver.BestObjectiveBound()),
               scope="Native optional-interval master on the bundle's declared program domain",
               reads_qubo_conflict_list=False, shared_program_generator=True)
    result = method_result(bundle, "native_cp_optional_intervals", samples,
                           timings=dict(build_s=build_time, solver_s=solver.WallTime(),
                                        total_s=time.monotonic()-start),
                           work=dict(workers=1, branches=solver.NumBranches()), reference=ref)
    if name not in ("OPTIMAL", "FEASIBLE"):
        result["status"] = "timeout" if name == "UNKNOWN" else "failed"
    return result


def solve_native(instance, snapshot, budget=None, config=None, output_dir=None):
    """Raw-input wrapper. Explicitly still a complete program-domain master."""
    from .options import enumerate_options
    from .qubo import compile_qubo
    start = time.monotonic()
    bundle = compile_qubo(instance, snapshot, enumerate_options(instance, snapshot))
    result = solve_program_master(bundle, budget, config, output_dir)
    result["timings"]["raw_input_total_s"] = time.monotonic()-start
    result["reference"]["scope"] = "Complete contiguous-packing grid programs; not unrestricted packing"
    if result["samples"]:
        checked = decode(bundle, result["samples"][0]["bits"])
        result["plan"] = checked["plan"]
        result["check"] = checked["check"]
    return result
