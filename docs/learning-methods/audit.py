"""Recompute the guide's numerical claims. No network or nonstandard packages.

Run from anywhere: python3 /path/to/docs/learning-methods/audit.py
The repository builder is a cross-check, not the independent feasibility oracle.
"""
from pathlib import Path
import cmath
import collections
import itertools
import json
import math
import random
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from solver.stage1 import build_qubo, energy, exact_reference

checks = []


def record(name, **evidence):
    checks.append(dict(name=name, status="passed", **evidence))


def assignments(n):
    return itertools.product((0, 1), repeat=n)


def independent_operations(instance):
    return [dict(job=j["id"], order=k, machine=o["machine"], duration=o["duration"])
            for j in instance["jobs"] for k, o in enumerate(j["operations"])]


def independent_valid(instance, chosen, horizon):
    """Direct scheduling predicates; no QUBO coefficients or source validator."""
    expected = independent_operations(instance)
    selected = collections.defaultdict(list)
    for v in chosen:
        selected[(v["job"], v["order"])].append(v)
    if set(selected) != {(o["job"], o["order"]) for o in expected}:
        return False
    if any(len(vs) != 1 for vs in selected.values()):
        return False
    starts = {k: vs[0]["start"] for k, vs in selected.items()}
    for o in expected:
        s = starts[o["job"], o["order"]]
        if s < 0 or s + o["duration"] > horizon:
            return False
        if o["order"]:
            prev = next(v for v in expected if v["job"] == o["job"] and v["order"] == o["order"] - 1)
            if starts[prev["job"], prev["order"]] + prev["duration"] > s:
                return False
    for a, b in itertools.combinations(expected, 2):
        sa, sb = starts[a["job"], a["order"]], starts[b["job"], b["order"]]
        if a["machine"] == b["machine"] and sa < sb + b["duration"] and sb < sa + a["duration"]:
            return False
    return True


def independent_candidates(instance, horizon):
    result = []
    for j in instance["jobs"]:
        ps = [o["duration"] for o in j["operations"]]
        for k, o in enumerate(j["operations"]):
            for t in range(sum(ps[:k]), horizon - sum(ps[k:]) + 1):
                result.append(dict(job=j["id"], order=k, machine=o["machine"], start=t, duration=o["duration"]))
    return result


A = json.loads((ROOT / "instances/instance_2x2.json").read_text())
B = json.loads((ROOT / "instances/instance_3x3.json").read_text())

# Every assignment, including invalid codes, is checked on these models.
crosschecks = []
custom = {"problem": "erp_scheduling", "jobs": [
    {"id": "J1", "operations": [{"machine": "T", "duration": 1}, {"machine": "F", "duration": 1}]},
    {"id": "J2", "operations": [{"machine": "T", "duration": 2}, {"machine": "F", "duration": 1}]}]}
for name, instance, h in [("A", A, h) for h in (2, 3, 4, 5)] + [("unequal-chain", custom, h) for h in (2, 3, 4)]:
    candidates = independent_candidates(instance, h)
    for enc in ("onehot", "domain-wall"):
        model = build_qubo(instance, h, enc)
        if enc == "onehot":
            assert model["variables"] == candidates
        else:
            assert model["start_variables"] == candidates
        n = len(model["variables"])
        feasible_count = 0
        minimum = math.inf
        for bits in assignments(n):
            e = energy(model, bits)
            minimum = min(minimum, e)
            if enc == "onehot":
                indicators = bits
                valid_code = True  # Direct checker handles one-hot cardinality.
            else:
                indicators = [ex["constant"] + sum(q * bits[i] for i, q in ex["terms"])
                              for ex in model["indicators"]]
                valid_code = all(x in (0, 1) for x in indicators)
            chosen = [v for v, x in zip(candidates, indicators) if x == 1]
            feasible = valid_code and independent_valid(instance, chosen, h)
            assert e >= 0, (name, h, enc, bits, e)
            assert (e == 0) == feasible, (name, h, enc, bits, e, feasible)
            feasible_count += feasible
        crosschecks.append(dict(instance=name, horizon=h, encoding=enc, bits=n,
                                assignments=2**n, zero_states=feasible_count, minimum=minimum))
record("zero-energy iff independently feasible, including empty/singleton domains", models=crosschecks,
       total_assignments=sum(m["assignments"] for m in crosschecks))

# Match the printed 8x8 matrix and the displayed domain-wall polynomial.
expected_pairs = {(0, 1): 2, (2, 3): 2, (4, 5): 2, (6, 7): 2,
                  (0, 4): 1, (0, 5): 1, (1, 5): 1, (2, 6): 1,
                  (2, 7): 1, (3, 7): 1, (1, 2): 1, (5, 6): 1}
onehot = build_qubo(A, 4)
assert onehot["linear"] == [-1] * 8 and onehot["offset"] == 4
assert {(i, j): q for i, j, q in onehot["quadratic"]} == expected_pairs
for bits in assignments(8):
    printed = 4 - sum(bits) + sum(q * bits[i] * bits[j] for (i, j), q in expected_pairs.items())
    assert printed == energy(onehot, bits)
dw = build_qubo(A, 4, "domain-wall")
for y1, y2, y3, y4 in assignments(4):
    printed = 2 - y2 + y3 - y1*y2 + y1*y3 + y2*y4 - y3*y4
    assert printed == energy(dw, (y1, y2, y3, y4))
assert energy(onehot, [0,1,0,1,1,0,1,0]) == 0
assert energy(onehot, [1,0,1,0,1,0,1,0]) == 2
assert energy(onehot, [1]*8) == 12
record("printed scheduling matrices and example energies", onehot_assignments=256, domain_wall_assignments=16)

assert exact_reference(A)["makespan"] == 4
assert exact_reference(B)["makespan"] == 8
for inst, h, nh, nd in [(A, 4, 8, 4), (B, 8, 39, 30)]:
    assert len(build_qubo(inst, h)["variables"]) == nh
    assert len(build_qubo(inst, h, "domain-wall")["variables"]) == nd
assert sum(math.ceil(math.log2(8 - sum(o["duration"] for o in j["operations"]) + 1))
           for j in B["jobs"] for _ in j["operations"]) == 21
bs = [("Z2", "T", 0, 1), ("Z2", "F", 1, 3), ("Z2", "S", 3, 4),
      ("Z1", "T", 1, 3), ("Z1", "F", 3, 4), ("Z1", "S", 4, 6),
      ("Z3", "T", 3, 5), ("Z3", "F", 5, 7), ("Z3", "S", 7, 8)]
chosen_b = [dict(job=j, machine=m, start=s, order=("T","F","S").index(m), duration=e-s) for j,m,s,e in bs]
assert independent_valid(B, chosen_b, 8)
record("source instance optima, counts and Example B intervals", optima=[4, 8], B_bits=dict(onehot=39, domain_wall=30, binary_before_auxiliaries=21))

# Generic Ising conversion on randomized signed QUBOs and every bit assignment.
rng = random.Random(20261017)
ising_assignments = 0
for n in range(1, 7):
    for _ in range(10):
        a = [rng.randint(-7, 7) for _ in range(n)]
        w = {(i,j): rng.randint(-7,7) for i in range(n) for j in range(i+1,n)}
        c0 = rng.randint(-7,7)
        ci = c0 + sum(a)/2 + sum(w.values())/4
        h = [-a[i]/2 - sum(q for (j,k),q in w.items() if i in (j,k))/4 for i in range(n)]
        for x in assignments(n):
            z = [1-2*xx for xx in x]
            original = c0 + sum(ai*xx for ai,xx in zip(a,x)) + sum(q*x[i]*x[j] for (i,j),q in w.items())
            spin = ci + sum(hi*zz for hi,zz in zip(h,z)) + sum(q*z[i]*z[j]/4 for (i,j),q in w.items())
            assert original == spin
            ising_assignments += 1
for x in assignments(2):
    z1,z2 = (1-2*b for b in x)
    assert 1+3*x[0]-2*x[1]+4*x[0]*x[1] == 2.5-2.5*z1+z1*z2
    assert 2-x[0]+3*x[1]-2*x[0]*x[1] == 2.5+z1-z2-.5*z1*z2
record("generic and printed QUBO-to-Ising conversions", assignments=ising_assignments+8)

# Domain-wall guarantees on arbitrary nonnegative cross-operation conflict graphs.
wall_assignments = 0
for sizes in [(1,3), (3,4), (4,4), (2,3,4)]:
    labels = [(o,r) for o,k in enumerate(sizes) for r in range(k)]
    edges = [(a,b,rng.randint(1,5)) for a,b in itertools.combinations(labels,2)
             if a[0] != b[0] and rng.random() < .5]
    degree = collections.Counter()
    for a,b,w in edges:
        degree[a] += w
        degree[b] += w
    dmax = max(degree.values(), default=0)
    eta = dmax + 1
    for bits in assignments(sum(k-1 for k in sizes)):
        indicators, up, pos = {}, 0, 0
        for o,k in enumerate(sizes):
            ys = (1,) + bits[pos:pos+k-1] + (0,)
            pos += k-1
            up += sum((1-ys[s])*ys[s+1] for s in range(1,k-1))
            for r in range(k):
                indicators[o,r] = ys[r]-ys[r+1]
        conflicts = sum(w*indicators[a]*indicators[b] for a,b,w in edges)
        e = conflicts+eta*up
        assert e >= (eta-dmax)*up
        if up:
            assert e > 0
        wall_assignments += 1
record("domain-wall strict incident-degree bound on arbitrary weighted conflicts", assignments=wall_assignments)

# Verify quadratization for positive and negative cubic coefficients.
for c in [-9,-2,0,3,11]:
    m = abs(c)+1
    for u,v,w in assignments(3):
        values = [(c*q*w + m*(u*v-2*u*q-2*v*q+3*q),q) for q in (0,1)]
        best = min(values)
        assert best[0] == c*u*v*w and best[1] == u*v
for u,v,q in assignments(3):
    linear_valid = q>=0 and q<=u and q<=v and q>=u+v-1
    assert linear_valid == (q == u*v)
record("product quadratization and constrained linearisation", cubic_coefficients=[-9,-2,0,3,11])

# General squared linear equality and the explicitly printed slack example.
equality_assignments = 0
for n in range(1,6):
    for _ in range(10):
        d = [rng.randint(-5,5) for _ in range(n)]
        b = rng.randint(-5,5)
        for x in assignments(n):
            expanded = b*b + sum((di*di-2*b*di)*xx for di,xx in zip(d,x))
            expanded += sum(2*d[i]*d[j]*x[i]*x[j] for i in range(n) for j in range(i+1,n))
            assert expanded == (sum(di*xx for di,xx in zip(d,x))-b)**2
            equality_assignments += 1
for x1,x2 in assignments(2):
    candidates = []
    for s0,s1 in assignments(2):
        x = (x1,x2,s0,s1)
        expanded = 9+sum(a*b for a,b in zip((-8,-9,-5,-8),x))
        expanded += sum(q*x[i]*x[j] for (i,j),q in zip(itertools.combinations(range(4),2),(12,4,8,6,12,4)))
        original = (2*x1+3*x2+s0+2*s1-3)**2
        assert expanded == original
        candidates.append(original)
    assert (min(candidates)==0) == (2*x1+3*x2<=3)
record("general equality expansion and four-bit slack example", assignments=equality_assignments+16)

# The complete one-qubit circuit, using complex amplitudes.
phase_checks = 0
for gamma in [-math.pi, -math.pi/2, -.73, 0, .42, math.pi/2, math.pi]:
    for beta in [-math.pi/2, -math.pi/4, -.2, 0, .64, math.pi/4, math.pi/2]:
        before = [1/math.sqrt(2), cmath.exp(-1j*gamma)/math.sqrt(2)]
        amplitude = math.cos(beta)*before[0] - 1j*math.sin(beta)*before[1]
        probability = abs(amplitude)**2
        formula = (1-math.sin(2*beta)*math.sin(gamma))/2
        assert abs(probability-formula) < 1e-12
        phase_checks += 1
record("one-qubit phase-to-probability identity", angle_pairs=phase_checks)

# Residual coefficients and annealing deltas are compared to full energies.
for n in range(2,7):
    a = [rng.randint(-4,4) for _ in range(n)]
    w = {(i,j):rng.randint(-4,4) for i in range(n) for j in range(i+1,n)}
    def e(x):
        return 3+sum(ai*xx for ai,xx in zip(a,x))+sum(q*x[i]*x[j] for (i,j),q in w.items())
    for x in assignments(n):
        for i in range(n):
            flipped = list(x)
            flipped[i] = 1-flipped[i]
            delta = (1-2*x[i])*(a[i]+sum(q*x[j if i==k else k] for (k,j),q in w.items() if i in (k,j)))
            assert delta == e(flipped)-e(x)
        if x[-1] == 1:
            residual = 3+a[-1]+sum((a[i]+w[i,n-1])*x[i] for i in range(n-1))
            residual += sum(q*x[i]*x[j] for (i,j),q in w.items() if j < n-1)
            assert residual == e(x)
record("annealing one-bit delta and fixed-variable substitution", randomized_sizes=list(range(2,7)))

report = dict(status="passed", seed=20261017, scope="finite example and implementation checks; general guarantees are proved in guide.md", checks=checks)
(HERE / "audit-report.json").write_text(json.dumps(report, indent=2)+"\n")
print(json.dumps(dict(status=report["status"], check_groups=len(checks), checks=[c["name"] for c in checks]), indent=2))
