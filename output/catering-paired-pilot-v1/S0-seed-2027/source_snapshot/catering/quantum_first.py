"""Unit-demand batch-selection QUBO and conflict-preserving mixer semantics.

Each data qubit chooses a complete local batch program, not a full kitchen plan.
No optimization method or reference solution is used to build the representation.
"""
from collections import Counter
import math

from .check import check_plan
from .domain import digest, make_plan, residual_demand, validate_instance
from .options import claims, conflict
from .qubo import validate_bundle


def compile_unit_qubo(instance, state, programs, *, representation="unit-demand-complete", parent_sha256=None):
    validate_instance(instance)
    if instance.get("service_model"):
        raise ValueError("Complete meals require the paired-course objective compiler")
    remaining = residual_demand(state)
    if any(q != 1 for q in remaining.values()):
        raise ValueError("Slack-free encoding requires unit residual demand groups")
    fixed = state["fixed_batches"]
    if not check_plan(instance,state,make_plan(instance,fixed,state.get("recovery_operations",[])))["valid"]:
        raise ValueError("Invalid committed boundary")
    ids = [p["id"] for p in programs]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate batch programs")
    coverage = []
    for p in programs:
        covered = Counter(p["allocation_order"])
        if not covered or any(g not in remaining or q != 1 for g,q in covered.items()):
            raise ValueError("Each program must serve distinct residual unit groups")
        if not check_plan(instance,state,make_plan(instance,fixed+[p],state.get("recovery_operations",[])))["valid"]:
            raise ValueError("Invalid local batch program")
        coverage.append(set(covered))
    n = len(programs)
    previous = {p["id"] for p in state["previous_unstarted"]}
    priorities = {d["id"]:d["priority"] for d in state["demand_groups"]}
    fixed_waste = sum(p["yield_lots"]-len(p["allocation_order"]) for p in fixed)
    bounds = dict(U=sum(priorities[g] for g in remaining),
                  W=fixed_waste+sum(p["yield_lots"]-len(p["allocation_order"]) for p in programs),
                  B=n,R=n+len(previous))
    weights = {}
    for key in reversed(("U","W","B","R")):
        weights[key] = 1+sum(weights[k]*bounds[k] for k in weights)
    constant = weights["U"]*bounds["U"]+weights["W"]*fixed_waste+weights["R"]*len(previous)
    linear = [-(weights["U"]*sum(priorities[g] for g in covered))
              +weights["W"]*(p["yield_lots"]-len(p["allocation_order"]))
              +weights["B"]+weights["R"]*(-1 if p["id"] in previous else 1)
              for p,covered in zip(programs,coverage)]
    # Invalid selections can receive negative duplicate-service rewards, so the
    # old nonnegative-objective penalty bound is not sufficient for this form.
    lower = constant+sum(min(0,c) for c in linear)
    upper = constant+sum(max(0,c) for c in linear)
    penalty = upper-lower+1
    occupations = [claims(instance,p) for p in programs]
    edges = [[i,j] for i in range(n) for j in range(i+1,n)
             if coverage[i]&coverage[j] or conflict(occupations[i],occupations[j])]
    bundle = dict(schema_version="catering-qubo.v1",
        bundle_id=instance["instance_id"]+"/"+state["scenario_id"]+"/"+representation,
        case_id=instance["instance_id"]+"/"+state["scenario_id"],profile_id=instance["profile_id"],
        scenario_id=state["scenario_id"],instance_sha256=digest(instance),snapshot_sha256=digest(state),
        representation_id=representation,parent_sha256=parent_sha256,
        encoding="unit-demand-coverage-reward.v1",
        scope="Complete declared unit-demand program domain" if parent_sha256 is None else "Lossy declared option restriction",
        instance=instance,snapshot=state,options=programs,variable_order=["option:"+p for p in ids],registers=[],
        constant=str(constant),linear=list(map(str,linear)),
        quadratic=[dict(i=i,j=j,value=str(penalty)) for i,j in edges],
        objective=dict(constant=str(constant),linear=list(map(str,linear)),weights=weights,
                       component_bounds=bounds,lower_bound=str(lower),upper_bound=str(upper)),
        penalty=str(penalty),penalty_proof="P exceeds the full bit-domain objective range, including duplicate-service rewards",
        conflicts=edges,size=dict(binary_variables=n,option_bits=n,shortfall_bits=0,capacity_bits=0,auxiliary_bits=0,couplers=len(edges)),
        coefficients=dict(max_abs=max([abs(constant),penalty]+[abs(c) for c in linear])),
        disabled_features=["phase_aware_WIP","interrupted_cooking","ingredients","holding","power","money"],
        reference_adapters=dict(exact_qubo=True,raw_slots=True,legacy_program_master=False),
        reference_note="Legacy program master adds explicit missed-variable cost; use raw slots or literal exact audit for this representation")
    bundle["bundle_sha256"] = digest(bundle)
    return validate_bundle(bundle)


def neighbor_masks(bundle):
    validate_bundle(bundle)
    if bundle.get("encoding") != "unit-demand-coverage-reward.v1":
        raise ValueError("Mixer requires the audited unit-demand conflict representation")
    n = bundle["size"]["binary_variables"]
    neighbors = [0]*n
    for i,j in bundle["conflicts"]:
        neighbors[i] |= 1 << j
        neighbors[j] |= 1 << i
    return neighbors


def compatibility_pool(instance, programs, cap):
    """Nested teacher-free restriction that retains compatible batch choices.

    Prefer candidates compatible with many already retained programs. This is
    preprocessing of individual alternatives, not a complete-plan optimizer.
    Its lost objective value must still be measured against the broader model.
    """
    if type(cap) is not int or cap<0:
        raise ValueError("Nonnegative integer cap required")
    ordered = sorted(programs,key=lambda p:(-len(p["allocation_order"]),p["cook_start"],p["pack_start"],p["id"]))
    occupied = {p["id"]:claims(instance,p) for p in programs}
    selected = []
    scores = {p["id"]:0 for p in programs}
    while ordered and len(selected)<cap:
        best = min(range(len(ordered)),key=lambda j:(-scores[ordered[j]["id"]],j))
        p = ordered.pop(best)
        selected.append(p)
        coverage = set(p["allocation_order"])
        for other in ordered:
            if not coverage.intersection(other["allocation_order"]) and not conflict(occupied[p["id"]],occupied[other["id"]]):
                scores[other["id"]] += 1
    return sorted(selected,key=lambda p:p["id"])


def apply_conflict_mixer(statevector, neighbors, beta):
    """Exact logical U=product_i controlled-on-neighbors-zero RX_i(2 beta).

    Little-endian data indices. This is a simulator/audit primitive, not a
    routed hardware circuit or a training algorithm. Start in a valid state.
    """
    import numpy as np
    n = len(neighbors)
    if n>22 or len(statevector) != 1<<n or not math.isfinite(float(beta)):
        raise ValueError("Finite beta and a <=22-qubit statevector required")
    if any(type(m) is not int or m<0 or m >= 1<<n or (m & (1<<i)) for i,m in enumerate(neighbors)):
        raise ValueError("Invalid neighbor mask")
    if any(bool(neighbors[i] & (1<<j)) != bool(neighbors[j] & (1<<i)) for i in range(n) for j in range(n)):
        raise ValueError("Undirected conflict graph required")
    output = np.array(statevector,dtype=np.complex128,copy=True)
    indices = np.arange(1<<n,dtype=np.uint64)
    c,s = math.cos(beta),-1j*math.sin(beta)
    for i,mask in enumerate(neighbors):
        zero = indices[((indices & (1<<i)) == 0) & ((indices & mask) == 0)].astype(np.intp)
        one = zero | (1<<i)
        a,b = output[zero].copy(),output[one].copy()
        output[zero] = c*a+s*b
        output[one] = s*a+c*b
    return output
