# Catering: shared foundation, four independent method owners

Active work allocation — 17 October 2026, Europe/Warsaw.

**Accepted award strategy:** one integrated catering-production extension,
targeting the overall award and best use of VeloxQ. The user chose judging
merit, solution quality and execution over a quantum-advantage requirement.
No standalone SAT pivot or larger-cluster work is required for this decision.
The quantum method remains substantive; actual QAOA/VQE evidence will determine
which is featured. VeloxQ owns the larger same-model/portfolio experiment and
shared small-QUBO comparisons, not a separate application. Native and same-QUBO
classical controls, scope gaps and independent checks remain required.
Section15does not explicitly settle whether the same team can receive both
prizes. The existing four human owners are unchanged. V3paired-meal code and
frozen inputs are now implemented; foundation-v2 must not be silently replaced. No teammate
notification or VeloxQ/IBM call accompanied this strategy update.

**Current inputs:** use the complete35qubit cell at
`output/catering-complete-cell-v3/quantum-qubo.json` for a small unrestricted
paired-meal comparison. Use `output/catering-foundation-v3/S0..S3/quantum-qubo.json`
for fixed portfolios with measured restriction gaps, and its nested
`scale-128-qubo.json` / `scale-256-qubo.json` for VeloxQ/classical scaling.
Every method must read the [V3contract additions](CATERING_SOLVER_CONTRACT.md):
objective.quadratic, onehot_groups and actual meal_handovers. The original
foundation-v2 remains regression input. The independent classical reference is
native_slots; meal_reference is the exact/limited offered-domain reference.
No one should claim the larger fixed quantum pools solve the whole kitchen.
For35qubit simulation, use the one-hot-sector implementation or a suitable
MPS/other simulator; a generic dense double statevector needs512GiB. A VQE
ansatz that leaves the one-hot sector cannot use the current sector shortcut.

The user selected catering as the direction to try now and requested asynchronous
work across four people. Their clarification supersedes a component-based split:
**Codex builds the common foundation first; each person then owns an optimization
method against that frozen foundation.** “Qve” is interpreted as VQE.

This is an allocation of work to human team members, not a record that four
agents were started or that assignments were sent. The user and this chat own
the classical track as well as the foundation. The three other people take the
VeloxQ, QAOA and VQE tracks; their names are not assigned here.
Factory code, evidence and demo remain intact as a fallback. The catering
first runnable core is now released: see [the quick start](../catering/README.md)
and the frozen inputs in output/catering-foundation-v2/. The full ambitious
profile remains incomplete. IBM/VeloxQ execution holds remain unchanged.

**Method owners can work independently:** consume the V3inputs above when the
new profile is selected, preserving exact bundle hashes. V2 complete-qubo files
and the older instructions below remain historical integration examples.
The shared compiler/encoding is ours; do not rebuild it per method or silently
change the physical model. New workloads are versioned.

Read the [ambitious specification](CATERING_AMBITIOUS_SPEC.md) for the target
problem and the [solver contract](CATERING_SOLVER_CONTRACT.md) for shared inputs,
outputs, coefficient conventions and evidence requirements.

## Returning results to the shared checker

Every owner returns the standard method-result JSON with exact bundle SHA-256,
ordered binary samples, positive counts, literal energy, settings and work/timing.
Use this local gate before sending a result for integration:

```sh
.venv-stage2/bin/python -m catering.run evaluate \
  --bundle output/catering-complete-cell-v3/quantum-qubo.json \
  --samples PATH-TO-YOUR-RESULT.json --output output/NEW-checked-result.json
```

The same gate accepts each scale bundle with its own result/hash. It performs
no optimization or repair. A passing encoding check does not by itself establish
service quality, speed or superiority; preserve the checked metrics and failures.

## 1. Ownership

| Owner | Work | Primary outcome |
|---|---|---|
| Codex / foundation integrator | Raw kitchen/state definition, four event cases, generator, QUBO, decoding, independent checking, tiny exact audit, shared runner | A versioned, runnable problem everyone can solve without rewriting it |
| Person 1 | VeloxQ | Same-QUBO service evaluation at a capped budget; offline adapter first |
| Person 2 | QAOA | Simulated QAOA and compiled shallow IBM candidate |
| Person 3 | VQE | A distinct variational ansatz on the identical Ising cost, evaluated fairly |
| Us — user + Codex | Classical benchmarks | Raw native CP reference and same-QUBO SA/exact controls |

The shared foundation includes the demo-data export and integration hooks.
Nobody is assigned to rebuild the kitchen physics, invent a different loss,
or silently shrink the problem for their method.

## 2. What Codex finishes before the handoff

### The raw operational model

Freeze time/quantity units, equipment/worker occupation, allowed batches, sharing,
fixed departures, freshness, disposal and event ordering. Use the four scenarios
from the specification: S0 control, S1 urgent order, S2 cooker outage, S3 both.
Preserve one common executed prefix within each four-case fixture.

Define the recovery profile explicitly. If the first working version uses
whole-started-batch commitments and idle-boundary withdrawal, label it as that
profile. Phase-aware WIP and interrupted cooking are a later version until
their state transitions are verified. Every method gets the same version.

Start with the default lexicographic tuple (missed lots, waste, new batches,
plan changes). Ingredient/holding/power and monetary extensions are separate
named profiles. A disabled mechanism must not be advertised as active.

### The executable foundation

Proposed files owned by Codex:

    catering/domain.py
    catering/state.py
    catering/options.py
    catering/qubo.py
    catering/decode.py
    catering/check.py
    catering/contracts.py
    catering/audit.py
    catering/run.py
    catering/demo_export.py
    instances/catering/
    tests/catering/test_domain.py
    tests/catering/test_state.py
    tests/catering/test_qubo.py
    tests/catering/test_check.py

The integrator owns shared environment/lock changes, package entry points and
top-level documentation. Method owners request shared changes instead of
editing these files concurrently.

### Frozen fixture tiers

1. **Audit tier:** a complete tiny declared domain small enough for independent
   exact auditing. The four scenario cases have actual measured variable/coupler
   counts and checked witnesses or an explicit infeasibility certificate.
2. **Shared quantum tier:** a complete small instance or labeled conditional
   neighborhood with a useful batch/sharing/freshness tradeoff. Target roughly
   18–28 circuit qubits initially; publish actual counts rather than promising
   the target in advance.
3. **Scale tier:** broader generated domains for native CP, SA and VeloxQ.
   Full direct-QUBO counts can exceed the quantum tier. Restricted variants
   have separate IDs and a documented relationship to the broader reference.

Release the earliest verified tier first. The people can begin on that immutable
tier while later tiers are prepared. Never replace a case's content under its ID.

### Foundation release gate

The handoff is ready only when all of the following exist:

- A runnable loader and validation command with pinned dependency instructions.
- Four scenario inputs, declared profile and common-prefix provenance.
- Ordered semantic variable map, literal QUBO, objective weights and penalty bound.
- Decoder and independent resource/material/freshness checker.
- Tiny reference optima/bounds from independent enumeration or a checked reference.
- Exact energy/objective agreement on audited assignments.
- Actual bit/coupler/register breakdown and coefficient-range report.
- Method-adapter smoke test, deterministic random-bit fixture and result schema.
- Immutable bundle version/hash and a known-valid example output.

Core feasibility does not require serving every meal. A valid plan with explicit
missed demand can be optimal in a stressed case. Keep service metrics separate
from hard-constraint validity. If a case has no feasible physical continuation,
publish its status explicitly; do not fabricate a feasible reference.

## 3. Person 1 — VeloxQ

**Scale assignment (current):** the complete 35-qubit cell is the shared check,
not the main service experiment. Use the newly frozen **512 / 1,024 / 2,048
variable** 12-customer S3 workloads in `output/catering-velox-scale-v3/`.
Read [the concrete VeloxQ handoff](catering-methods/VELOXQ.md) for restore commands,
actual coupler counts, reference results, numerical limits and the capped pilot
gate. The earlier 128/256 pools remain integration inputs. No service execution
has occurred or been authorized by this update.

**Own:**

    catering/methods/veloxq.py
    tests/catering/test_veloxq_adapter.py
    docs/catering-methods/VELOXQ.md
    output/catering-methods/veloxq/

**Start without credits:**

1. Consume the frozen QUBO through the solver contract.
2. Implement serialization, variable mapping, energy/offset conversion and
   response parsing with offline fixtures.
3. Check binary/spin conventions against known small energies.
4. Prepare a minimal pilot manifest: case IDs, settings, repeats and a hard
   credit/job/runtime ceiling; automatic retries disabled.

**After explicit service authorization:** run the agreed pilot, retain all
responses/failures, and compare against same-QUBO SA/exact results. Expand only
within the approved cap. Do not run a broad tuning sweep against the account.

Report raw feasibility and quality, all timing components, actual quota use,
settings and backend identity. A GPU service result is not physical quantum
execution. A backend that returns only a final sample cannot establish
time-to-first-feasible without additional observable information.

**Done:** reproducible adapter, offline checks, explicit usage state and a
measured comparison if access is authorized. If access stays held, deliver a
ready pilot, not an invented service result.

## 4. Person 2 — QAOA

**Own:**

    catering/methods/qaoa.py
    tests/catering/test_qaoa.py
    docs/catering-methods/QAOA.md
    output/catering-methods/qaoa/

1. Implement QAOA for the frozen Ising Hamiltonian and variable order.
2. Verify state preparation, bit ordering, expectation and decoded energies on
   an independently enumerable tiny case.
3. Tune shallow depths and parameters locally on TRAIN cases within a declared
   evaluation/time budget; retain unsuccessful settings.
4. Compare raw samples with uniform/initializer and classical controls.
5. Freeze candidate circuits, compile for the actual IBM target when available,
   and report width, native two-qubit gates, depth, shots and usage estimate.

No hardware parameter search is assumed. Device execution requires separate
authorization and a verified remaining allowance. Stay within the foundation's
declared model; request a smaller shared fixture or neighborhood instead of
privately deleting constraints.

**Done:** verified simulator implementation, training/evaluation receipts and a
compiled hardware candidate when target metadata is available. A “best energy”
alone is insufficient without decoding and physical checks.

## 5. Person 3 — VQE

**Own:**

    catering/methods/vqe.py
    tests/catering/test_vqe.py
    docs/catering-methods/VQE.md
    output/catering-methods/vqe/

VQE is a variational minimization of the same diagonal Ising Hamiltonian, using
a circuit ansatz distinct from QAOA's alternating cost/mixer construction.
There is no separate catering objective for VQE.

1. Begin with a shallow specified rotation/entanglement ansatz, including its
   parameter count, entangler graph and initializer.
2. Verify expectation, measurements and semantic bit order on audit cases.
3. Evaluate a small predeclared ansatz/optimizer set on TRAIN cases.
4. Report parameter count, objective evaluations, circuit executions, shots,
   runtime, raw feasibility and decoded quality.
5. Compare with QAOA on the identical quantum-tier cases under matched
   evaluations/shots and separately matched wall-time budgets where feasible.

Because the Hamiltonian is diagonal, sampled bitstrings can score the full
QUBO in one computational measurement basis. Do not multiply the budget by
the number of Z/ZZ terms as if each required a different basis. Derivative
methods can still require many circuit evaluations; count them explicitly.

Product-state VQE, initializer-only and uniform sampling are useful controls.
A more expressive ansatz may train worse or produce mostly infeasible samples.
Keep negative results. Hardware VQE is optional and must share the same
centrally approved IBM campaign budget rather than claim another ten minutes.

**Done:** validated simulator path and a fair ansatz/optimizer comparison.
Do not promise VQE will beat QAOA; its purpose is an informative alternative.

## 6. Our track — classical reference and controls

The concrete formulation, supported adapters, comparison protocol and output
requirements are in [the classical reference design](catering-methods/CLASSICAL.md).
The raw CP implementation is catering/native_slots.py. It is the full declared
physical reference; the older catering/native.py is a program-domain master
and rejects the coverage-reward encoding. Exact literal enumeration and the
independent subset audit supply references on the identical quantum inputs.

**Own:**

    catering/methods/classical.py
    catering/native.py
    catering/native_slots.py
    tests/catering/test_classical.py
    tests/catering/test_native.py
    docs/catering-methods/CLASSICAL.md
    output/catering-methods/classical/

1. Implement a native scheduling reference from raw instance/state semantics.
   Build resource/quantity constraints independently of the QUBO conflict list.
2. Match the foundation's tiny enumerated optima before scaling.
3. Implement/use exact same-QUBO solving where tractable and a declared SA
   baseline on the precise matrices used by the other method owners.
4. Add sensible fixed-per-customer and sharing heuristics with checked outputs.
5. Produce reference status, incumbent, bound and runtime for each frozen case.

Distinguish full raw-model, complete option-domain and restricted-neighborhood
references. OPTIMAL in a smaller domain does not certify the broader kitchen.
UNKNOWN remains UNKNOWN; retain a valid incumbent and bound when available.

Use the same information, initializers and declared compute budgets. Report
hardware/allocation. WCSS metadata is verified, but actually allocating a new
remote job is a separate action from this work split.

**Done:** auditable reference table plus reproducible exact/SA/heuristic controls
against which all three other tracks can be compared.

## 7. Why this can run asynchronously

After a foundation bundle is released, each owner needs only that bundle and
the solver contract. They write their own adapter, tests, report and result
directory. Nobody needs another method's intermediate result to start.

Foundation tiny reference values are released first so our classical track is
not a bottleneck for the first round. Our stronger references later extend
the shared comparison without changing case contents. Method owners can
develop standalone smoke tests before release, but cannot claim catering
results from placeholder data.

All methods return raw normalized bit vectors through the same interface.
The central runner decodes/checks them and produces the common comparison.
Native CP may return a raw plan; compare its verified operational tuple, not
an invented energy against a QUBO it did not solve.

Shared changes are requested with: problem, smallest reproducer, affected
case/profile and proposed contract version. Codex owns the fix/version bump.
Do not solve integration problems by each owner maintaining a private schema.

## 8. Checkpoints and decision rules

These are milestone gates, not promises about hours of work:

| Gate | Integrator | Each method owner |
|---|---|---|
| F0 definition | Close core semantics, contract and fixture inputs | Read contract; identify method-specific resource needs |
| F1 runnable bundle | Release audited tiny/four-case fixtures | Run identical smoke test, then implement adapter |
| F2 first common result | Decode/check every returned output | Submit first raw result, including failure if that is the outcome |
| F3 comparable runs | Freeze evaluation budgets and case versions | Run the agreed simulator/classical evaluation |
| F4 external pilot | Verify credits/target, obtain authorization, lock combined cap | VeloxQ/IBM owners execute only approved workloads |
| F5 integration | Reconcile references, visualize real results, preserve limitations | Deliver reproducible report and interpretation |

If a method cannot solve a case, return an explicit failure/timeout record.
Do not stop the other owners. If the model needs a correction, regenerate a
new foundation version and rerun affected methods; old results stay labeled.

Suggested isolated branches are iwosmu/catering-veloxq, iwosmu/catering-qaoa,
iwosmu/catering-vqe and iwosmu/catering-classical. These are proposed branch
names only; no branch/worktree was created by this document.

## 9. Copyable assignment briefs

### Person 1

Implement the VeloxQ adapter for the frozen catering foundation using
CATERING_SOLVER_CONTRACT.md. Own only your method/test/report paths above.
Start with offline serialization and parsing tests. Keep all service calls
held until a specific credit/job/runtime cap is authorized. Preserve raw
responses and timing; return normalized bits for central decoding/checking.
Compare identical QUBOs with classical controls. Do not edit the loss or model.

### Person 2

Implement simulated QAOA on the frozen catering QUBO/Ising cases. Verify bit
ordering and energies, then run a bounded TRAIN tuning study and frozen
evaluation. Return raw samples and full budget receipts. Prepare shallow IBM
circuits and resource estimates if target metadata is available; do not
execute hardware. Own your QAOA paths and request shared-model changes centrally.

### Person 3

Implement VQE with a distinct shallow ansatz on exactly the same Hamiltonians
and quantum-tier fixtures as QAOA. Audit expectations and bit ordering, count
all optimizer/gradient evaluations, and compare equal-shot/evaluation and
wall-time budgets with appropriate controls. Return raw samples and reports.
Keep IBM use held and do not rewrite the scheduling model.

### Our classical track

Build the independent raw native scheduling reference and same-QUBO exact/SA
baselines for the frozen catering cases. Match tiny foundation references
first. Report status, incumbent, bound, objective tuple, feasibility and full
runtime at each representation scope. Own classical/native paths; do not
derive raw physical rules from the QUBO's conflict list or discard hard cases.
