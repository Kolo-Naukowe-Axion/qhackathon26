"""Classical reference on one offered paired-meal QUBO, not the raw kitchen.

Enforce the proven zero-penalty constraints and minimize the same quadratic
objective. The compiler's penalty proof makes this equivalent to minimizing
the literal QUBO. This reference reads the conflict graph; raw native_slots
is the independent reference that does not.
"""
import math
import time

from .contracts import method_result
from .decode import decode
from .qubo import energy, objective_energy, validate_bundle


def solve_bundle(bundle, seconds=5, seed=2026):
    from ortools.sat.python import cp_model

    start = time.monotonic()
    validate_bundle(bundle)
    if bundle.get("encoding") != "paired-course-anchor-onehot.v1":
        raise ValueError("Paired-course block encoding required")
    if not math.isfinite(seconds) or seconds <= 0:
        raise ValueError("Positive finite end-to-end budget required")
    obj = bundle["objective"]
    magnitude = abs(int(obj["constant"])) + sum(abs(int(c)) for c in obj["linear"])
    magnitude += sum(abs(int(t["value"])) for t in obj["quadratic"])
    if magnitude >= 2**62:
        raise ValueError("Objective exceeds the conservative CP integer range")
    model = cp_model.CpModel()
    bits = [model.NewBoolVar(f"x{i}") for i in range(bundle["size"]["binary_variables"])]
    idle = {g["idle_index"] for g in bundle["onehot_groups"]}
    for i, bit in enumerate(bits):
        model.AddHint(bit, int(i in idle))
    for group in bundle["onehot_groups"]:
        model.AddExactlyOne(bits[i] for i in group["indices"])
    for i, j in bundle["conflicts"]:
        model.Add(bits[i] + bits[j] <= 1)
    objective = int(obj["constant"]) + sum(int(c)*x for c, x in zip(obj["linear"], bits))
    for k, term in enumerate(obj["quadratic"]):
        product = model.NewBoolVar(f"product{k}")
        model.AddMultiplicationEquality(product, [bits[term["i"]], bits[term["j"]]])
        objective += int(term["value"])*product
    model.Minimize(objective)
    build_s = time.monotonic() - start
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = max(0.001, seconds-build_s)
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = seed
    status = solver.Solve(model) if build_s < seconds else cp_model.UNKNOWN
    name = solver.StatusName(status)
    samples, checked, value = [], None, None
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        selected = [solver.Value(x) for x in bits]
        checked = decode(bundle, selected)
        value = energy(bundle, selected)
        if not checked["valid"] or value != objective_energy(bundle, selected) or value != solver.Value(objective):
            raise AssertionError("Reference disagrees with literal energy or raw checker")
        samples = [dict(bits=selected, count=1, reported_energy=str(value))]
    ref = dict(status=name, objective=None if value is None else str(value),
               bound=str(value) if name == "OPTIMAL" else solver.BestObjectiveBound() if build_s < seconds else None,
               scope="Identical offered paired-meal domain; exact zero-penalty constraints",
               reads_qubo_conflict_list=True, raw_kitchen_reference=False)
    result = method_result(bundle, "paired_program_cp", samples,
                           timings=dict(build_s=build_s, solver_s=solver.WallTime() if build_s < seconds else 0,
                                        total_s=time.monotonic()-start),
                           work=dict(workers=1, product_auxiliaries=len(obj["quadratic"]),
                                     note="Classical CP products are not QUBO data qubits"), reference=ref)
    result["configuration"] = dict(seed=seed, wall_time_limit_s=seconds, initializer="All-idle partial hint", repair=False)
    result["status"] = "completed" if samples else "timeout"
    result["check"] = None if checked is None else checked["check"]
    return result
