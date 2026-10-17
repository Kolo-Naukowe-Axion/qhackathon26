"""Normalize no samples silently; decode and check every returned decision."""
from collections import Counter
from .check import check_plan
from .domain import make_plan, residual_demand
from .qubo import checked_bits, energy, objective_energy


def decode(bundle, bits):
    checked_bits(bundle, bits)
    instance, state = bundle["instance"], bundle["snapshot"]
    chosen = [p for x, p in zip(bits, bundle["options"]) if x]
    plan = make_plan(instance, state["fixed_batches"] + chosen)
    raw = check_plan(instance, state, plan)
    coverage = Counter(g for p in chosen for g in p["allocation_order"])
    register_ok = all(
        coverage[r["demand_group"]] + sum(bits[i]*w for i, w in zip(r["indices"], r["weights"]))
        == residual_demand(state)[r["demand_group"]] for r in bundle["registers"])
    literal, objective = energy(bundle, bits), objective_energy(bundle, bits)
    expected = (sum(bundle["objective"]["weights"][k]*raw["metrics"][k] for k in ("U", "W", "B", "R"))
                if raw["valid"] else None)
    valid = raw["valid"] and register_ok and literal == objective and objective == expected
    return dict(valid=valid, physical_valid=raw["valid"], register_valid=register_ok,
                energy=str(literal), objective_energy=str(objective), check=raw, plan=plan)
