# Pair-order probe: four qubits for the complete tiny deadline decision

**The official three-job, three-machine instance has a four-bit, exact deadline-feasibility QUBO after certified structural presolve.** It retains all five schedules meeting `H=8`, including the non-permutation schedule. This is an instance-specific reduction with disclosed classical work, not a quantum speedup or a generic four-bit factory solver. Official Stage 1 artifacts remain unchanged.

Code: `stage2/rank_probe.py`. Primary standard-library-only reproduction:

```sh
python3 -m stage2.rank_probe --sat-only --output /path/to/new-empty-directory
```

Archived result: `output/stage2-search/rank-probe/sat-only-final/`. Optional coefficient sparsification: `output/stage2-search/rank-probe/structural-final/` (requires NumPy/SciPy). Both contain the numerical instance, full proof report, standalone four-bit model and its lifted nine-bit model.

## What the four bits mean

For each machine T/F/S, three initial bits encode whether Z1 precedes Z2, Z1 precedes Z3, and Z2 precedes Z3. Bit indices are T:0–2, F:3–5, S:6–8. Each machine has six transitive orders and two cyclic tournaments. All `6³=216` transitive combinations are acyclic because job precedence only moves forward through the common machine route.

At deadline eight, structural constraints imply:

- `a = x0 = x3`: Z1 versus Z2 on T and F.
- `b = x1 = x4 = x7`: Z1 versus Z3 on T, F and S.
- `c = x2 = x5 = x8`: Z2 versus Z3 on T, F and S.
- `d = x6`: Z1 versus Z2 on S.

No individual bit is constant. The equalities are proved from physical critical-path constraints with SAT contradiction proofs; no one optimal schedule is selected or hardcoded. The reduced variables remain interpretable machine-order decisions.

The SAT-only integer QUBO is:

`E(a,b,c,d) = 2 + 3b − 2c − d − ab + 2ac − ad − 3bc − bd + 2cd`.

It has six couplers, maximum coefficient magnitude three, and no auxiliary bits. All sixteen assignments were checked exactly. Energy is zero precisely for these reduced bit vectors (written a,b,c,d; a is the least-significant bit):

| Reduced bits | Original nine-bit integer state | Earliest makespan |
|---|---:|---:|
| 1,0,0,1 | 73 | 8 |
| 0,0,1,0 | 292 | 8 |
| 0,1,1,0 | 438 | 8 |
| 0,1,1,1 | 502 | 8 |
| 1,1,1,1 | 511 | 8 |

State 502 uses a different order on S than on T/F; it demonstrates that the reduction did not silently restrict the problem to permutation flow-shop schedules.

Every other reduced assignment has energy at least one. A full nine-bit equivalent is obtained by evaluating the reduced polynomial on representative bits and adding `(xi−xj)²` for each required equality. Since the reduced polynomial is nonnegative everywhere, unit equality penalties suffice. Every one of the 512 original bitstrings was independently checked: zero energy iff it decodes to a valid schedule completing by eight. All five deadline-feasible states are retained.

## Construction without complete-schedule labels

The primary compiler does **not** first score all 216 schedules and fit the answer. It proceeds from primitive physical constraints:

1. Keep job-precedence arcs and add only the machine-order arcs selected by a partial bit assignment.
2. Compute that partial DAG's longest path. If its duration exceeds H, every completion of the assignment is impossible. Save the actual critical path as a witness.
3. Compile a forbidden unary/pair assignment as a nonnegative literal penalty. Three-bit cuts are clauses; they are not silently treated as quadratic.
4. Add each machine's transitivity constraints. For local bits u,v,w, the quadratic triangle penalty `v−uv−vw+uw` is one on the two cycles and zero on the six valid orders.
5. Use SAT implication queries on these structural clauses to prove bit equalities and additional forbidden unary/pair assignments. Every unit propagation and branch contradiction has a replayed proof.
6. Substitute the proved equalities. Sum distinct nonnegative proved unary/pair penalties and triangle penalties. For this instance the resulting six functions are already quadratic and exact. No LP is needed for the primary model.

The six functions being summed are:

```text
b(1−c)
(1−a)(1−c)
(1−c)(1−d)
a(1−d)
b−ab−bc+ac        [triangle on T/F]
b−bd−bc+cd        [triangle on S]
```

Their sum is the displayed four-bit QUBO. Each is nonnegative on binary inputs. Original physical cuts or replayed SAT contradiction proofs justify each penalty.

**Actual construction work:** 770 partial-DAG longest-path evaluations, 78 physical nogoods, 90 SAT queries, and 172 total DPLL search nodes. The 90 queries comprise 18 constant tests and 72 cases testing unequal pairs. All 25 UNSAT answers have independently replayed proofs; the other 65 answers retain satisfying assignments. The structural formula has 84 clauses: 78 physical nogoods and six transitivity clauses. All 78 critical-path witnesses were checked against the actual operation durations and allowed precedence arcs.

The reported local SAT-only run took approximately **0.032 seconds including exhaustive verification**. This is a tiny-instance measurement, not a scaling claim.

Complete-order scheduling is used **after model construction for validation**, not to choose its coefficients. Classical SAT presolve is still real computational work; it can itself find satisfying assignments. The experiment does not show that quantum sampling was needed to find the answer.

## Negative result: physical pair cuts alone are insufficient

All 18 unary and 144 pair partial assignments were tested. They produce no unary deadline cuts and five pair cuts. With transitivity, that quadratic relaxation leaves 90 zero states: the five feasible states and **85 infeasible states**.

Allowing minimal triple assignments produces 73 additional physical critical-path nogoods. These cover every bad state, but directly summing their literal penalties has degree three. The implementation preserves this negative result; it does not call those cubic terms a QUBO. Structural SAT closure is what exposes enough additional quadratic consequences to obtain the small exact model.

The 770 evaluated partial DAGs include the 162 unary/pair cases and 608 triple cases; 64 triple assignments are skipped because a previously witnessed pair nogood already excludes them.

## Optional smaller-coefficient model

An optional nonnegative cut-weight LP uses twelve distinct reduced structural cut functions. It selects five functions, all with exact integer weight one, so all cubic coefficients cancel. The resulting model is:

`E_sparse = 1 + 2b − c + ac − ad − 2bc − bd + cd`.

It has five couplers and coefficient magnitude at most two. Its sixteen assignments and all 512 states of the lifted model were checked exactly. It retains the same five schedules.

This LP uses only structural-cut values and their polynomial coefficients, **not makespan labels**. It is optional coefficient optimization: the SAT-only model already works. Its cost is separate from the primary standard-library compiler.

Reproduce with:

```sh
.venv/bin/python -m stage2.rank_probe --structural-only --output /path/to/new-empty-directory
```

## Separate supervised expressiveness experiment

The original probe deliberately scored every one of the 216 complete order combinations and classified all 512 bitstrings. A 46-coefficient quadratic LP, with 46 absolute-value auxiliaries for coefficient minimization, found an exact nine-bit H=8 classifier. Rationalization produced integer coefficients of magnitude at most two, thirteen couplers, zero energy on all five feasible states and minimum bad energy one.

That construction **does use complete-schedule supervision** and must not be advertised as free or scalable preprocessing. It remains a useful independent expressiveness comparison, preserved in `rank-probe/certified-v2/report.json`. The later structural method avoids these labels during construction.

## Exact makespan is not a nine-bit quadratic

An exact rational linear-algebra test shows that the full makespan function cannot be represented as a quadratic of these same nine pair-order bits on all 216 valid orders. The feature matrix has rank 43. A particularly short contradiction uses eight valid states:

| State | Weight | Makespan |
|---:|---:|---:|
| 6 | −1 | 12 |
| 7 | +1 | 12 |
| 14 | +1 | 13 |
| 15 | −1 | 13 |
| 64 | +1 | 10 |
| 65 | −1 | 11 |
| 72 | −1 | 9 |
| 73 | +1 | 8 |

For the constant, every linear feature and every quadratic feature, the weighted sum is exactly zero. The weighted makespan sum is **−2**. Thus no choice of quadratic coefficients can equal makespan on all these states. Deadline feasibility and exact makespan are different modeling claims.

## Conditional three-bit rank objectives

When the other two machines' orders are frozen, six permutations remain for the selected machine. Their six resulting makespans can be interpolated exactly by a three-bit quadratic. Adding a sufficiently large triangle penalty lifts the two cyclic states above every valid permutation.

All **108 contexts** were tested: three choices of varied machine times 36 fixed-order combinations. Exact rational coefficients reproduced every valid objective and excluded every cycle across 864 local states. This supports a small conditional neighborhood formulation, while explicitly freezing the surrounding schedule. It does not establish global optimality for a large factory or eliminate the need to account for boundary resources.

## Scope

At the same H=8, the existing baseline builder uses 39 one-hot bits or 30 domain-wall bits. The pair-order domain initially needs nine bits; certified, deadline-specific structural relations reduce this instance to four. These comparisons concern the same deadline decision, not identical timing parameterizations.

The method is not guaranteed to reduce a different instance to four bits, or even to obtain an exact quadratic after SAT closure. The code's exact verification gate prevents reporting such a claim when the construction fails. SAT and partial-DAG preprocessing can become expensive on larger problems. Fitting the qubit count also leaves device connectivity, routed circuit depth and noise to be checked separately.

No official schedule, Stage 1 selected artifact, QPU job, deployment or paid solver was changed or launched by this probe.
