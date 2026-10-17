# Catering solver contract v1 — foundation handoff design

17 October 2026. The first runnable core now implements the loader, exact energy,
Ising conversion, decoder/checker, classical adapters and frozen fixtures.
Start with [the runnable quick start](../catering/README.md). Quantum/VeloxQ
adapters and the ambitious profile remain separate work.
See [work allocation](CATERING_METHOD_WORKSPLIT.md) and
[operational specification](CATERING_AMBITIOUS_SPEC.md).

The integrator owns this contract and shared code. Four method owners consume
versioned bundles and return raw results. Backend-specific circuits, optimizers
and sample formats stay behind adapters.

## 1. Common units and identities

- Times are integer minutes from the instance's declared local origin.
- Quantities are integer lots; the fixture declares meals per lot.
- Resource intervals are half-open.
- Scenarios are S0, S1, S2 and S3, with a declared revealed time/common prefix.
- Completed actions at a boundary are processed before the event; new starts
  are processed after revelation unless already committed in the input state.
- The default objective tuple order is U, W, B, R.
- All IDs are stable semantic strings; list order is never an identity.
- No method receives future realized events through its observation.

Every bundle has schema_version, bundle_id, bundle_sha256, case_id, profile_id,
scenario_id, instance_sha256, snapshot_sha256 and representation_id.
Hash immutable canonical inputs, coefficient files and ordered variable maps.
The representation record states complete domain, exact reduction or restriction,
with parent-domain ID and restriction parameters where applicable.

## 2. Raw model and boundary state

Instance fields include:

| Field | Required meaning |
|---|---|
| time_origin, horizon_minutes, grid_minutes, lot_size | Units/calendar |
| menus | Allowed yields, phase durations, attendance, freshness |
| demand_groups | Customer, menu, fixed departure, revealed time, lots, priority |
| equipment, workers | IDs, eligibility/qualifications, calendars |
| policies | Disposal, cleaning, event-order and continuation rules |
| capacities | Explicit enabled flags and any ingredient/holding/power limits |
| cost_profile | Objective mode, units and all prices if money is enabled |

Snapshot fields include current time, observed event, executed operations,
actual handovers, remaining stocks, WIP batches, packed allocations, running
operations/attendance, future committed reservations, prefix waste/cost and
previous unstarted plan identity.

The common checker must reject inconsistent stock/material/resource identities
before compiling a QUBO. A profile may omit a mechanism only by declaring it
disabled. Methods must not infer default physics from missing fields.

## 3. Operational plan output

A plan has plan_id, instance/snapshot identity, operations, allocations,
disposals and source metadata.

An operation records id, batch/task id, kind, start/end, equipment id and
identified worker attendance intervals. A handover allocation records demand
group, source batch, lot quantity, packing-operation identities and departure.
A disposal records source batch/material state, quantity, time and reason.

The checker reconstructs demands, resource use, freshness, material balances
and objective metrics from these records and the raw inputs. It must not
trust a method-provided valid flag or objective number.

## 4. Literal QUBO conventions

The canonical energy is:

    E(x) = constant + sum_i linear_i*x_i
           + sum_(i<j) quadratic_ij*x_i*x_j.

- Binary variables are exactly 0 or 1.
- Each off-diagonal pair is stored once with i<j.
- Squared binary terms are folded into linear coefficients.
- Keep the constant. No implicit factor of two or symmetric-matrix convention.
- variable_order[i] is the semantic identity of bit i.
- Registers declare purpose, ordered bit indices, integer weights and range.
- Include objective components/weights, literal penalty, proof bound and scope.

For serialization, exact integer coefficients/constant are decimal strings;
this prevents browser/JavaScript precision loss. Python in-memory arithmetic
may use integers. Reject NaN, unlabelled scaling and silently truncated values.

Required coefficient fields:

    constant: decimal integer string
    linear: ordered list of decimal integer strings, length n
    quadratic: list of {i, j, value}, with value a decimal integer string
    variable_order: ordered semantic IDs, length n
    registers: named ordered index/weight/range records

The bundle records n, coupler count, register breakdown, coefficient range,
generation time, memory where measured and all safe/unsafe reductions.
Method wrappers may normalize energies internally only if they restore original
units and document the transformation in the returned metadata.

## 5. Ising and measurement conventions

For quantum circuits:

    x_i = (1 - Z_i)/2.

Under the literal QUBO above, each linear coefficient a_i contributes a_i/2
to the constant and -a_i/2 to Z_i. Each pair coefficient b_ij contributes
b_ij/4 to the constant, -b_ij/4 to each Z_i/Z_j and b_ij/4 to Z_i Z_j.

The integrator provides this conversion with an exact representation, including
offset and any common scale. A VeloxQ backend using spin s=2x-1 needs a separate
explicit transformation; do not copy Pauli-Z field signs blindly.

Normalized samples are integer arrays [x_0,...,x_(n-1)] in variable_order.
Qiskit display strings and physical-qubit order are not the contract's bit order.
Adapters retain logical/physical/classical-bit maps and test all relevant
conversion paths. Do not reverse a bitstring by intuition.

Standalone smoke example:

    E = -4*x_A - 3*x_B + 6*x_A*x_B
    variable_order = [A, B]
    unique optimum = [1, 0], energy -4.

This is an adapter smoke test, not a catering result or a penalty certificate.

## 6. Adapter input and output

The common interface to implement is:

    solve_qubo(bundle, budget, method_config, output_dir) -> MethodResult

The same method may process several independent case bundles, but must not
merge scenarios into one stochastic objective without a new model/ID.

Budget fields distinguish:

- wall_time_limit_s and, where observable, backend-time limit.
- training objective evaluations and evaluation circuit counts.
- shots per circuit/total shots.
- repeats and seed where the backend supports it.
- service job/credit/QPU-time limits when applicable.
- initialization identity and scope.
- allowed external execution, default false.

Do not pretend unsupported backend controls were enforced. Report their status.
No adapter may silently retry remote calls, choose a paid account or repair a
sample unless the common protocol explicitly enables it.

MethodResult fields:

| Field | Meaning |
|---|---|
| schema_version, method_id, method_version | Adapter identity |
| bundle/case/representation hashes | Exact input identity |
| execution_kind | classical, quantum_simulation, physical_qpu, veloxq_service or illustrative |
| status | completed, timeout, failed, unavailable or not_run |
| samples | Normalized raw bit arrays, multiplicities and optional reported energy |
| configuration | Exact settings, initializer, seeds/support status |
| timings | Build/compile/network/backend/decode/total where observable |
| work | Objective calls, circuits, shots, repeats and actual budget use |
| environment | Packages, CPU/GPU/backend and allocation metadata |
| raw_artifacts | Local raw-response/circuit/count/log paths and hashes |
| failure | Structured reason/error when relevant, without secrets |

Samples can be infeasible; return them honestly. The central evaluator computes
literal energy, decodes a plan and independently checks physical validity.
Optimality is not a generic completed status. Record certificates/references
in separate fields with their domain, source and proof status.

Native references can implement:

    solve_native(instance, snapshot, budget, config, output_dir) -> NativeResult

NativeResult returns a raw plan plus solver status/incumbent/bound. The same
checker computes operational metrics. It does not fabricate a QUBO energy
unless the plan is also explicitly encoded in that particular option domain.

## 7. Fair comparison

Use identical bundle hashes within same-QUBO comparisons. Native full-model
results compare operational tuples with the scope difference disclosed.
QAOA and VQE share quantum-tier fixtures and the same cost Hamiltonian.
They may use distinct ansatzes, but initialization, tuning budgets, gradients,
shots and all measurements must be reported.

All Z/ZZ cost terms are diagonal and can be scored from the same computational
basis samples. Parameter-shift/SPSA/other gradient evaluations still count
as actual objective/circuit work. Exact simulator expectations and shot-based
hardware estimates are different evaluation regimes and need separate labels.

Report raw valid-sample rate, best feasible objective tuple, sampling frequencies,
reference gap/bound, total runtime and compute consumed. Retain invalid outputs,
timeouts and failures. Per-method repair is disabled by default. If later enabled,
show raw versus repaired outputs, repair time and a repair-only baseline.

Different seeds on one fixture are algorithmic repeats, not independent demand
instances. Four event cases sharing one prefix are paired cases.

## 8. Independence and delivery

After foundation release, a method owner can run entirely from immutable input
bundles, their adapter and the checker. No other owner's live process is needed.
Outputs go into method-specific fresh directories. Shared-source changes require
an integrator-controlled version bump; case contents are never silently replaced.

The first delivered method package contains:

1. One reproducible command and dependency instructions.
2. A passing smoke test against the frozen foundation.
3. One raw result per released case, including explicit failures/not_run.
4. A compact result table and method limitations.
5. Full raw evidence for every reported run.

IBM and VeloxQ use remains held until explicit authorization. Simulator/offline
adapter development does not require spending either allowance.
