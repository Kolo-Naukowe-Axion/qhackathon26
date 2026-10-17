# Historical catering guide — superseded 17 October

Use [the current guide](../../../catering/README.md) for setup and reproduction.
This preserves the earlier mixed v2/v3 handoff; statuses and test counts below are historical.

# Catering foundation: start here

Current extension: paired-course v3, 17 October 2026. One integrated project
targets the overall award and best use of VeloxQ. A substantive quantum method
remains central; classical methods provide references. Read the method, proofs and
acceptance gates in [the quantum-first design](../../CATERING_QUANTUM_FIRST.md).
The [classical reference design](../../catering-methods/CLASSICAL.md) defines
the independent raw CP model, exact same-input checks and SA controls, including
how to distinguish representation loss from quantum search loss.
For the talk and recording, use the [active presentation/demo plan](../../CATERING_PRESENTATION.md).
The [standalone project design and proofs](../../../PROJECT_DESIGN.md) define the
implemented model. The [quality audit](../../CATERING_QUALITY.md) separates
full-grid, same-portfolio and returned-plan quality and records current checks.

**Superseded results:** v1 omitted the mandatory post-repair clean in S2/S3.
Use V3for the paired-meal extension, or output/catering-foundation-v2/ for
component-demand regression runs. Existing v1 files are
retained as historical evidence; their outage answers are not spec-conformant.

Read [method ownership](../../CATERING_METHOD_WORKSPLIT.md) and
[solver conventions](../../CATERING_SOLVER_CONTRACT.md). The
[ambitious specification](../../CATERING_AMBITIOUS_SPEC.md) is the larger target,
not the scope already implemented here.

## New paired-course extension and shared research inputs

For an unrestricted small quantum example, use
`output/catering-complete-cell-v3/quantum-qubo.json`:35qubits, all32legal
programs of that cell, no choice cap. Its three idle qubits are included.
Raw/encoded/subset/sector references agree on(0,0,2,2). All6retained QAOA
simulator trials recover it, as do initializer and mixer-only controls. This
is an intentional correctness/method example, not quantum advantage. The
larger release below instead measures the cost of restricting program choices.

    .venv-stage2/bin/python -m catering.meal_cell --output output/NEW-COMPLETE-CELL

`paired-course-contiguous.v3` represents a meal lot as one main-component lot
AND one side-component lot. The physical allocations are reservations;
`meal_handovers` records actual complete meals, and `unpaired_disposals` records
reserved components discarded when their counterpart is missing. The independent
checker reconstructs these records and balances all produced components.
U counts priority-weighted missed complete meal lots; W counts discarded
component lots; B/R retain their meanings. Lot size is10portions. This differs
from the older v2 objective; do not compare raw energies or relabel old outputs.

For a meal, M/S are its 0/1 main/side coverage expressions. Its objective terms
are U=priority*(1-M*S) and unmatched waste=M+S-2*M*S. With unit groups these
expand quadratically without product-register qubits. Each demand-anchor block
has program-choice data qubits and one idle data qubit. XY mixers preserve one
choice per block; cross-block conflicts still require penalties and raw checks.

Frozen inputs: `output/catering-foundation-v3/`. Each S0/S1/S2/S3 folder contains:

| Files | Purpose |
|---|---|
| quantum-qubo.json / quantum-ising.json | Fixed shared quantum portfolio and exact4E Pauli-Z coefficients |
| scale-128-qubo.json / scale-256-qubo.json | Nested larger portfolios for offline VeloxQ integration and classical controls |
| *-reference.json | Exact/limited offered-domain CP status, samples, objective bound and checked metrics |
| raw-reference.json | Independent raw batch-slot reference without program enumeration |
| quantum-sector-reference.json | Exact one-hot-sector minimum and state counts |
| *-sa.json | Unrepaired seeded literal-QUBO annealing control |
| *-witness.json | Known all-idle continuation, explicitly not a solver result |

The report declares each portfolio's measured size/scope and restriction loss.
All larger pools retain every smaller pool choice. These are research inputs,
not a claim that a capped quantum pool solves the full kitchen. All4raw release
references reached OPTIMAL at their declared budgets. The33/35/31/35bit fixed
quantum pools miss5/7/5/6meal lots respectively versus raw2/3/2/3; they fail the
final full-kitchen quality gate and must be shown with those gaps. Changing
portfolios can explore more choices, but has no global convergence guarantee.
Sources are copied and hashed in source_snapshot/; v2 is preserved byte-for-byte.

The game-style viewer at `presentation/catering/` now consumes checked V3 evidence.
It replays the complete-cell actual QAOA sample, its controls, larger final quantum
plans, their exact offered-domain references and independent raw-grid references.
The source selector changes the actual schedule. Meal counters use complete
handovers, and mandatory post-repair cleaning occupies C2 and W2. Model & results
explains the QUBO and reports all larger pilot gaps. See
[the viewer guide](../../../presentation/catering/README.md). Rebuild the evidence with
`.venv-stage2/bin/python presentation/catering/build-data.py`; this invokes no solver.

Reproduce into fresh directories:

    .venv-stage2/bin/python -m catering.build_meal_release --output output/NEW-PAIRED-RELEASE
    .venv-stage2/bin/python -m catering.meal_campaign --output output/NEW-PAIRED-PILOT
    .venv/bin/python -m catering.meal_circuit --step output/NEW-PAIRED-PILOT/S3-seed-2026/step-00 --output output/NEW-CIRCUIT-AUDIT
    .venv-stage2/bin/python -m catering.verify_meals output/catering-foundation-v3 output/catering-paired-pilot-v1 output/catering-complete-cell-v3 --output output/NEW-VERIFICATION.json

The campaign declares4paired scenarios and2algorithm seeds before execution;
it is an exact-sector QAOA development pilot, not IBM hardware or a broad
statistical study. CP/exact evaluation references never initialize its plans.
The circuit command uses optional Qiskit and routes to a synthetic heavy-hex
topology, not a calibrated IBM backend. No command above uses VeloxQ, tokens,
network services or physical QPUs. Do not overwrite retained evidence.

## Larger inputs for the VeloxQ owner

The ready scale workload is `output/catering-velox-scale-v3/`: 12 customers, S3,
and nested **512 / 1,024 / 2,048-variable** paired-meal QUBOs. Actual couplers are
37,008 / 156,129 / 636,882. These are larger restrictions of 18,182 generated local
programs; density is measured, not assumed sparse. Restore large JSON matrices
with `node scripts/restore-compressed-evidence.mjs` after pulling.
Read [the VeloxQ handoff](../../catering-methods/VELOXQ.md) for scope, checked
witnesses, finite-budget CP results, coefficient checks and actual Phase D
service receipts. The first authorized cold runs are retained; further service
experiments need their own approved cap. The 35-bit cell remains the small shared
method comparison. Input generation itself used no service credits.

## Corrected v2 regression profile (historical shared handoff)

### What is implemented in v2

The core is a finite-grid kitchen with a committed started batch, optional new
batch yields, same-menu sharing, prep/cook/pack/clean phases, identified qualified
workers, calendars, fixed handovers, freshness and explicit surplus disposal.
Four observed cases share one fixed production state: normal, urgent order,
idle-cooker withdrawal and both. The nominal previous plan is provided openly;
it is not an optimal-plan teacher for option generation.

The executable profile is core-contiguous-repair-clean.v2:

- Started batches retain their whole remaining local program.
- New batches must serve at least one lot.
- Packing of one batch is contiguous, with one packing worker.
- A cooker clean immediately follows cooking.
- Waste is unallocated yielded lots explicitly discarded at cook completion.
- Outages must not interrupt committed operations. Such inputs are rejected.
- Every outage requires a qualified worker and ten-minute post-repair clean,
  even if the cooker remains unused. The core fixes it at the earliest slot
  compatible with committed work. Here W2/C2 clean at 70–80; no C2 cook may
  start before 80. Optimizing that task is outside this conservative policy.
- Aggregate ingredients/holding/power, money and phase-aware failure are disabled
  explicitly. Enabling them without an implementation raises an error.

The small fixture has two menus; one A batch is committed and only B requires
new production. Staff qualifications give one eligible worker per role. It
exercises batch yield/sharing, equipment/time choices and competing staff;
it does not establish general menu/crew-assignment scaling or the 240-meal kitchen.

Complete means all legal new programs on this declared core grid and policy,
not arbitrary packing or the full ambitious profile.

## Setup and reproduce

The verified run uses Python 3.14.6, NumPy 2.5.4 and OR-Tools 9.15.6755.
Use a separate environment for each method's quantum SDK dependencies.
Loading a frozen QUBO and using the integer energy/Ising helpers needs only
the Python standard library.

    python3 -m venv .venv-catering
    .venv-catering/bin/python -m pip install -r catering/requirements.txt
    .venv-catering/bin/python -m unittest discover -s tests/catering -p 'test_[!v]*.py' -v
    .venv-catering/bin/python -m catering.run build --output output/my-catering-foundation

The existing local .venv-stage2 also runs these commands. A build refuses to
overwrite an output directory. Defaults use local CPU only; no network service,
QPU, credit, H100 allocation or private credential is touched.

The test pattern excludes the optional VeloxQ adapter's pytest file. Its
dependencies and runner belong to that method environment; unittest discovery
of the entire directory in the lightweight foundation environment would fail
to import dimod. Qiskit circuit equivalence is optional in the core suite and
can be run separately in the SDK environment. Current local checks:

```sh
.venv-stage2/bin/python -m unittest discover -s tests/catering -p 'test_[!v]*.py' -v
.venv/bin/python -m unittest discover -s tests/catering -p test_meal_circuit.py -v
.venv/bin/python -m pytest tests/catering/test_veloxq_adapter.py -q
.venv-stage2/bin/python -m catering.audit_math --output output/NEW-MATH-AUDIT.json
```

The mathematical audit recomputes exact small-domain costs and physical pair
checks from frozen inputs. It does not train, repair a sample or submit a job.

## Frozen inputs for method owners

The first retained input release is:

    output/catering-foundation-v2/

Within each S0/S1/S2/S3 directory:

| File | Use |
|---|---|
| complete-qubo.json | Complete core program-domain QUBO |
| quantum-qubo.json | Deterministic cap-16 option restriction |
| quantum-ising.json | Exactly scaled Pauli-Z form; coefficients represent 4E |
| snapshot.json | Observed state and shared committed prefix |
| reference-complete.json | Native optional-interval master reference |
| reference-quantum.json | Same restricted-domain native reference |
| exact-quantum.json | Literal-QUBO ground states by all-bitstring enumeration |
| audit-complete.json | Independent feasible-program-subset audit |
| audit-quantum.json | Same audit plus exhaustive zero-penalty/bitstring checks |
| sa-complete.json | Seeded same-QUBO annealing, no repair |

report.json gives counts, objective tuples, restriction gaps and timing.
manifest.json seals raw artifacts and source versions. bundle_sha256 seals
each self-contained input. Preserve these files; write results to your own
method output directory. New fixtures/releases get new identities/directories.

## Actual register sizes

| Scenario | Complete bits / couplers | Quantum bits / couplers |
|---|---:|---:|
| S0 normal | 27 / 351 | 17 / 136 |
| S1 urgent | 91 / 3,782 | 18 / 149 |
| S2 withdrawal + repair clean | 1 / 0 | 1 / 0 |
| S3 both + repair clean | 10 / 36 | 10 / 36 |

The cap is a restriction, not a lossless encoding proof. For these particular
four cases it retains the complete core optimum. S2 and S3 retain every offered
program, so there is no domain reduction in those cases. Coefficient scales and
objective weights differ across differently sized bundles: compare operational
tuples across representations, never raw energies.

The exact tuples (U,W,B,R) are S0=(0,0,1,0), S1=(0,0,1,2),
S2=(1,0,0,1), S3=(1,0,1,2). S2 misses the nominal B order. S3 serves only
the urgent B order, on C1. The repair clean still executes in both cases.
S2 offers no new production program and has only its shortfall register bit.
These small cases validate physics and encoding; they are not the main quantum
workload or evidence of quantum/service advantage.

## Use the stable helpers

    from catering.contracts import load_bundle
    from catering.qubo import energy, ising
    from catering.decode import decode

    bundle = load_bundle("output/catering-foundation-v2/S1/quantum-qubo.json")
    # Your adapter returns Python int bits in bundle["variable_order"].
    # energy(bundle, bits) returns the exact original integer energy.
    # ising(bundle) gives coefficients of 4H with z=1-2x.
    # decode(bundle, bits) reconstructs/checks the complete raw plan.

For a known-valid integration smoke, evaluate a retained reference response:

    python -m catering.run evaluate \
      --bundle output/catering-foundation-v2/S1/quantum-qubo.json \
      --samples output/catering-foundation-v2/S1/reference-quantum.json \
      --output /tmp/catering-reference-check.json

The output path must be fresh. Your MethodResult should use the same bundle
identity and normalized sample structure; replace its method identity, execution
kind, settings, work and timings with your actual method's values.
Reported energies must be in original E units. If using quantum-ising.json,
divide its full energy including offset by four before reporting E.

## Ownership and method work

- VeloxQ: catering/methods/veloxq.py; offline adapter first, service held.
- QAOA: catering/methods/qaoa.py; simulate quantum-qubo inputs first.
- VQE: catering/methods/vqe.py; same small inputs/Hamiltonian as QAOA.
- Us: shared quantum-oriented encoding/checking and classical reference sanity checks.
- New encoding/mixer semantics: catering/quantum_first.py.
- Direct raw CP sanity reference: catering/native_slots.py.
- Shared model/compiler/checker/contracts: this chat's integrator ownership.

Every owner can work without another adapter's implementation. Do not edit
shared physics or change objective weights locally. Request a new shared bundle
if a different penalty, restriction or instance is needed. Do not spend VeloxQ
credits on these small smoke cases without authorization; larger useful workloads
remain a later foundation tier. IBM also remains held.

## Reference limits

The native master enforces raw optional equipment/attendance intervals with
NoOverlap and demand equations, without reading QUBO conflict penalties. It shares
the complete program generator and objective specification. The separate catering/native_slots.py now chooses raw
batch quantities, allocations, workers and times without enumerating programs
or reading QUBO conflicts. Both use the declared core packing/recovery policies.

The independent audit instead enumerates all potentially feasible program subsets
up to residual demand and checks raw operation/material records. Every new program
serves at least one lot, so larger subsets cannot be feasible. It compares those
optima with the native master and audits every QUBO bitstring for bundles up to
22 bits. It does not enumerate 2^91 bitstrings.

SA returns its best state from each restart. Its returned-state feasibility is
not a measurement of every visited state or an equal-budget comparison with
quantum shots. The release records work counts and does not repair returns.

## Quantum-first prototype

The shared unit-demand coverage-reward encoding removes shortfall bits and
supports a conflict-preserving mixer. See the design document above before
using output/catering-quantum-first-v2/. It is an audited design prototype, not
a trained QAOA result or an accepted main workload: its capped pools still lose
one demand lot against the complete raw reference. The old program-master
adapter rejects this representation to prevent double-counting service costs.
Generic QUBO/Ising loaders, energy evaluation, decoder and exact/SA adapters work.

All 32 catering tests pass. No IBM or VeloxQ calls were made. A kitchen replay
still loading foundation-v1 is historical and must be refreshed before it is
used to explain the corrected S2/S3 outcomes.
