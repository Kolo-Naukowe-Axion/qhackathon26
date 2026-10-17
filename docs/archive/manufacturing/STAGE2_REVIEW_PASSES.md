# Stage 2: independent review passes and resulting changes

17 October 2026. The user explicitly requested multiple subagent review passes.
Three reviewers examined rubric fit, VeloxQ usefulness and technical validity.
The process included independent critique, isolated implementations and local
experiments, followed by cross-checks of proofs, samples, candidate domains,
source manifests and claims. Existing remote/backend/publication holds remain.

## What changed

| Initial assumption or weakness | Review action | Result |
|---|---|---|
| The781-variable pool loses recovery value, so the2,499-variable full model may be needed | Deterministic nested enrichment, no CP-answer teacher |2,078-variable pool recovers the full0-tardiness/855-minute optimum; large complete domain is not necessary |
| The backend needs the entire weighted optimization Hamiltonian to answer the capacity question | Exact hard-deadline decision QUBO and independent native satisfaction reference |818variables/33,817couplers; unit feasibility penalties; same original recipes and constraints |
| A compact query should be easy to sample | Expanded cold binary and group-preserving annealing controls |40runs/640returned samples; encoded-valid, physically-valid and target counts all zero in an independent reporting-only audit |
| A small conditional block should connect QAOA to recovery | Two boundary-safe structural release gates from the original first heuristic parent | Neither yielded a supported block within24logicalqubits/12freed operations; those failures remain unchanged |
| The failed boundary ladders leave quantum integration unresolved | Complete component-trajectory encoding, then incumbent-preserving redesign |All32operations retained in18/28/36logicalqubits;18/18QAOA and18/18SA match restricted optima, with the constructive optimum disclosed |
| Feature accounting and economics were still proposed | Fixed-grid full-recipe ablations, count-only calendar supplement, exact plan-cost ledger |Measured counts/coefficients/bounds plus135cost sensitivities; independent monetary audit passes |
| Offline preparation covered older representations only | Three cold packet representations and matched enriched penalty control |Every coefficient/label/offset audited; no actual VeloxQ execution or service acceptance claimed |
| Comparison requirements were implicit | Recheck official§5 | Explicitly include baseline3×3 counts72naive/39pruned/3selected, with six-order classical enumeration disclosed |

The main question is now: **which representation retains the manufacturing
decision, and which solver can exploit it at a useful total cost?** This is a
stronger experiment than preserving a weak pool as a favorable comparison.

## Implemented results and their limits

**Nested optimization frontier:** original cap24 and expanded caps32/48 remain
45weighted minutes late. Cap64 reaches0late/855minutes with2,078bits and
196,228couplers. Every pool contains all earlier candidates. All ten references
are OPTIMAL on their own domains. The generation rule sees only raw inputs and
original columns, with fixed deterministic mode/time diversity. This is a known-
fixture development study, not learned/adaptive column generation or proof of a
minimum sufficient representation. [Full result](STAGE2_CAPACITY_FRONTIER.md).

**Exact operational query:** zero energy iff every original operation is
scheduled legally, each terminal due date is met and completion≤C. There is no
makespan register or weighted soft objective. Native reference proves outage900
impossible, replacement855possible and replacement854impossible. The818-bit
query is smaller partly because it asks a different exact question; it is not
lossless compression of the complete original objective landscape. The native
positive query takes about0.706seconds including construction, versus1.428seconds
for query compilation in this saved local run. This is not classical hardness.
[Formulation and evidence](STAGE2_DEADLINE_DECISION.md).

**Larger controls:** five fixed seeds,16reads each, original/query formulations
and outage/replacement cases. Binary SA uses1,024sweeps; one-hot SA uses4,096
proposals per read, with disclosed different work counts. All runs start cold.
Reference schedules and witness files never initialize sampling. Every sample
has a literal-energy and decoder audit. The feasible positive query reaches
energy1 but never0 at these budgets. The negative query also reaches1: heuristic
near-zero energy alone answers neither feasibility nor infeasibility. No
formulation or VeloxQ speed advantage follows from these observations.
[Frozen sampler study](../../../output/deadline-anneal-review-v1/report.json).
The [separate reporting audit](../../../output/deadline-anneal-report-audit-v2/report.json)
rechecks all640 retained bitstrings without resampling, verifies the original
manifest/input hashes, and confirms0encoded-valid/0physically-valid/0target.
It corrects the reporting method to assess physical plans independently of the
completion-register bits; the original conclusion remains unchanged.

**Preserved same-case quantum gate failures:** both structural release methods preserve the first
saved heuristic parent's real outside occupation. One ends with98candidate bits,
the other60, both with an empty mandatory supported domain after freeing12
operations. No sector enumeration, quantum sampling or exact solver is run when
the declared gate fails. These are failures of two greedy ladders, not proofs
that every small neighborhood is impossible. The earlier separate18–34-qubit
study remains valid at its own scope. The later trajectory bridge supplies a
different implemented connection; these conditional gates did not succeed.
[Gate evidence](STAGE2_DEADLINE_BOUNDARY.md).

**Completed whole-recipe quantum bridge:** eight component-trajectory groups
cover every operation in the unchanged 32-operation inputs. Nested caps2/3/4
produce18/28/36logicalqubits. All18QAOA and18SA returns reach their restricted
optima, versus6/18uniform returns. Complete-model optimum loss is zero on the
two tested inputs, but schedules outside the supplied trajectories are excluded.
The classical generator already finds the recovery optimum and the native/SA
controls are faster. Sector-table preparation is exact classical enumeration.
The earlier trajectory-selection failure is retained; v2 explicitly preserves
the constructive incumbent. Independent replay checks all six18-qubit circuits
before/after transpilation; larger circuits are parsed/transpiled only.
[Bridge and circuit evidence](STAGE2_RECIPE_BRIDGE.md).

**Completed realism accounting:** six feature variants share the same operation
set, resources, horizon1440 and grid30. Removing calendars enlarges the exact
support encoding from2,499 to9,322bits while improving completion855→765;
removing transfer lags can instead enlarge the final graph by weakening pruning.
The initially guarded calendar compilation remains in the record, filled by a
separate exact blockwise coefficient-count audit. Fresh64/128-operation native
references remain UNKNOWN, with checked upper bounds rather than invented
optima. [Full feature/scaling table](STAGE2_REALISM_FRONTIER.md).

**Completed economic valuation:** four actual checked plans have exact synthetic
tariff, active/standby/base-power, attendance, night and machine-start ledgers.
At late rate10 and capacity fee100, complete and enriched recovery produce
net+374.5417/+372.0208 illustrative PLN, while the old pool produces−95.5958.
This is plan valuation, not monetary optimization. An independent minute ledger
verifies all four records;135sensitivities and a properly separated capital-price
calculation are retained. [Economic evidence](STAGE2_CAPACITY_ECONOMICS.md).

**Completed offline sponsor assets:** cold818/2,078/2,499-bit packets plus the
matched65,791-penalty enriched variant have exact all-state coefficient/offset
audits. No Spectrum or initial solution is included in these packets. Actual
service acceptance, precision, account resources and performance remain open
under the existing hold. [Packet evidence](STAGE2_SPONSOR_PACKETS.md).

## Review corrections retained in the plan

- H3 replacement-machine assignments were already in the original pool. The
  lost optimum required coordinated missing choices elsewhere. The diagnostic
  reference rows were not inputs to the new enrichment rule.
- Do not compare energies between feasibility and weighted-objective models.
  Compare raw schedules' target satisfaction, actual tardiness and makespan.
  Report encoded validity separately from raw schedule validity: an incorrect
  completion register is not automatically a physical schedule violation.
- Positive-energy sampling failure is UNKNOWN. Native CP infeasibility and exact
  preprocessing certificates are separate evidence.
- Small QUBO coefficients do not imply unit Ising fields. The positive query's
  maximum absolute field/coupling is51 before scaling; backend arithmetic remains
  unverified.
- Penalty tightening preserves ground states but did not improve the earlier
  measured annealing pilot. Feasibility classification must decode schedules;
  `energy<P` is not exhaustive for every witness-tightened objective model.
- Best-of8,192 quantum success masks substantial per-shot/per-seed variation.
  Future quantum reports should include single-shot target probabilities and
  target probability against a declared shot budget, with training cost shown.
- QOBLIB is secondary. It helps reporting and optional external controls;
  manufacturing quality and native references remain the main evidence.

## Revised execution priorities

1. Freeze a representation comparison: original complete optimization, original
   restricted pool, deterministic enriched pools and exact hard-deadline query.
   Use the same original input identities and a common operational target.
2. Add the actual VeloxQ backend only after the existing hold is lifted, starting
   with the positive/negative known-target queries and validated energy scaling.
   Measure total cost/time, valid returns and schedule quality. Include native
   CP and both local control families. Scale genuine backlogs/windows after
   integration succeeds; do not pad unrelated graph blocks to inflate size.
3. Use the completed whole-recipe bridge as the integrated quantum experiment.
   Preserve the failed boundary/trajectory histories, actual classical incumbent,
   preparation/training costs and independent circuit audit. Do not promote its
   probability concentration as quantum advantage.
4. Use the completed feature/encoding table and independently audited economic
   sensitivity, preserving fixed-grid, model-ablation and price-assumption labels.
5. Update the production studio, submission description, video and final rubric
   sheet to this tested story. Preserve all unsuccessful experiments and the
   baseline comparable number. Keep whole-factory controller evidence separate.

These passes improve the entry and identify the remaining scientific gaps.
They do not establish sponsor eligibility, useful VeloxQ performance, a quantum
advantage or any predicted jury score.

Verification evidence is linked per experiment: tiny/exhaustive compiler and
boundary checks, incremental sampler checks, vector/scalar coefficient parity,
whole-plan native references, independent monetary arithmetic and actual circuit
replay/transpilation. Each campaign retains its own source/input hashes and
manifest. Global acceptance/test totals belong to the final acceptance record;
frozen failed campaigns remain intact.
