# Catering foundation: start here

Current corrected release: v2, 17 October 2026. The project is quantum-first;
classical methods provide reference checks. Read the current method, proofs and
acceptance gates in [the quantum-first design](../docs/CATERING_QUANTUM_FIRST.md).
The [classical reference design](../docs/catering-methods/CLASSICAL.md) defines
the independent raw CP model, exact same-input checks and SA controls, including
how to distinguish representation loss from quantum search loss.

**Superseded results:** v1 omitted the mandatory post-repair clean in S2/S3.
Use output/catering-foundation-v2/ for new method runs. Existing v1 files are
retained as historical evidence; their outage answers are not spec-conformant.

Read [method ownership](../docs/CATERING_METHOD_WORKSPLIT.md) and
[solver conventions](../docs/CATERING_SOLVER_CONTRACT.md). The
[ambitious specification](../docs/CATERING_AMBITIOUS_SPEC.md) is the larger target,
not the scope already implemented here.

## What is implemented

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
    .venv-catering/bin/python -m unittest discover -s tests/catering -v
    .venv-catering/bin/python -m catering.run build --output output/my-catering-foundation

The existing local .venv-stage2 also runs these commands. A build refuses to
overwrite an output directory. Defaults use local CPU only; no network service,
QPU, credit, H100 allocation or private credential is touched.

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
