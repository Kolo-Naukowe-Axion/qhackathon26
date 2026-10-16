"""Time-indexed QUBO preparation using only Python's standard library.

Run: python3 -m solver.stage1 --output output/stage1-preparation
This builds models and exact classical references, never a VeloxQ job.
"""

import argparse
import itertools
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def operations(instance):
    """Validate the supported baseline domain and flatten job chains."""
    if instance.get("problem") != "erp_scheduling" or not instance.get("jobs"):
        raise ValueError("Expected a nonempty erp_scheduling instance")
    result, ids, route = [], set(), None
    for job in instance["jobs"]:
        if not isinstance(job["id"], str) or not job["id"] or job["id"] in ids:
            raise ValueError("Job ids must be unique strings")
        ids.add(job["id"])
        machines = [op["machine"] for op in job["operations"]]
        if any(not isinstance(m, str) or not m for m in machines):
            raise ValueError("Machine ids must be nonempty strings")
        if not machines or len(set(machines)) != len(machines):
            raise ValueError("Each job must visit each route machine once")
        if route is not None and machines != route:
            raise ValueError("This implementation supports a common baseline route")
        route = machines
        for order, op in enumerate(job["operations"]):
            if type(op["duration"]) is not int or op["duration"] <= 0:
                raise ValueError("Durations must be positive integer hours")
            result.append(dict(job=job["id"], machine=op["machine"],
                               duration=op["duration"], order=order))
    return result


def build_qubo(instance, horizon, encoding="onehot"):
    """E = sum_o (sum_t x_ot - 1)^2 + sum_conflicts x_a*x_b.

    All penalty weights are one. At a fixed horizon E >= 0 and E = 0 iff
    the decoded schedule is feasible. Makespan optimization is an outer search,
    not an extra term that could trade feasibility for objective improvement.
    """
    if type(horizon) is not int or horizon < 1:
        raise ValueError("Horizon must be a positive integer")
    ops = operations(instance)
    variables, groups = [], []
    for op in ops:
        chain = [other for other in ops if other["job"] == op["job"]]
        earliest = sum(p["duration"] for p in chain if p["order"] < op["order"])
        tail = sum(p["duration"] for p in chain if p["order"] >= op["order"])
        group = []
        for start in range(earliest, horizon - tail + 1):
            group.append(len(variables))
            variables.append(dict(job=op["job"], machine=op["machine"],
                                  start=start, duration=op["duration"], order=op["order"]))
        groups.append(group)
    quadratic = {}

    def add(i, j, value):
        pair = (min(i, j), max(i, j))
        quadratic[pair] = quadratic.get(pair, 0) + value

    for group in groups:
        for i, j in itertools.combinations(group, 2):
            add(i, j, 2)
    for i, a in enumerate(variables):
        for j in range(i + 1, len(variables)):
            b = variables[j]
            if a["job"] == b["job"] and a["order"] == b["order"]:
                continue  # Already handled by exactly-one, not capacity.
            if a["machine"] == b["machine"] and (
                a["start"] < b["start"] + b["duration"] and
                b["start"] < a["start"] + a["duration"]
            ):
                add(i, j, 1)
            if a["job"] == b["job"]:
                first, second = sorted((a, b), key=lambda v: v["order"])
                if second["order"] == first["order"] + 1 and (
                    first["start"] + first["duration"] > second["start"]
                ):
                    add(i, j, 1)
    model = dict(schema="stage1-qubo.v1", encoding="onehot", horizon=horizon, variables=variables,
                linear=[-1] * len(variables), offset=len(ops),
                quadratic=[[i, j, q] for (i, j), q in sorted(quadratic.items())],
                provenance="offline formulation; no VeloxQ execution")
    if encoding == "onehot":
        return model
    if encoding == "domain-wall":
        return domain_wall(model)
    raise ValueError(f"Unsupported encoding: {encoding}")


def domain_wall(onehot):
    """Replace d one-hot bits by d-1 monotone bits, preserving every schedule.

    x_0=1-y_0, x_t=y_(t-1)-y_t, x_(d-1)=y_(d-2). Monotone
    y gives exactly one start. A 0->1 wall gives one negative indicator.
    A wall penalty greater than the largest incident conflict weight bounds
    ALL possible negative conflict energy, so invalid walls cannot reach zero.
    """
    groups = {}
    for i, v in enumerate(onehot["variables"]):
        groups.setdefault((v["job"], v["machine"]), []).append(i)
    variables, indicators, walls = [], [None] * len(onehot["variables"]), []
    for (job, machine), group in groups.items():
        ys = []
        for k in range(len(group) - 1):
            ys.append(len(variables))
            variables.append(dict(job=job, machine=machine, after_start=onehot["variables"][group[k]]["start"]))
        walls.extend(zip(ys, ys[1:]))
        for k, old in enumerate(group):
            terms = []
            if k:
                terms.append([ys[k - 1], 1])
            if k < len(ys):
                terms.append([ys[k], -1])
            indicators[old] = dict(constant=int(k == 0), terms=terms)
    # Determine conflict degree; exactly-one couplings are not conflicts.
    degree = [0] * len(indicators)
    for i, j, q in onehot["quadratic"]:
        a, b = onehot["variables"][i], onehot["variables"][j]
        if (a["job"], a["machine"]) != (b["job"], b["machine"]):
            degree[i] += q
            degree[j] += q
    penalty = max(degree, default=0) + 1
    linear, quadratic, offset = [0] * len(variables), {}, onehot["offset"]

    def add_pair(i, j, value):
        if i == j:
            linear[i] += value  # Binary idempotence.
        else:
            pair = tuple(sorted((i, j)))
            quadratic[pair] = quadratic.get(pair, 0) + value

    for old, q in enumerate(onehot["linear"]):
        expr = indicators[old]
        offset += q * expr["constant"]
        for i, a in expr["terms"]:
            linear[i] += q * a
    for old_i, old_j, q in onehot["quadratic"]:
        a, b = indicators[old_i], indicators[old_j]
        offset += q * a["constant"] * b["constant"]
        for i, ai in a["terms"]:
            linear[i] += q * ai * b["constant"]
        for j, bj in b["terms"]:
            linear[j] += q * bj * a["constant"]
        for i, ai in a["terms"]:
            for j, bj in b["terms"]:
                add_pair(i, j, q * ai * bj)
    for previous, following in walls:
        linear[following] += penalty
        add_pair(previous, following, -penalty)
    return dict(schema="stage1-qubo.v1", encoding="domain-wall", horizon=onehot["horizon"],
                variables=variables, start_variables=onehot["variables"], indicators=indicators,
                wall_penalty=penalty, monotone_pairs=[list(pair) for pair in walls],
                linear=linear, quadratic=[[i, j, q] for (i, j), q in sorted(quadratic.items()) if q],
                offset=offset, provenance=onehot["provenance"])


def checked_bits(model, sample):
    bits = list(sample)
    if len(bits) != len(model["variables"]) or any(b not in (0, 1) for b in bits):
        raise ValueError("Sample must contain one binary value per variable")
    return bits


def energy(model, sample):
    bits = checked_bits(model, sample)
    return (model["offset"] + sum(q * x for q, x in zip(model["linear"], bits))
            + sum(q * bits[i] * bits[j] for i, j, q in model["quadratic"]))


def decode(model, sample):
    bits = checked_bits(model, sample)
    variables = model["variables"]
    if model.get("encoding") == "domain-wall":
        bits = [expr["constant"] + sum(q * bits[i] for i, q in expr["terms"])
                for expr in model["indicators"]]
        if any(x not in (0, 1) for x in bits):
            raise ValueError("Nonmonotone domain-wall sample")
        variables = model["start_variables"]
    return [dict(job=v["job"], machine=v["machine"], start=v["start"],
                 end=v["start"] + v["duration"])
            for v, bit in zip(variables, bits) if bit]


def encode_schedule(model, schedule):
    """Encode a feasible schedule for round-trip tests or explicit warm starts."""
    selected = {(s["job"], s["machine"]): s["start"] for s in schedule}
    if model.get("encoding") == "domain-wall":
        return [int(selected[(v["job"], v["machine"])] > v["after_start"]) for v in model["variables"]]
    return [int(selected.get((v["job"], v["machine"])) == v["start"]) for v in model["variables"]]


def validate(instance, schedule, makespan):
    """Check intervals directly, independently of QUBO coefficients/windows."""
    ops = operations(instance)
    if not isinstance(schedule, list) or any(not isinstance(s, dict) or not {"job", "machine", "start", "end"} <= s.keys() for s in schedule):
        return ["malformed schedule"]
    expected = {(op["job"], op["machine"]): op for op in ops}
    found, errors = {}, []
    for item in schedule:
        if not isinstance(item["job"], str) or not isinstance(item["machine"], str):
            errors.append("unknown or duplicate operation")
            continue
        key = (item["job"], item["machine"])
        if key not in expected or key in found:
            errors.append("unknown or duplicate operation")
            continue
        found[key] = item
        start, end = item["start"], item["end"]
        if type(start) is not int or type(end) is not int:
            errors.append("noninteger time")
            continue
        if start < 0 or end - start != expected[key]["duration"]:
            errors.append("invalid start or duration")
    if set(found) != set(expected):
        errors.append("missing operation")
    if "noninteger time" in errors or "unknown or duplicate operation" in errors:
        return errors
    for a, b in itertools.combinations(found.values(), 2):
        if a["machine"] == b["machine"] and a["start"] < b["end"] and b["start"] < a["end"]:
            errors.append("machine overlap")
    for op in ops:
        successors = [p for p in ops if p["job"] == op["job"] and p["order"] == op["order"] + 1]
        for successor in successors:
            a = found.get((op["job"], op["machine"]))
            b = found.get((successor["job"], successor["machine"]))
            if a and b and a["end"] > b["start"]:
                errors.append("precedence violation")
    if type(makespan) is not int or makespan != max((s["end"] for s in schedule), default=0):
        errors.append("incorrect makespan")
    return errors


def exact_reference(instance):
    """Enumerate independent orders on EVERY machine, then longest paths.

    Every feasible nonpreemptive schedule induces such machine orders. For each
    acyclic order combination the earliest-start schedule minimizes makespan.
    Thus enumeration is exact, including non-permutation schedules and idle time.
    This is factorial and intentionally limited to the tiny official baselines.
    """
    ops = operations(instance)
    machines = list(dict.fromkeys(op["machine"] for op in ops))
    machine_ops = [[i for i, op in enumerate(ops) if op["machine"] == m] for m in machines]
    count = math.prod(math.factorial(len(group)) for group in machine_ops)
    if count > 100_000:
        raise ValueError("Exact enumerator limited to 100,000 machine-order combinations")
    choices = [list(itertools.permutations(group)) for group in machine_ops]
    best = None
    for orders in itertools.product(*choices):
        predecessors = {i: set() for i in range(len(ops))}
        for i, op in enumerate(ops):
            predecessors[i].update(j for j, p in enumerate(ops)
                                   if p["job"] == op["job"] and p["order"] + 1 == op["order"])
        for order in orders:
            for a, b in zip(order, order[1:]):
                predecessors[b].add(a)
        ends, schedule = {}, []
        while len(ends) < len(ops):
            ready = [i for i, preds in predecessors.items() if i not in ends and preds <= ends.keys()]
            if not ready:
                break  # Cyclic orders cannot define a feasible schedule.
            for i in ready:
                op = ops[i]
                start = max((ends[j] for j in predecessors[i]), default=0)
                ends[i] = start + op["duration"]
                schedule.append(dict(job=op["job"], machine=op["machine"], start=start, end=ends[i]))
        if len(ends) == len(ops):
            makespan = max(ends.values())
            if best is None or makespan < best["makespan"]:
                best = dict(method="Exact classical machine-order enumeration (reference only)",
                            makespan=makespan, schedule=schedule, order_combinations=count)
    if best is None:
        raise ValueError("No feasible schedule")
    return best


def to_dimod(model):
    """Optional SDK handoff: build a BINARY BQM; no client/network activity.

    The SDK accepts dimod BQMs. Keep explicit BINARY vartype: passing QUBO
    coefficients as raw biases/couplings would risk interpreting them as Ising.
    """
    import dimod
    return dimod.BinaryQuadraticModel(dict(enumerate(model["linear"])),
                                     {(i, j): q for i, j, q in model["quadratic"]},
                                     model["offset"], dimod.BINARY)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "output/stage1-preparation")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    for name in ("instance_2x2", "instance_3x3"):
        source = ROOT / "instances" / f"{name}.json"
        instance = json.loads(source.read_text())
        reference = exact_reference(instance)
        model = build_qubo(instance, reference["makespan"])
        errors = validate(instance, reference["schedule"], reference["makespan"])
        if errors:
            raise RuntimeError(errors)
        selected = {(s["job"], s["machine"], s["start"]) for s in reference["schedule"]}
        sample = [int((v["job"], v["machine"], v["start"]) in selected) for v in model["variables"]]
        if energy(model, sample) != 0 or validate(instance, decode(model, sample), reference["makespan"]):
            raise RuntimeError("Reference does not round-trip through QUBO")
        reference.update(instance=name, provenance="classical reference; no quantum or VeloxQ run",
                         qubo_roundtrip_energy=energy(model, sample))
        for suffix, content in (("qubo", model), ("reference", reference)):
            (args.output / f"{name}.{suffix}.json").write_text(json.dumps(content, indent=2) + "\n")
        print(f"{name}: {len(model['variables'])} variables; exact reference {reference['makespan']} h; round-trip energy 0")
    print("Offline preparation only. Required quantum and VeloxQ runs remain outstanding.")


if __name__ == "__main__":
    main()
