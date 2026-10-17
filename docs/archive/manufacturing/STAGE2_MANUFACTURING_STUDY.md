# Manufacturing recovery: current implementation and evidence

Updated 17 October 2026. Local work; remote jobs, credits, publication and deployment remain held.

The main Stage 2 demonstration is **complete 16-operation pump recipes and the value of recovery capacity**. This implements the manufacturing direction in [the combined decision record](STAGE2_COMBINED_DIRECTION.md). The completed whole-recipe trajectory bridge now runs QAOA on a restricted representation of those same32-operation recovery inputs; the earlier smaller QAOA study remains separately scoped.

Read the [main-model mathematical specification](STAGE2_MANUFACTURING_MATH.md) for the literal QUBO, proof conditions and implementation links, and the [workspace design record](STAGE2_UI_DESIGN.md) for the revised desktop interface.

## The decision and measured result

Two pumps are due at minute 900. Heat capacity is withdrawn before planning. We can introduce replacement capacity usable from minute 360. Both cases retain all machining, component joins, assembly and final inspection. Start time, eligible machine and qualified worker are joint decisions; calendars, attendance, machine-only metric setups and minimum transfer lags are enforced. Time is discretized on a 30-minute start grid, with actual durations retained.

| Model | Heat capacity withdrawn | Replacement available |
|---|---:|---:|
| Complete native CP optimum, weighted late minutes | 45 | 0 |
| Complete native CP optimum, makespan minutes | 945 | 855 |
| Restricted candidate-pool optimum, weighted late minutes | 45 | 45 |
| Complete QUBO bits / couplers | 2,353 / 343,682 | 2,499 / 381,371 |
| Restricted QUBO bits / couplers | 781 / 25,818 | 781 / 26,307 |

This particular small pool misses the benefit of the replacement. Native CP certifies the four reference optima on their respective domains. Compiling a complete QUBO does not mean a QUBO backend has solved it. Sources: [matching recovery inputs/results](../../../output/manufacturing-recovery-v2/report.json), [complete-domain QUBOs](../../../output/manufacturing-full-recovery-v1/report.json). The older study-v1 heat cases have different due dates and remain separate.

The completed [nested capacity frontier](STAGE2_CAPACITY_FRONTIER.md) recovers the
replacement optimum with an answer-independent2,078-bit/196,228-coupler cap64
pool. The original781-bit pool is a failed representation, not proof that all
2,499complete-domain variables are necessary. A separate exact hard-deadline
query retains818bits/33,817couplers and answers whether an on-time schedule
exists at a declared cap; it does not preserve the soft-objective landscape.

The nine-case study also covers mill withdrawal, rush deadlines, added mill capacity, worker shortage and 32/64/128-operation nominal cases. Native CP returns UNKNOWN for the 64/128-operation complete models under its saved short cap, while checked heuristic/pool schedules provide upper bounds. UNKNOWN is neither infeasible nor optimal. The nominal 32-operation pool optimum is 945 versus the complete optimum 855: compression already costs 10.53% of that objective. Mill replacement does not improve the certified 32-operation nominal optimum; that negative result is retained.

All data are synthetic. The planning models do not include capacitated AGVs, physical buffers, power, stochastic quality or shipment simulation. Those belong to the existing rich physical-factory replay. Final inspection completion in this study is not a shipment claim.

## Completed price of realism and economic readout

The [feature study](STAGE2_REALISM_FRONTIER.md) removes one feature at a time
while keeping operations, resources, horizon1440 and grid30 fixed. It reports
actual unary/support/restricted bits, couplers, coefficient scales, build costs
and same-variant native references. The calendar case initially triggers the
dense-build guard; a separately tested blockwise audit supplies exact counts
without allocating its global quadratic dictionary. Continuous calendars give
9,322support bits versus2,499with the actual calendars, while optimum completion
improves855→765. Removing transfer lags weakens pruning enough to enlarge the
final graph. These are representation findings, not solver speed predictions.
Fresh nominal64/128references remain UNKNOWN, with checked raw objective
intervals[0,1748]/[0,4479331]; restricted optima are not global certificates.

The [audited economic ledger](STAGE2_CAPACITY_ECONOMICS.md) values four saved
schedules under explicit synthetic tariffs, machine/standby/base power, attended
labor, night premiums, starts and late penalties. It does not add monetary
optimization to the planning models. At late rate10 and capacity fee100, the
complete and enriched replacement plans yield net+374.5417/+372.0208 illustrative
PLN; the old pool yields−95.5958. All135sensitivity combinations and a separately
defined repeated-exposure/capital-price example are retained. Independent
minute-by-minute rational arithmetic verifies all four plan ledgers.

## Completed quantum bridge on the same full recipes

The [whole-recipe bridge](STAGE2_RECIPE_BRIDGE.md) chooses complete housing,
rotor, flange and pump trajectories while retaining every original operation
and cross-component constraint. Caps2/3/4 use18/28/36logicalqubits. All18QAOA and
18SA runs return checked restricted-optimal whole schedules; uniform sampling
reaches the optimum in6/18runs. Both scenario pool optima match the existing
complete-model optima on these specific inputs.

The constructive generator already supplies the recovery optimum, native pool
CP and SA are faster, and sector-table preparation is exact classical work.
The result establishes integration and concentration within a restricted domain,
not quantum advantage or quantum-discovered recovery value. The first trajectory
selection and both earlier fixed-boundary ladders failed and remain unchanged.
Independent circuit replay validates all six18-qubit circuits before/after
transpilation; larger28/36-qubit circuits are parsed/transpiled only.

## QUBO and a safe penalty experiment

One-hot groups select each operation's assignment and a makespan register. Incompatibility couplers enforce shared resources, precedence/transfer, setups and completion. The objective is `(horizon + 1) * weighted_terminal_tardiness + makespan`. Complete-domain support pruning is distinct from the capped, lossy candidate pools.

A checked feasible heuristic witness of objective U permits penalty P=U+1: every invalid bitstring costs at least P, all objective terms are nonnegative, and a valid bitstring of energy U exists. This preserves feasible objectives and global minima. It intentionally changes invalid-state energies. The witness is generated before the native reference; no CP answer is used as a teacher. Coefficient range is smaller, but solver performance need not improve.

The completed CPU annealing development pilot makes that limitation concrete. Five saved models × two penalties × two initializations × three seeds = 60 runs, eight reads and 256 sweeps each. Out of 240 reads per penalty, the original bound returns 21 feasible samples; the tighter witness bound returns only one. No run improves the supplied heuristic incumbent. Keeping that incumbent is a surrounding policy fallback, not a returned solver improvement. The pilot used the older study-v1 heat fixture, not recovery-v2. Its inputs/protocol and raw bitstrings are retained in [the pilot](../../../output/manufacturing-anneal-pilot-v1/report.json). This is development evidence, not a held-out backend competition.

## Visual demonstration

Open [the local production studio](http://127.0.0.1:4189/manufacturing/) while `python -m stage2.entry_demo --port 4189` runs. It shows actual saved schedules on the factory layout, worker attendance, all 16 recipe operations, machine/worker Gantts, resource counterfactuals and full versus restricted recovery. It reads independently checked plans and exact source hashes. It does not animate invented AGV journeys or silently label an unchanged nominal schedule feasible after a disruption.

The original physical factory and earlier planning views remain linked. The small [quantum microscope](http://127.0.0.1:4189/entry/) retains actual QAOA evidence; its success rates do not describe the 32–128-operation study. The new [recovery-centered review video](../../../output/manufacturing-video-v3/qfactoria-manufacturing-review.mp4) is161.9493 seconds, with actual UI captures and disclosed synthetic narration. Its [receipt](../../../output/manufacturing-video-v3/receipt.json) pins script and capture hashes. It remains a local review draft; it has not been uploaded or submitted. The earlier small-fixture video remains historical.

## VeloxQ experiment: prepared locally, performance still open

The useful backend question is which exact-query/enriched/complete representation
VeloxQ can exploit at useful total quality, time and cost. Compare native CP
solving the matching question, same-QUBO controls and the constructive heuristic.
Report raw schedule validity, encoded-register validity and common target
satisfaction separately; energies from different objectives are not comparable.
Preparation and full wall time matter alongside backend time. Warm starts must
be disclosed and matched.

Do not call the current coefficient reduction a performance improvement: our CPU pilot shows the opposite direction at its chosen settings. Do not infer service quota, backend precision, GPU type or expected success from serialization or published benchmarks. No VeloxQ execution has occurred. Six larger models now have twelve audited cold/witness-initialized HDF5 files in [the offline packet report](../../../output/manufacturing-packets-v1/report.json), including the2,499-variable complete replacement case and3,084-variable restricted128-operation case. Each warm file contains eight identical, disclosed heuristic witness replicas. Exact integer SDK-format files are audited entirely offline; importing its SDK receives an explicitly empty process-local VELOX_TOKEN.

The [gated VeloxQ runbook](STAGE2_VELOXQ_RUNBOOK.md) defines the useful question, initialization disclosure and budget gate. [The independent audit](../../../output/manufacturing-independent-audit-v1.json) passed132 manifest files,37 checked plans,6,301,798 coefficient checks and480 annealing samples without importing the SDK or executing a solver.

The new [cold sponsor packets](STAGE2_SPONSOR_PACKETS.md) cover818deadline,
2,078enriched and2,499complete variables, plus a separate enriched penalty
variant matched to the complete model's65,791penalty using a pre-CP heuristic
certificate. Every coefficient, label and offset is audited offline; no initial
Spectrum is included. Service acceptance and arithmetic are still unverified.
The expanded40-run local comparison returns640samples with zero encoded-valid,
physically-valid or target-success schedules, independently confirmed by a
reporting-only audit. That failure does not establish classical hardness or
predict VeloxQ performance.

## Rubric map and remaining work

| Scoring criterion | Evidence we can show |
|---|---|
| Correctness, 5 | Explicit formulation, independent checker, safe-pruning and penalty arguments, same-input native references |
| Quality, 5 | Certified32-operation references, nested pool/query frontier, integrated recipe QAOA and faster classical controls, honest bounds at scale |
| Creativity/complexity, 5 | Capacity decision, measured representation loss, nonmonotonic feature/encoding effects and audited conditional economic readout |
| Log, 3 | Dated protocols, snapshots, hashes, retained failures and ongoing development log |
| Project Design, 3 | Mathematical and software architecture, scope, tradeoffs and verification; the UI communicates this design |
| Video, 3 | Recovery-centered161.95-second local review cut, actual captures and disclosed synthetic narration; human review/upload remains |
| Live presentation, 3 | Recovery toggle, same-model comparison and concise defense; rehearse on final candidate |
| Consistency, 3 | One evidence-linked story across code, saved results, design, video and live demo |

These are whole-entry criteria, not a new30-point allocation exclusively to
Stage2. Official Stage1 baselines remain mandatory. The local merit experiments,
economic audit and offline assets above are completed. Final acceptance and
demo/video alignment belong to the final packaging record. Actual sponsor
execution, public-source/form steps and publication remain subject to their
existing holds; no score, eligibility or prize is guaranteed.

## Reproduction commands

```sh
.venv-stage2/bin/python -m stage2.manufacturing_study --output output/NEW-STUDY
.venv-stage2/bin/python -m stage2.manufacturing_study --cases heat-outage-32 heat-lease-32 --output output/NEW-RECOVERY
.venv-stage2/bin/python -m stage2.manufacturing_full --study output/NEW-RECOVERY --output output/NEW-FULL
.venv/bin/python -m stage2.manufacturing_anneal --study output/manufacturing-study-v1 --output output/NEW-PILOT
.venv/bin/python -m stage2.manufacturing_packets --output output/NEW-PACKETS
.venv-stage2/bin/python presentation/manufacturing/build-data.py
.venv-stage2/bin/python -m unittest tests.stage2.test_manufacturing -v
.venv-stage2/bin/python -m stage2.manufacturing_realism --output output/NEW-REALISM
.venv-stage2/bin/python -m stage2.capacity_economics --output output/NEW-ECONOMICS
.venv-stage2/bin/python -m stage2.recipe_bridge --anchor-policy first_and_incumbent --output output/NEW-BRIDGE
.venv/bin/python -m stage2.sponsor_merit_packets --output output/NEW-SPONSOR-PACKETS
npm run build
```

Outputs refuse an existing directory. Source snapshots pin historical study-v1; current scenario definitions use recovery-v2 due dates, so rerunning current sources is not a byte-for-byte recreation of the older heat fixtures. CP parallel search can return a different optimal witness. The packet preparer reads the six explicitly named retained models, not a newly solved reference. Python environments have different dependencies; the SDK and annealer run only in `.venv`, native CP in `.venv-stage2`.

## Post-hoc explanation of the original pool loss — 17 October

The [membership/energy diagnostic](../../../output/recovery-pool-diagnostic-v1/report.json)
compares a retained cap64on-time optimal witness with the original781-bit pool.
Of its32operation assignments,31already exist in that pool. The sole absent row
is **P02assembly on A1, attended by W06, at720–780minutes**. The witness's spare
H3assignment (P01housing, W02,360–480) is already present in the original pool.

Adding that known-reference row yields a782-bit/26357-coupler pool. Its encoded
witness passes the original checker and has literal QUBO energy855. The retained
complete-model optimum provides lower bound855; therefore the augmented pool
also attains855. The original pool's retained exact optimum remains65790.
No optimizer or sampler was run to establish this diagnostic; literal
compilation, membership, energy and raw-schedule checks suffice.

This is a privileged post-hoc explanation, **not a blind candidate generator**:
we read the added row from an already known optimal reference. It does not
replace the2078-bit deterministic enrichment result, imply a universal782-bit
formulation, or prove a minimal qubit count. The earlier experiment's generation
used no CPteacher; this diagnostic explicitly does. Existing sponsor packets,
inputs and historical results remain unchanged. The useful operational insight
is downstream assembly coordination, not just the availability of a furnace.

Reproduce in a new directory:

```sh
.venv-stage2/bin/python scripts/explain-recovery-pool-loss.py --output output/NEW-POOL-DIAGNOSTIC
```
