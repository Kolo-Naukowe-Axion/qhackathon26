# Stage 2 entry: deadline-aware manufacturing recovery

**Current scope:** this document specifies the separate smaller validation cell. The main manufacturing demonstration now also has a [whole-recipe quantum bridge](STAGE2_RECIPE_BRIDGE.md) on all32 operations, [representation frontier](STAGE2_CAPACITY_FRONTIER.md) and [capacity economics](STAGE2_CAPACITY_ECONOMICS.md). The small-cell results below retain their own scope and do not stand in for the larger factory.


## Current role of this document — 17 October update

The **main application centerpiece is now the complete-recipe manufacturing recovery study**, documented in [STAGE2_MANUFACTURING_STUDY.md](STAGE2_MANUFACTURING_STUDY.md) and [the combined direction](STAGE2_COMBINED_DIRECTION.md). This document retains the smaller residual-cell formulation and quantum evidence as a validation microscope. Its 18–34-qubit results are not 32-operation results. The prior narrated video is a small-fixture draft awaiting a recovery-centered cut. Historical language below describing this fixture as the current main narrative is superseded by this note.

Local candidate, 17 October 2026. This is the current submission narrative and
bounded quantum evidence. It supplements the existing factory and preserves all
earlier experiments. It does not replace their inputs, policies or final samples.

Mentor context supplied by the user: Paweł Góra's 12:23 response prefers staying
firmly within industrial ERP/factory scheduling, while saying he will consult
other jury members. We treat this as direct steering toward manufacturing,
not a confirmed formal rule forbidding every domain transfer. No mentor or
private team channel was contacted as part of this work.

## The problem we solve

**How should a pump manufacturer reassign unfinished machining, assembly and
inspection after a loss of capacity, while protecting customer deadlines?**

The decision jointly selects start time, eligible machine and qualified worker
for every remaining operation. It answers a practical second question: which
capacity matters—another machine, or a worker who can perform another task?
This is production scheduling inside manufacturing. It does not depend on
reclassifying retail logistics or catering as manufacturing.

The full synthetic two-hall factory remains our application environment. Its
15 machines, four AGVs, ten workers, physical components, buffers, energy and
quality rules are documented in [the factory specification](STAGE2_ENVIRONMENT.md).
The frozen final campaign contains 23,552 executions, with 592 original retained
traces freshly independently replayed. Its strongest tested controllers are
classical; see [the original results](STAGE2_RESULTS.md).

Our **quantum evidence is a complete, smaller residual-cell model**, not a
lossless encoding of that whole factory. It is a new synthetic fixture with an
explicit boundary, not a recorded snapshot extracted from a factory trace.
Earlier larger planning experiments and their 21.41% objective gap remain in
[the planning record](STAGE2_PLANNING_CORE.md). No result from one scope is used
as a bound for another.

## Complete numerical definition

Time is in minutes. Start times are multiples of 30; durations are 30 minutes.
The horizon H is 120, 150 or 180 in the quantum study. All material for the
remaining work is already allocated. Earlier component steps and flange
manufacture are complete. Every operation must finish by H; it cannot be
dropped, interrupted or reassigned halfway through processing.

| Remaining operation | Eligible machines | Skill | Predecessors | Release |
|---|---|---|---|---:|
| P01 housing, final machining | F1 or F2 | mill | completed boundary material | 0 |
| P01 rotor, final machining | T1 | turn | completed boundary material | 0 |
| P01 pump assembly | A1 | assembly | housing AND rotor | 0 |
| P01 pump inspection | QA1 | qa | assembly | 0 |
| Separate urgent component inspection | QA1 | qa | completed upstream work | 60 |

The machinist has milling, turning and, when cross-training is enabled, assembly
skills. The finisher has assembly and inspection skills. Each operation requires
its worker for the entire processing interval. Machines and people cannot serve
two overlapping operations. Intervals are half-open, so one can start when
another ends. A known outage removes F1 availability during [0,60); no running
operation is erased. All work is in one cell with zero transfer/travel lag.

The pump is due at 120, with tardiness weight 2. The urgent inspection is due at
90, with weight 1. Due dates apply to terminal operations only. Let

`T = 2 max(0, pump_QA_end−120) + max(0, urgent_QA_end−90)`.

Minimize `J=(H+1)T+C`, where C is the actual final completion. Because C≤H and T
is a nonnegative integer, this lexicographically minimizes weighted terminal
tardiness, then final completion. These are priority weights, not calibrated
PLN costs. No revenue, carbon or deployment benefit has been measured.

Excluded from this cell: AGV contention, power constraints, finite buffers,
sequence-dependent setups, stochastic quality, rework and worker travel. Those
are exercised separately in the rich factory. A 30-minute grid is part of this
model's definition; no claim of equivalence to minute-grid scheduling is made.

## QUBO and correctness

For every unary-legal assignment a=(operation, machine, worker, start), introduce
`x_a∈{0,1}`. Unary legality checks eligibility, skill, release, resource calendar
and horizon. Safe pairwise support pruning removes an assignment only if it has
no compatible assignment for another required operation. Iteration preserves
every complete feasible schedule; it does not query a CP solution or pick a
candidate cap. It is not itself a global feasibility solver.

Each operation's surviving assignments form a one-hot group. Introduce another
one-hot group `y_c` over possible operation end times, representing a completion
upper bound. Add P for each selected incompatible pair: machine overlap, worker
overlap, violated predecessor/assembly relation, and chosen completion bound
smaller than a selected operation end. Multiple violated reasons may contribute
multiple P terms.

The exact upper-triangular-once polynomial is

```
E = Σ_terminal assignments (H+1) w_o max(0,end_a−due_o) x_a
    + Σ_c c y_c
    + P Σ_groups (Σ_i z_i−1)^2
    + P Σ_conflicting pairs n_ij z_i z_j.
```

All objective coefficients are nonnegative. Let B be the sum, over the operation
groups, of their maximum objective coefficient, plus the maximum completion
value. Every feasible encoded objective is at most B. The compiler chooses
**P=B+1**. Any invalid bitstring violates at least one unit of a nonnegative
penalty and has E≥P>B. Therefore, **if a feasible schedule exists**, every global
QUBO minimum is feasible and minimizes the declared objective. At a ground state,
the completion register equals the actual last completion. A nonoptimal sample
can have a larger register; both numbers are retained, without changing actions
or substituting a reference plan.

`window_qubo.check_plan` independently checks the raw operation plan without
reading QUBO coefficients. `solve_cp` builds native interval/optional-resource
CP-SAT constraints from the original problem, not the QUBO or a quantum candidate
pool. On all six declared cases, its certified optimum equals the exhaustive
one-hot-sector minimum. Small tests separately check every emitted sector energy
against the original polynomial and compare the mixer to a full bitstring
simulation. These finite checks support, rather than replace, the argument above.

## Quantum method and the actual contribution

`assignment_qaoa.py` prepares a uniform W state in **every** assignment group,
including the completion register. Each cost layer is followed by ordered
nearest-neighbor `RXX(β) RYY(β)` rotations within each group. Those gates preserve
one selected bit per group and connect the entire product assignment domain.
Resource/precedence feasibility is still penalized; this is not a fully feasible
scheduling mixer. One-hot penalty terms are identically zero in this invariant
sector and are omitted from cost gates, with an exhaustive sector-energy check.

W states, XY mixers and CVaR are established methods, not our inventions. Relevant
primary sources include [the alternating-operator framework](https://arxiv.org/abs/1709.03489)
and [CVaR variational optimization](https://arxiv.org/abs/1907.04769).
Our contribution here is their complete assignment-domain implementation,
explicit manufacturing boundary, same-model comparisons, decision counterfactuals
and audited compilation/resource accounting.

The simulator stores exactly the product of the one-hot group dimensions. For
H=180 that is 24,576 complex amplitudes, versus 2^34 unrestricted amplitudes.
**The emitted circuit still uses 34 logical qubits.** This is exact classical
simulation within an invariant subspace, not 15-qubit compression. Preparing its
complete diagonal energy table enumerates states classically; this already
reveals the minimum to an external observer. The optimizer does not consume
that minimum or a CP schedule, but the experiment is not scalable computation
or evidence of quantum speedup.

The independent Qiskit 2.5.2 audit replays the emitted 18-qubit QASM on all
262,144 Hilbert-space states. Maximum probability error is
1.0061396160665481e−15, outside-sector probability 1.11e−16. Larger QASM is parsed
and logically transpiled, not independently full-Hilbert simulated. The 34-qubit
example has 852 CX gates and depth 322 after optimization level 1 with unrestricted
connectivity, including W preparation, cost and mixers. No physical routing,
noise resilience, QPU execution or hardware readiness is claimed.

## Declared protocol and results

Evidence: `output/stage2-entry-v2/`. Protocol and literal source snapshots are
written before runs. TRAIN seeds are 7,13,29. We compare p=1 expectation, p=2
expectation, and p=2 CVaR α=.25 using 128 exact simulated objective evaluations
and 8,192 Born samples. The configuration is selected by aggregate TRAIN
sampled-energy excess; **p=2 / CVaR .25** wins before TEST execution.

TEST seeds are 101,103,107,109,113,127,131,137,139,149. These test optimizer and
sampling randomness on the same six synthetic instances; they are not unseen
industrial instances. Full campaign time is 11.980 wall / 11.838 process CPU
seconds on this host, including compilation, preparation, TRAIN, TEST and the
small scaling checks. Peak process RSS is 137,199,616 bytes. Those are local
classical process measurements, not hardware benchmarks.

Each TEST case compares the identical pruned domain with uniform one-hot samples
and 32-replica Metropolis annealing. Quantum uses 128 simulated angle evaluations
plus 8,192 samples; uniform uses 8,192 samples; annealing uses 32×256 proposals and
returns 32 best states. **These are unequal compute budgets.** Timings in each
method record exclude shared compilation/sector preparation; model metadata
records those costs separately.

| Case | Variables / couplers | CP objective | QAOA valid | QAOA optimal actual schedules | QAOA exact measured minima |
|---|---:|---:|---:|---:|---:|
| Nominal H=120 | 18 / 55 | 120 | 10/10 | 10/10 | 10/10 |
| Nominal H=150 | 26 / 123 | 120 | 10/10 | 10/10 | 10/10 |
| Nominal H=180 | 34 / 218 | 120 | 10/10 | 10/10 | 9/10 |
| Outage, spare available | 32 / 200 | 120 | 10/10 | 10/10 | 9/10 |
| Outage, no spare | 22 / 95 | 11,010 | 10/10 | 10/10 | 9/10 |
| No assembly cross-training | 30 / 162 | 11,010 | 10/10 | 10/10 | 10/10 |

Across six cases QAOA gives 60/60 valid optimal actual schedules and 57/60 exact
encoded minima. The three misses cost 30 encoded objective units each because
the completion register is 30 too large; the operation schedules are unchanged.
Classical annealing gives **60/60 of both**. Uniform gives 59/60 optimal schedules
and 52/60 exact encoded minima. No quantum advantage is established; the point is
an auditable integrated extended-model formulation and quantified solver quality.
Do not extrapolate this six-case result to the whole factory.

The first campaign directory `stage2-entry-v1` retains a reporting failure caused
by a duplicate Python keyword. It stopped during first TEST row packaging.
The fix changed reporting only; configuration/protocol were not retuned from
TEST outcomes. Offline SDK packet v1 also retains an environment failure:
OR-Tools was absent in the SDK environment. Native references now run in their
own environment and their exact problem hashes are checked during serialization.

## What is creative and what it means

The strongest demonstration is a **capacity counterfactual**, not a new industry
label. With a spare and cross-training, the selected outage plan is:

1. Housing on F2 / machinist, 0–30; rotor on T1 / machinist, 30–60.
2. Assembly on A1 / machinist, 60–90, while urgent QA uses finisher, 60–90.
3. Pump QA / finisher, 90–120. Both due dates are met.

Remove F2 during the outage: the housing waits until 60, and the best pump ends at
150; T=60 and J=11,010. Remove cross-training with nominal machines: the selected
equally weighted optimum finishes the pump at 120 but the urgent component at
150, also T=60 and J=11,010. **Cross-training prevents deadline debt; it does not
necessarily mean a late pump in that ablation.** Multiple optimal schedules exist.

This demonstrates coupled material joins, machine alternatives and people—not
just a longer job list. It supports a capacity-planning hypothesis for this
synthetic fixture, not an economic purchase recommendation or calibrated ROI.
Selective-replanning and schedule-stability objectives are possible future
extensions; they are not implemented or claimed by this experiment.

## Scaling and VeloxQ boundary

Safe pruning at H=180 reduces 46/475 raw variables/couplers to 34/218. Increasing
the same residual model to 1,2,3,4 pumps produces 5,9,13,17 operations and
34/218, 114/1,787, 242/6,124, 418/14,645 variables/couplers. These scaling rows
are compiled and independently CP-solved; the larger rows are not QAOA runs.

Actual SDK HDF5 packets, label maps, coefficients, source problem hashes,
independent native references and serialization audits are prepared in
`output/stage2-entry-velox-offline-v4/`. Every packet checks 64 deterministic
random bitstring energies after reloading the actual serialized file, including
the Ising offset and `s=2x−1` convention. The SDK writer is a private installed API;
its version is recorded, and platform acceptance remains unverified. Nine packets
cover the six quantum cases and 2/4/8-pump scaling cases; the largest has 1,602
variables and 118,889 couplers, with native CP optimum 570 on its own input.

**Precision-aware integration:** v2 caught an actual energy mismatch at two
pumps: SDK 1.0.0 casts non-integral Ising inputs to float32 based on magnitude,
without checking exact coefficient preservation. Integer-QUBO Ising coefficients
are quarter-integral. Multiplying the entire Hamiltonian, including offset, by
four and supplying Python integers uses the SDK's exact integer storage path.
This preserves the minimizer and gives zero error on all 576 serialized-energy
checks. A separate independent integer-algebra audit checks **274,653 literal
coefficients**, labels and offsets across all nine HDF5 files, establishing
equality for every bitstring, not just the 64 probes per file. Evidence:
`output/stage2-entry-velox-coefficient-audit-v2.json`.
Return energies must be divided by four (and any documented omitted
offset restored) before comparison. The failed v2 file is retained. This fixes
local serialization; platform acceptance, internal arithmetic and supported
integer ranges are still unverified. It is not evidence of a VeloxQ service bug.

**VeloxQ service requests, uploads, jobs and credit use remain zero.** The current
preparer forces the process-local token environment value empty before importing
the SDK, without reading the previous value. Earlier offline receipts used
`token_accesses=0` to count explicit preparer lookups; that did not account for
the SDK's own import-time environment lookup. No credential was displayed or
used for a service request. Earlier receipts are historical and do not prove
the broader zero-lookup claim. The parent shell/configuration is unchanged.
Offline
preparation cannot establish sponsor-award eligibility, performance or quotas.
After separate authorization, use the same instances/decoder and compare the
whole submitted QUBO against CP and annealing. A useful sponsor story is the
capacity decision and scaling frontier, not relabeling a generic solver call as
novel. Start with one packet, inspect feasibility/energy and credit cost, and
authorize a bounded remaining campaign only after that. No backend id, price,
quota or runtime is assumed here.

## Reproduction and demonstration

Use the existing `.venv-stage2` (Python 3.14.6, NumPy 2.5.4, OR-Tools 9.15.6755)
and `.venv` (Python 3.11.15, Qiskit 2.5.2, SDK 1.0.0) environments.
`requirements-entry-core.lock.txt` records all 19 installed core packages;
`requirements-solver.lock.txt` pins the separate SDK/Qiskit environment. For new
core installations use `uv venv --python 3.14 .venv-stage2` then
`uv pip sync --python .venv-stage2/bin/python requirements-entry-core.lock.txt`.
Installing dependencies needs registry access; executing the models does not.
Choose new output directories; retained results are never overwritten.

```sh
.venv-stage2/bin/python -m unittest discover -s tests/stage2 -p 'test_assignment_qaoa.py' -v
.venv-stage2/bin/python -m stage2.entry_campaign --output output/my-entry-campaign
.venv/bin/python -m stage2.entry_circuit_audit --campaign output/my-entry-campaign --output output/my-entry-audit
.venv-stage2/bin/python -m stage2.entry_reference --output output/my-entry-references
.venv/bin/python -m stage2.entry_velox_offline --references output/my-entry-references --output output/my-entry-offline
.venv/bin/python -m stage2.entry_packet_audit --packets output/my-entry-offline --output output/my-entry-coefficient-audit.json
.venv-stage2/bin/python -m stage2.entry_demo --port 4189
```

Open `http://127.0.0.1:4189/entry/`. The scenario selector changes retained evidence;
**Run fresh QAOA** actually compiles, optimizes, samples, checks, and computes a
separate CP reference. New files are saved in `output/stage2-entry-live/` with
timestamp, source hashes, QASM and manifest. The static build shows retained
evidence with the fresh-run button disabled. No Python service is deployed.

## Local video review draft

`output/stage2-entry-video-v6/qfactoria-stage2-draft.mp4` is a 173.217366-second
H.264/AAC draft. It combines real UI screenshots and the actual fresh-button
action capture, with a clearly labeled synthetic macOS Daniel narration. It
is edited evidence, not a continuous recording of the full presentation. The
script, chapter transcript, capture timestamps, hashes and receipt accompany
it. Human review, upload and live rehearsal remain necessary. Earlier failed
renders (sandboxed empty speech, unavailable drawtext, then a duration over
three minutes) are retained; v5 passes duration/codec and sampled-frame checks.

To rebuild from the retained captures, using the existing Pillow environment:

```sh
.venv/bin/python scripts/build-entry-video.py --output output/my-entry-video --recording output/playwright/entry-recording-v2
```

## Point-by-point submission evidence

Stage 1 is the eligibility gate. The 30-point rubric assesses the whole submitted
project and its Stage 2 extension; the QUBO criterion is not an extra Stage-1-only
five points. Project Design means problem/model/algorithm specification and
justified decisions; frontend polish supports the demo but is not its definition.
VeloxQ is a separate sponsor award, not an extra row in the 30-point rubric.

| Criterion | Max | Prepared evidence | Remaining limitation |
|---|---:|---|---|
| Correct QUBO | 5 | Explicit extended model, P>B argument, exact domain/pruning, raw checker, native CP, QASM audit | No whole-factory lossless quantum formulation |
| Solution quality | 5 | Same-input CP optimum, measured QUBO gaps and actual schedule gaps, SA/uniform, all costs disclosed | Small synthetic cells; no advantage or unseen-instance generalization |
| Creativity / complexity | 5 | Deadline recovery, assembly joins, machine/worker/calendar coupling, spare/cross-training counterfactuals, larger factory | Novel algorithm/industrial partner not claimed |
| Development log | 3 | Dated decisions, failed studies, reporting failures and artifacts | Human review of narrative before submission |
| Project Design | 3 | This specification and root Project Design, exact units/objective/boundaries | No industrial calibration |
| Video | 3 | Local demo, prepared script, fresh action and evidence | Upload and final human review remain external |
| Live / Q&A | 3 | Timed script and precise answers | Human rehearsal and live delivery |
| Consistency | 3 | Manifest, literal snapshots, generated view and claim verifier | Final released commit/video/form must match |

These are evidence targets, not awarded marks or a promise of 30/30. Public MIT
repository, final video URL, team declaration and submission form remain release
duties. The challenge permits a five-minute video but the general regulations
give three; target **at most three minutes** to satisfy both. Deadline in the
provided materials is 18 October, 15:00 Warsaw. Publication, commit, push,
deployment and remote-solver holds are unchanged by local preparation.
