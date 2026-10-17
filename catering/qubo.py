"""Exact integer literal QUBO, bounded registers and Pauli-Z conversion."""
from collections import Counter
from .domain import digest, make_plan, residual_demand
from .options import claims, conflict


def bounded_weights(limit):
    if type(limit) is not int or limit < 0:
        raise ValueError("Nonnegative integer register bound required")
    if not limit:
        return []
    length = limit.bit_length()
    return [1 << i for i in range(length - 1)] + [limit - ((1 << (length - 1)) - 1)]


def compile_qubo(instance, state, programs, *, representation="complete-core-grid", parent_sha256=None):
    from .check import check_plan
    for p in programs:
        if not p["allocation_order"] or not check_plan(instance, state, make_plan(instance, state["fixed_batches"] + [p]))["valid"]:
            raise ValueError("Compiler accepts only individually valid nonempty programs")
    order = [p["id"] for p in programs]
    if len(order) != len(set(order)):
        raise ValueError("Duplicate options")
    remaining = residual_demand(state)
    variables = ["option:" + key for key in order]
    registers, regterms = [], {}
    for group, bound in sorted(remaining.items()):
        weights = bounded_weights(bound)
        indices = list(range(len(variables), len(variables) + len(weights)))
        variables += [f"missed:{group}:{j}" for j in range(len(weights))]
        registers.append(dict(purpose="missed_lots", demand_group=group, indices=indices,
                              weights=weights, minimum=0, maximum=bound))
        regterms[group] = list(zip(indices, weights))
    n = len(variables)
    previous = {p["id"] for p in state["previous_unstarted"]}
    fixed_waste = sum(b["yield_lots"] - len(b["allocation_order"]) for b in state["fixed_batches"])
    bounds = dict(U=sum(d["priority"] * remaining.get(d["id"], 0) for d in state["demand_groups"]),
                  W=fixed_waste + sum(p["yield_lots"] - len(p["allocation_order"]) for p in programs),
                  B=len(programs), R=len(programs) + len(previous))
    weights = {}
    for key in reversed(("U", "W", "B", "R")):
        weights[key] = 1 + sum(weights[k] * bounds[k] for k in weights)
    objective_constant = fixed_waste * weights["W"] + len(previous) * weights["R"]
    objective = [0] * n
    for i, p in enumerate(programs):
        objective[i] = ((p["yield_lots"] - len(p["allocation_order"])) * weights["W"]
                        + weights["B"] + (-1 if p["id"] in previous else 1) * weights["R"])
    priorities = {d["id"]: d["priority"] for d in state["demand_groups"]}
    for group, terms in regterms.items():
        for i, value in terms:
            objective[i] = priorities[group] * weights["U"] * value
    bound = objective_constant + sum(max(0, c) for c in objective)
    penalty = bound + 1
    linear, pairs, constant = objective.copy(), {}, objective_constant
    def pair(i, j, value):
        key = (min(i, j), max(i, j))
        if i == j:
            linear[i] += value
        else:
            pairs[key] = pairs.get(key, 0) + value
    def square(terms, target):
        nonlocal constant
        constant += penalty * target * target
        for i, value in terms:
            linear[i] += penalty * (value * value - 2 * target * value)
        for a, (i, u) in enumerate(terms):
            for j, v in terms[a+1:]:
                pair(i, j, 2 * penalty * u * v)
    coverage = [Counter(p["allocation_order"]) for p in programs]
    for group, demand in sorted(remaining.items()):
        terms = [(i, row[group]) for i, row in enumerate(coverage) if row[group]] + regterms[group]
        square(terms, demand)
    option_claims = [claims(instance, p) for p in programs]
    conflicts = []
    for i in range(len(programs)):
        for j in range(i + 1, len(programs)):
            if conflict(option_claims[i], option_claims[j]):
                conflicts.append([i, j])
                pair(i, j, penalty)
    pairs = {k: v for k, v in pairs.items() if v}
    bundle = dict(
        schema_version="catering-qubo.v1", bundle_id=instance["instance_id"] + "/" + state["scenario_id"] + "/" + representation,
        case_id=instance["instance_id"] + "/" + state["scenario_id"], profile_id=instance["profile_id"],
        scenario_id=state["scenario_id"], instance_sha256=digest(instance), snapshot_sha256=digest(state),
        representation_id=representation, parent_sha256=parent_sha256,
        scope="Complete only on this profile's finite grid" if parent_sha256 is None else "Lossy deterministic option restriction",
        instance=instance, snapshot=state, options=programs, variable_order=variables,
        registers=registers, constant=str(constant), linear=[str(c) for c in linear],
        quadratic=[dict(i=i, j=j, value=str(v)) for (i, j), v in sorted(pairs.items())],
        objective=dict(constant=str(objective_constant), linear=[str(c) for c in objective],
                       weights=weights, component_bounds=bounds, upper_bound=str(bound)),
        penalty=str(penalty), conflicts=conflicts,
        size=dict(binary_variables=n, option_bits=len(programs), shortfall_bits=n-len(programs),
                  capacity_bits=0, auxiliary_bits=0, couplers=len(pairs)),
        coefficients=dict(max_abs=max([abs(constant)] + [abs(c) for c in linear] + [abs(v) for v in pairs.values()])),
        disabled_features=["phase_aware_WIP", "interrupted_cooking", "ingredients", "holding", "power", "money"],
    )
    bundle["bundle_sha256"] = digest(bundle)
    return bundle


def validate_bundle(bundle):
    if bundle.get("schema_version") != "catering-qubo.v1":
        raise ValueError("Unsupported bundle schema")
    if digest({k: v for k, v in bundle.items() if k != "bundle_sha256"}) != bundle["bundle_sha256"]:
        raise ValueError("Bundle hash mismatch")
    if digest(bundle["instance"]) != bundle["instance_sha256"] or digest(bundle["snapshot"]) != bundle["snapshot_sha256"]:
        raise ValueError("Raw input hash mismatch")
    n = len(bundle["variable_order"])
    if len(set(bundle["variable_order"])) != n or len(bundle["linear"]) != n or bundle["size"]["binary_variables"] != n:
        raise ValueError("Variable-map mismatch")
    seen = set()
    for term in bundle["quadratic"]:
        i, j = term["i"], term["j"]
        if not 0 <= i < j < n or (i, j) in seen:
            raise ValueError("Invalid quadratic pair")
        seen.add((i, j))
    return bundle


def checked_bits(bundle, bits):
    if len(bits) != len(bundle["linear"]) or any(type(x) is not int or x not in (0, 1) for x in bits):
        raise ValueError("Expected normalized integer bits in variable_order")
    return bits


def energy(bundle, bits):
    checked_bits(bundle, bits)
    return (int(bundle["constant"]) + sum(int(c)*x for c, x in zip(bundle["linear"], bits))
            + sum(int(t["value"])*bits[t["i"]]*bits[t["j"]] for t in bundle["quadratic"]))


def objective_energy(bundle, bits):
    checked_bits(bundle, bits)
    return int(bundle["objective"]["constant"]) + sum(int(c)*x for c, x in zip(bundle["objective"]["linear"], bits))


def ising(bundle):
    """Coefficients of 4H; 4E(x)=offset+sum h_i*z_i+sum J_ij*z_i*z_j."""
    fields = [-2*int(c) for c in bundle["linear"]]
    offset = 4*int(bundle["constant"]) + 2*sum(map(int, bundle["linear"]))
    edges = []
    for term in bundle["quadratic"]:
        i, j, v = term["i"], term["j"], int(term["value"])
        fields[i] -= v
        fields[j] -= v
        offset += v
        edges.append(dict(i=i, j=j, value=str(v)))
    return dict(schema_version="catering-ising.v1", source_bundle_sha256=bundle["bundle_sha256"],
                convention="z=1-2*x", energy_scale=4, constant=str(offset),
                linear=list(map(str, fields)), quadratic=edges, variable_order=bundle["variable_order"])
