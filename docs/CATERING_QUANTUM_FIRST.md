# Catering: quantum-first method and current evidence

17 October 2026. The user clarified that the quantum method is the main project;
classical optimization provides validation and reference values. This supersedes
a classical-planner-first interpretation of the work split.

## The operational decision

Choose which legal local batch programs to execute. A program specifies menu,
yield, customer allocation, cooker, qualified workers and prep/cook/pack/clean
times. Several customers can share one batch. It is not a pre-solved complete
kitchen schedule. The selected programs directly decode into the full kitchen
plan; no classical optimizer completes or repairs a quantum answer.

The score remains lexicographic (U,W,B,R): weighted missed demand, discarded
lots, new batches and symmetric difference from the prior unstarted programs.
Hard constraints remain hard even when some demand cannot be fulfilled.

## A quantum-oriented representation

The implemented prototype, catering/quantum_first.py, uses unit residual demand
groups: each represents one lot, not necessarily one individual meal. For the
current fixtures a lot is ten meals. This representation rejects residual
quantities above one rather than silently changing their meaning.

Let x_b select a legal batch program and a_db be its 0/1 coverage of group d.
Connect two programs whenever they double-book any equipment/worker interval
or serve the same unit demand. A feasible selection is an independent set of
this conflict graph. Individual program validity and global pair compatibility
are sufficient only for the declared profile: aggregate ingredients, holding
and power are disabled. Adding those constraints requires a new proof/mixer.

On feasible selections:

    U = sum_d priority_d * (1 - sum_b a_db x_b)
    W = fixed_waste + sum_b (yield_b - served_b) x_b
    B = sum_b x_b
    R = |previous| + sum_b (1 - 2*[b in previous]) x_b

Thus the objective C=C0+sum_b c_b x_b is linear, with no missed-demand register.
The equivalent unconstrained QUBO is:

    E(x) = C(x) + P sum_{(b,c) in conflicts} x_b x_c.

Coverage rewards can make C negative on invalid selections. The old penalty
bound for a nonnegative objective is insufficient here. The implementation uses
P=1+sum_b |c_b|, exceeding the entire bit-domain objective range. If any conflict
is selected, E is greater than the maximum possible C; all-zero is a feasible
witness. Every global minimizer is therefore feasible and optimizes C in the
declared option domain. Every zero-penalty selection is checked independently
against raw operations, meal allocations and material disposal.

The loader, literal energy, Ising conversion, decoder and generic sampling
contract remain usable. The old catering.native.solve_program_master explicitly
rejects this representation: it separately adds missed-variable costs, which
would double-count them. Use literal exact enumeration/independent selection
audits or catering.native_slots for the complete raw reference.

## Algorithm: alternate cost phases and feasible mixing

For program b, rotate its data qubit only when every conflicting neighbor is
zero. A sequential layer of these neighbor-controlled RX(2 beta) gates preserves
independent-set support. Start from all-zero, which retains committed work and
mandatory recovery cleaning while explicitly missing the remaining meal demand.
Any independent set can be reached through valid single-bit additions/removals;
this connectivity statement does not guarantee useful amplitudes at shallow depth.

On this invariant feasible subspace, penalty phases are identities. The cost
phase can therefore use only the linear service/waste/batch/change terms.
Ordinary X-mixer QAOA instead uses the full penalized QUBO. Compare both methods
on identical offered programs and physical objectives, recording their different
gate costs and state preparations explicitly.

Controlled independent-set/set-packing mixers are established methods, not our
invention: see Hadfield et al., Sections 4.2 and A.2.4,
[Quantum Alternating Operator Ansatz](https://arxiv.org/abs/1709.03489).
Our proposed contribution is the catering mapping, its precise correctness and
scope, and the measured feasibility/quality/resource tradeoff.

The central experiment is whether constraint-preserving mixing gives better
checked schedules per shot and per routed gate budget than ordinary QAOA.
VQE and VeloxQ consume the same literal QUBO for their comparisons; they need
not use the QAOA mixer. Classical solving supplies optima/bounds and sanity checks.

## What has actually been tested

Run:

    .venv-stage2/bin/python -m unittest discover -s tests/catering -v
    .venv-stage2/bin/python -m catering.build_quantum_first --output output/NEW-DIRECTORY

The retained prototype is output/catering-quantum-first-v2/. Its raw fixture has
two residual menus, four ten-meal demand groups, variable batch yields,
freshness/departures, shared crews and committed Menu A work. Its complete
program encoding has 359 data bits and 55,426 couplers. Caps 8/12/16/20 are
explicit restrictions with distinct hashes.

Tests verify the literal QUBO against independent raw enumeration, the full
objective-range penalty bound, mixer unitarity, feasible-support preservation
and exact Ising energies. Fixed-angle, two-layer full-statevector probes are
logical circuit audits, not trained QAOA performance measurements.

| Cap/data qubits | Feasible basis states | Exact restricted U,W,B,R | Full raw optimum |
|---:|---:|---|---|
| 8 | 25 | 1,0,2,2 | 0,0,2,2 |
| 12 | 49 | 1,0,2,2 | 0,0,2,2 |
| 16 | 96 | 1,0,2,2 | 0,0,2,2 |
| 20 | 189 | 1,0,2,2 | 0,0,2,2 |

**These capped pools fail the main-workload gate:** they lose one demand lot
relative to the complete model. Do not present an exact optimum of these pools
as solving the complete kitchen. The first pool policy in retained v1 was even
weaker: every offered pair conflicted, so at most one program could be selected.
It is rejected as a main workload. V2 admits compatible multi-batch selections
but still loses the complete optimum. Preserve both negative diagnostics.

The v2 20-qubit logical probe retains feasible probability 1 within numerical
precision, versus about 0.017 for ordinary X mixing with the same fixed angles
and all-zero initialization. This validates the invariant, not an optimized,
hardware, equal-gate-budget or quantum-versus-classical advantage. Its largest
rotation has 11 neighbor controls. Routed depth, ancillas and native gate counts
are unknown; logical data width alone is not a hardware feasibility claim.

## Acceptance gates before calling this the main result

1. Retain meaningful competing multi-batch plans; report components, density,
   feasible states and operational gaps, not just qubit count.
2. Improve/version the restriction or use a small complete domain that preserves
   the decision we intend to demonstrate. Do not inject a classical optimum
   into the choices. Exact reductions need proofs; heuristic caps need gaps.
3. Train QAOA locally, with declared train/test cases, seeds and evaluation
   budgets. The method owner retains unsuccessful runs and initializers.
4. Compile both mixers for the same actual IBM target. Judge the benefit against
   the added controls/routing/depth; change the mixer if the cost is impractical.
5. Use checked raw returns directly. Keep CP/exact/SA as reference evidence;
   tiny correctness cases are not the project centerpiece or a hardness claim.
6. Freeze a bounded campaign before any IBM/VeloxQ use. Both remain held.

Alternative-menu, ingredient-stock and stochastic extensions remain proposals.
They must not silently invalidate this pair-conflict feasible-subspace proof.

## Mandatory post-repair clean: corrected physical core

The current core profile is core-contiguous-repair-clean.v2. Every outage case
includes a ten-minute recovery clean, even if C2 was idle and is never used again.
The conservative core fixes its time/worker by the declared earliest grid slot
compatible with committed operations. In this fixture W2 cleans A during 60–70;
C2's recovery clean is therefore W2/C2 during 70–80. Cooking on C2 cannot restart
until minute 80. The task is in raw plans and consumes both equipment and labor.

This is a fixed recovery-policy restriction, costing zero decision bits. It is
not the ambitious model's optimized choice of cleanup time/worker, phase-aware
failure or material-loss recovery. A quantum model with movable mandatory tasks
needs exactly-one continuation groups and an appropriate feasible mixer; the
independent-set-only proof cannot be reused unchanged.

Corrected exact tuples: S0=(0,0,1,0), S1=(0,0,1,2), S2=(1,0,0,1),
S3=(1,0,1,2). S2 misses the nominal B order. S3 serves only the urgent B order on
C1. output/catering-foundation-v2/ is the current common-method release.
The v1 outage results omitted this mandatory task and are superseded.
