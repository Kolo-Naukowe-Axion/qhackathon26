"""Local-penalty variants of frozen paired-meal QUBO bundles (offline study).

The frozen compiler uses one global penalty P = (sum of all absolute objective
coefficients) + 1, so P grows with the whole problem. Here each constraint gets
its own penalty from the objective coefficients of the variables it touches:

    L_i     = |a_i| + sum_j |b_ij|                      (objective terms only)
    lambda_g = 1 + max_{k in g} L_k                      one-hot block g
    mu_ij    = 1 + min(L_i + L_idle(i), L_j + L_idle(j)) cross-block conflict

Every infeasible state then has a 1- or 2-flip neighbour with strictly lower
energy: drop a surplus choice or add the idle bit (penalty falls by >= lambda_g,
objective rises by <= L_k), or replace one end of a conflict by its block's idle
bit (penalty falls by >= mu_ij, objective rises by <= L_i + L_idle). Hence every
minimum is feasible, at any width, and the feasible energies equal the objective.

Variant "local": same lexicographic (U,W,B,R) objective.
Variant "local-uw": objective (bound_W + 1)*U + W only. B and R are linear in the
choices (B = programs chosen, R = |previous| - kept previous + new), so they are
subtracted exactly; the compiler's weights satisfy w_U = w_W*(bound_W + 1), so the
rest divides exactly by w_W. B/R are then tie-breaks after decoding.

The source bundle is never modified; each variant records its parent hash.
"""
import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

from ..contracts import load_bundle
from ..domain import digest
from ..qubo import energy, objective_energy, validate_bundle

VARIANTS = ("local", "local-uw")


def objective_terms(bundle):
    o = bundle["objective"]
    return (int(o["constant"]), list(map(int, o["linear"])),
            {(t["i"], t["j"]): int(t["value"]) for t in o.get("quadratic", [])})


def uw_objective(bundle):
    """Exact (bound_W + 1)*U + W from the frozen U,W,B,R objective."""
    constant, linear, quadratic = objective_terms(bundle)
    w, bounds = bundle["objective"]["weights"], bundle["objective"]["component_bounds"]
    previous = {p["id"] for p in bundle["snapshot"]["previous_unstarted"]}
    constant -= w["R"]*len(previous)
    for i, p in enumerate(bundle["options"]):
        linear[i] -= w["B"] + w["R"]*(-1 if p["id"] in previous else 1)
    if w["U"] != w["W"]*(bounds["W"] + 1):
        raise ValueError("Unexpected weight structure")
    values = [constant] + linear + list(quadratic.values())
    if any(v % w["W"] for v in values):
        raise ValueError("U,W objective is not an exact multiple of w_W")
    weights = dict(U=bounds["W"] + 1, W=1, B=0, R=0)
    return (constant//w["W"], [v//w["W"] for v in linear],
            {k: v//w["W"] for k, v in quadratic.items()}, weights)


def objective_reach(linear, quadratic):
    reach = [abs(v) for v in linear]
    for (i, j), v in quadratic.items():
        reach[i] += abs(v); reach[j] += abs(v)
    return reach


def local_penalties(bundle, linear, quadratic):
    reach = objective_reach(linear, quadratic)
    groups = bundle["onehot_groups"]
    idle_of = {i: g["idle_index"] for g in groups for i in g["program_indices"]}
    lam = [1 + max(reach[k] for k in g["indices"]) for g in groups]
    mu = {(i, j): 1 + min(reach[i] + reach[idle_of[i]], reach[j] + reach[idle_of[j]])
          for i, j in map(tuple, bundle["conflicts"])}
    return lam, mu


def build_variant(bundle, variant, margin=1):
    """margin >= 1 multiplies every local penalty; the feasibility proof still holds."""
    if variant not in VARIANTS:
        raise ValueError(f"Unknown variant {variant}")
    if bundle.get("encoding") != "paired-course-anchor-onehot.v1" or bundle.get("registers"):
        raise ValueError("Paired-meal one-hot bundle without registers required")
    if variant == "local":
        constant, linear, quadratic = objective_terms(bundle)
        weights = dict(bundle["objective"]["weights"])
    else:
        constant, linear, quadratic, weights = uw_objective(bundle)
    if type(margin) is not int or margin < 1:
        raise ValueError("Integer margin >= 1 required")
    lam, mu = local_penalties(bundle, linear, quadratic)
    lam, mu = [margin*v for v in lam], {k: margin*v for k, v in mu.items()}
    objective = dict(constant=str(constant), linear=list(map(str, linear)),
                     quadratic=[dict(i=i, j=j, value=str(v)) for (i, j), v in sorted(quadratic.items()) if v],
                     weights=weights, component_bounds=bundle["objective"]["component_bounds"])
    full_constant, full_linear, pairs = constant, linear.copy(), defaultdict(int, quadratic)
    for (i, j), m in mu.items():
        pairs[(i, j)] += m
    for g, penalty in zip(bundle["onehot_groups"], lam):
        full_constant += penalty
        for k, i in enumerate(g["indices"]):
            full_linear[i] -= penalty
            for j in g["indices"][k+1:]:
                pairs[tuple(sorted((i, j)))] += 2*penalty
    pairs = {k: v for k, v in pairs.items() if v}
    out = {k: v for k, v in bundle.items() if k != "bundle_sha256"}
    suffix = "-" + variant_name(variant, margin)
    out.update(bundle_id=bundle["bundle_id"] + suffix, representation_id=bundle["representation_id"] + suffix,
               parent_sha256=bundle["bundle_sha256"],
               parent_domain_kind="Frozen source bundle; same options, variables, groups and conflicts",
               constant=str(full_constant), linear=list(map(str, full_linear)),
               quadratic=[dict(i=i, j=j, value=str(v)) for (i, j), v in sorted(pairs.items())],
               objective=objective, penalty=str(max(lam + list(mu.values()))),
               penalty_policy=dict(kind="local", variant=variant, margin=margin,
                                   onehot=dict(min=str(min(lam)), max=str(max(lam))),
                                   conflict=dict(min=str(min(mu.values(), default=0)),
                                                 max=str(max(mu.values(), default=0)))),
               penalty_proof=("Each penalty exceeds the objective change of a 1- or 2-flip move that removes it "
                              "(see catering/methods/veloxq_penalty.py); every minimum is feasible"),
               size={**bundle["size"], "couplers": len(pairs), "objective_couplers": len(objective["quadratic"])})
    out["bundle_sha256"] = digest(out)
    return validate_bundle(out)


def variant_name(variant, margin=1):
    return variant if margin == 1 else f"{variant}-m{margin}"


def check_variant(variant_bundle, source, bits_list, *, rng=None, trials=200):
    """Feasible states keep their meaning; infeasible states have a strictly better neighbour."""
    for bits in bits_list:
        e = energy(variant_bundle, bits)
        if e != objective_energy(variant_bundle, bits):
            raise AssertionError("Feasible state carries a penalty")
        if objective_energy(source, bits) != energy(source, bits):
            raise AssertionError("Source witness is not feasible")
    rng = rng or random.Random(2026)
    groups = variant_bundle["onehot_groups"]
    _, linear, quadratic = objective_terms(variant_bundle)
    reach = objective_reach(linear, quadratic)
    idle_of = {i: g["idle_index"] for g in groups for i in g["program_indices"]}
    conflict_of = defaultdict(list)
    for i, j in variant_bundle["conflicts"]:
        conflict_of[i].append(j); conflict_of[j].append(i)
    full_linear = list(map(int, variant_bundle["linear"]))
    neighbors = defaultdict(list)
    for t in variant_bundle["quadratic"]:
        neighbors[t["i"]].append((t["j"], int(t["value"]))); neighbors[t["j"]].append((t["i"], int(t["value"])))
    n = len(full_linear)
    for _ in range(trials):
        bits = [int(rng.random() < 0.15) for _ in range(n)]
        start = energy(variant_bundle, bits)
        current = start
        for _ in range(4*n):
            move = _repair_move(bits, groups, conflict_of, idle_of, reach)
            if move is None:
                break
            delta = 0
            for i, value in move:
                if bits[i] != value:
                    delta += (1 - 2*bits[i])*(full_linear[i] + sum(v*bits[j] for j, v in neighbors[i]))
                    bits[i] = value
            if delta >= 0:
                raise AssertionError("Repair move did not lower the energy")
            current += delta
        else:
            raise AssertionError("Repair did not terminate")
        if current != energy(variant_bundle, bits) or current != objective_energy(variant_bundle, bits) or current >= start:
            raise AssertionError("Repaired state is not a cheaper feasible state")
    return True


def _repair_move(bits, groups, conflict_of, idle_of, reach):
    for g in groups:
        chosen = [i for i in g["indices"] if bits[i]]
        if not chosen:
            return [(g["idle_index"], 1)]
        if len(chosen) > 1:
            return [(chosen[0], 0)]
    for g in groups:
        for i in g["program_indices"]:
            if bits[i]:
                for j in conflict_of[i]:
                    if bits[j]:
                        # Drop the end whose replacement by idle can raise the objective least.
                        k = min((i, j), key=lambda v: reach[v] + reach[idle_of[v]])
                        return [(k, 0), (idle_of[k], 1)]
    return None


def coefficient_stats(bundle):
    values = [abs(int(v)) for v in bundle["linear"]] + [abs(int(t["value"])) for t in bundle["quadratic"]]
    nonzero = [v for v in values if v]
    w = bundle["objective"]["weights"]
    return dict(max_abs=max(nonzero), min_nonzero_abs=min(nonzero), dynamic_range=max(nonzero)/min(nonzero),
                penalty_max=int(bundle["penalty"]), penalty_over_w_U=int(bundle["penalty"])/w["U"])


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--bundle", required=True, nargs="+")
    parser.add_argument("--output", required=True, help="New directory")
    parser.add_argument("--margins", type=int, nargs="+", default=[1], help="Penalty margins for every variant")
    args = parser.parse_args()
    names = [(v, m, variant_name(v, m)) for m in args.margins for v in VARIANTS]
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    rows = []
    for path in args.bundle:
        source = load_bundle(path)
        witnesses = []
        stem = Path(path).parent / Path(path).name.replace("-qubo.json", "")
        for ref in (Path(f"{stem}-reference.json"), Path(f"{stem}-witness.json"),
                    Path(path).parent/"reference-encoded.json"):
            if ref.exists():
                data = json.loads(ref.read_text())
                if data.get("bundle_sha256") not in (None, source["bundle_sha256"]):
                    continue
                witnesses += [s["bits"] for s in data.get("samples", [])] + ([data["bits"]] if "bits" in data else [])
        row = dict(source=str(path), source_sha256=source["bundle_sha256"], source_stats=coefficient_stats(source))
        for variant, margin, key in names:
            built = build_variant(source, variant, margin)
            check_variant(built, source, witnesses)
            name = Path(path).parent.name + "-" + Path(path).name.replace("-qubo.json", f"-{key}-qubo.json")
            (output/name).write_text(json.dumps(built, sort_keys=True) + "\n")
            row[key] = dict(file=name, bundle_sha256=built["bundle_sha256"], stats=coefficient_stats(built),
                                witnesses_checked=len(witnesses))
        rows.append(row)
        print(row["source"], {k: round(row[k]["stats"]["penalty_over_w_U"], 1) for _, _, k in names})
    (output/"build-report.json").write_text(json.dumps(dict(variants=[k for _, _, k in names], rows=rows), indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
