# Combined Stage 2 direction: the value and encoding cost of recovery

Decision record, 17 October 2026. The user authorized combining **iwos** (the
implemented manufacturing recovery work), **kari** (cost and capacity planning),
and **iwow** (the price of realism and a measured insight). This document defines
the combined direction; it does not relabel proposed experiments as completed.
The initial synthesis was separate from the other active instance. Subsequent
authorized implementation and review integrated the manufacturing study, solver
bridge and studio. The agreed technical scope now passes all 14 acceptance
requirements; [current status](STAGE2_STATUS.md) separates that closeout from
actual VeloxQ, final video, human rehearsal and release work.

## The entry in one sentence

**MetalTech must recover customer deadlines after losing capacity: which added
resource actually helps, and does a compact QUBO retain the schedules needed to
recognize its value?**

**Completed multi-agent work:** [nested enrichment](STAGE2_CAPACITY_FRONTIER.md)
retains the on-time optimum with 2,078 variables; an
[exact deadline query](STAGE2_DEADLINE_DECISION.md) uses 818 variables and 33,817
couplers. The [whole-recipe quantum bridge](STAGE2_RECIPE_BRIDGE.md) now runs QAOA
on a restricted representation of the same 32-operation recovery inputs, with
18/28/36 logical qubits and independently checked whole schedules. Its classical
generator already finds the optimum; no quantum advantage is established.
[Feature accounting and scaling](STAGE2_REALISM_FRONTIER.md),
[audited plan-cost sensitivity](STAGE2_CAPACITY_ECONOMICS.md) and
[cold sponsor packets](STAGE2_SPONSOR_PACKETS.md) are also complete locally.
The [review record](STAGE2_REVIEW_PASSES.md) preserves all failed earlier
sampling, boundary and trajectory-selection attempts. Actual VeloxQ performance
remains untested.

Keep manufacturing as the application. Paweł Góra's supplied reply expresses a
preference pending consultation with other jury members; it is not a verdict on
which of these three manufacturing ideas wins. The official specification asks
for an integrated extended model, correct compact formulation, same-model
classical comparisons, scaling and a measured price of realism.

## What comes from each idea

| Source | Keep | Qualification |
|---|---|---|
| iwos | Manufacturing rules, independent checker, native CP references, assignment QUBO, whole-recipe QAOA bridge and visual explanation | The earlier small cell, restricted whole-recipe bridge and rich simulator have different declared scopes |
| kari | Audited operating-cost and capacity-fee sensitivity, with larger offline VeloxQ packets | Saved schedules optimize the priority objective; weekly monetary optimization, calibrated ROI and actual VeloxQ performance remain absent |
| iwow | Per-feature encoding accounting, exact versus lossy reductions, a falsifiable hypothesis and a short coherent talk | No universal three-class theorem, automatic robustness, or automatic QAOA benefit from fewer bits |

## Main evidence: compression can hide the value of capacity

Use the 32-operation, two-pump full-recipe recovery comparison as the main
manufacturing case. It includes component joins, alternate resources, workers,
calendars, machine-only metric setups and minimum transfer lags. It excludes
capacitated AGVs, physical buffers, stochastic quality and energy optimization.
All parameters are synthetic. Both pumps are due at minute 900; replacement
heat capacity becomes usable at minute 360. These are known planning conditions,
not a failure secretly revealed to the optimizer after planning.

| Known scenario | Complete-model CP optimum: weighted tardiness / makespan | Restricted-pool CP optimum: weighted tardiness / makespan | Complete QUBO variables / couplers | Pool variables / couplers |
|---|---|---|---|---|
| Heat capacity withdrawn | 45 / 945 min | 45 / 945 min | 2,353 / 343,682 | 781 / 25,818 |
| Replacement heat capacity available from 360 min | 0 / 855 min | 45 / 945 min | 2,499 / 381,371 | 781 / 26,307 |

The native CP models certify these optima; the complete QUBOs are compiled
artifacts. No VeloxQ solution of them is claimed. The pool is solved exactly
within its retained assignments, yet misses the on-time replacement-capacity
plan. This distinguishes **representation loss** from **solver loss**.
The 146 extra complete-model variables and 37,689 extra couplers retain an
operational benefit absent from this particular 781-variable pool. This is not
a proof that every compact formulation must lose that benefit.

The subsequent deterministic nested cap64 pool retains the full 0/855 optimum
with 2,078 bits and 196,228 couplers. The key result is a **representation
frontier**, not a requirement that a solver search all 2,499 variables. The
whole-recipe trajectory bridge also retains both scenario optima in an explicitly
restricted domain. Neither zero observed optimum loss establishes losslessness.

Sources: [recovery v2](../output/manufacturing-recovery-v2/report.json) and
[complete-domain compilation](../output/manufacturing-full-recovery-v1/report.json).
The earlier `manufacturing-study-v1` has different due dates; do not combine its
heat-scenario answers with v2. A separate synthesis audit freshly rechecked all
four raw/pool schedules, objectives and input identities, using a checker whose
hash matches the recorded source:
[audit and source hashes](../output/combined-direction-20261017/evidence.json).
This audit did not rerun optimization or independently re-prove CP optimality.

## One integrated experiment, with explicit scales

1. **Quantum integration scale:** the completed
   [whole-recipe bridge](STAGE2_RECIPE_BRIDGE.md) covers all 32 operations through
   eight component-trajectory groups. All 18 QAOA and 18 SA runs match their
   restricted references; uniform sampling succeeds in 6/18. Its 18/28/36-qubit
   registers are simulated in their invariant sectors, not compressed quantum
   registers. Candidate generation already supplies the optimum, sector-table
   preparation is exact classical enumeration, and the classical controls are
   faster. The earlier 18–34-qubit residual-cell results remain separate.
2. **Manufacturing decision scale:** use the full-recipe recovery case above.
   Compare native CP, the complete QUBO and the restricted QUBO on matching
   problems, and explain exactly what the smaller representation discards.
   A complete-formulation theorem can apply across sizes; empirical quantum
   success cannot be extrapolated across different fixture boundaries.
3. **Scaling and realism:** the completed six-feature fixed-horizon ablation
   and fresh 32/64/128-operation scaling campaign retain explicit bounds,
   incumbents and guarded complete-build cells. Full native 64/128 solves remain
   UNKNOWN with checked objective intervals [0,1748] and [0,4479331]. The separate
   exact blockwise audit fills the continuous-calendar coefficient counts
   without allocating its global quadratic dictionary.
4. **VeloxQ question:** can the backend exploit the deadline, enriched and
   complete representations at useful feasibility, quality, total time and cost?
   Compare to native CP solving the matching question and same-QUBO controls. Also compare against
   the retained heuristic alone, separating returned solver samples from any
   incumbent kept by the surrounding policy. This question remains open.

The main-prize narrative is the formulation and measured decision consequence.
Within this same Stage2 extension, VeloxQ provides a controlled backend comparison once authorized. Its
published sparse-instance results are motivation, not our expected performance.
Existing holds on remote jobs, credits, physical hardware and publication remain.

## The price of realism: accounting, not slogans

The completed [price-of-realism table](STAGE2_REALISM_FRONTIER.md) measures six
feature variants at the same horizon 1440/grid 30, with native and restricted
references, unary/support/pool bits, couplers, coefficients and build costs.
The 34,300 naive assignment product is a family count, not a complete naive
Hamiltonian; its one-hot coupler count is explicitly a lower bound.

Worker calendars reduce the support-pruned graph from 9,322 to 2,499 bits while
worsening optimal completion from 765 to 855 minutes. Removing transfer lags
weakens exact pruning and increases the final graph from 381,371 to 457,015
couplers. These are measured representation effects, not automatic solver or
quantum improvements. The initially guarded calendar build remains in the
record; its complete counts come from the separately tested blockwise audit.

An additive assignment cost changes linear coefficients without new variables.
A compatibility rule may add couplers between existing assignments. Additional
machine/worker alternatives expand this encoding's assignment domain. Explicit
shared transport or immediate-predecessor state can require new variables.
These statements depend on representation and semantics. Zero added bits does
not mean zero additional circuit or classical construction cost.

Use measured pairs of full/restricted optima to distinguish pruning, grid loss,
candidate restriction and optimizer failure. Do not use the claim that a messier
factory is automatically easier for QAOA. If tested, plot variable count, actual
one-hot-sector feasible fraction and measured quantum success separately.

## Economic layer: completed valuation and sensitivity

The completed [economic ledger](STAGE2_CAPACITY_ECONOMICS.md) values four saved
plans using exact tariff, active/standby/base-power, attended-labor, night and
machine-start accounting. All rates and activation policies are synthetic.
A separate minute-by-minute rational audit checks every monetary line item.
This is valuation of priority-objective schedules, not monetary optimization.

At a declared late rate of 10 PLN per weighted minute, the complete recovery
plan's gross per-event benefit is 474.5417 PLN; a 100 PLN capacity fee leaves
374.5417 PLN. The old pool yields −95.5958 PLN net under that same fee, while
the enriched on-time plan yields +372.0208 PLN. The report retains 135 sensitivity
combinations and an explicitly hypothetical repeated-exposure/capital-price
example. Purchase cash flows exclude the per-event lease fee. No calibrated
failure distribution, robust policy or purchase recommendation is inferred.

Actual monetary optimization would require a new objective, justified penalties
and independent same-objective references. The present experiment establishes
the conditional value of replacement heat capacity, not a general mill ROI.

## QOBLIB: use its evaluation discipline; optional external controls

The user suggested [QOBLIB](https://zib-aopt.github.io/QOBLIB/index.html).
Its ten problem families include sports scheduling and graph problems but no
manufacturing job-shop family in the current list. It complements this work as
an external solver control; it does not supply the main factory case or verify
our manufacturing encoding.

Adopt its clear separation of formulation, coefficient range, feasibility,
optimality bounds, repeated runs, hardware paradigm and runtime. Record both
compilation/preparation and solve time, plus complete workflow cost. The
[participation guide](https://zib-aopt.github.io/QOBLIB/participate.html) recommends
at least five independent stochastic trials, preferably ten or more, and supports
objective-versus-time traces. Our reporting must still satisfy the challenge's
same-model factory comparison.

If the core entry is secure, a small predeclared subset of
[maximum independent set](https://zib-aopt.github.io/QOBLIB/problem/07/) instances
could stress the generic QUBO backend across size and graph density. Our
assignment-conflict graph is related but not interchangeable: mandatory one-per-
operation choices, costs and precedence remain factory semantics. Do not claim
that MIS performance proves scheduling performance, or compare leaderboard
timings as equal-budget experiments. No QOBLIB experiment or submission has
been performed by this synthesis.

## One Stage2 project, including VeloxQ

Clarified with the user on17October: VeloxQ is part of the manufacturing
extension, not a separate project. The official challenge PDF Section5 lists
VeloxQ within Stage2; Section11 evaluates integration, solution quality, scaling,
insight and reproducibility; Section15 describes end-to-end integration that
complements classical and quantum approaches. The sponsor award is a separate
judging opportunity, not a separate application requirement.

The common task is recovering factory deadlines and valuing capacity. Classical
code builds/audits the model; native references certify comparisons; local QAOA
uses restricted complete component routes; VeloxQ is intended to solve the
larger scheduling QUBOs. Each return must be decoded and checked against the
original factory constraints before entering the same capacity comparison.
Prepared packets demonstrate input correctness only. Actual backend execution
and useful performance remain unmeasured and held pending authorization.

The creative contribution to test is whether this integrated backend can retain
more valuable scheduling choices at a stated total budget, recover a deadline,
or supply distinct competitive plans. It is not sufficient merely to call an API
or show unrelated benchmark scores. Different representation objectives must
remain explicit. Simultaneous prize eligibility still needs organizer confirmation.

## Sponsor-prize priority: find a useful VeloxQ operating region

The user explicitly wants a workload where VeloxQ can contribute meaningfully,
with the aim of also competing for the sponsor prize. Prioritize a measured
factory solver experiment over unrelated external benchmark volume.

The current best candidate is **manufacturing recovery with a measured
representation frontier**. Compare the818-variable exact deadline query, the
2,078-variable enriched optimization pool and the2,499-variable complete
optimization QUBO on the common deadline target. Their energy objectives differ;
report raw schedule quality and query success, not cross-model energy gaps.
Then evaluate predetermined larger backlogs and window widths. A neighborhood
must preserve boundary resource occupation, required operations and assembly
dependencies. Report its restriction against the complete declared model.
The larger frontier is a proposed experiment, not an established VeloxQ strength.

The authors' [revised VeloxQ paper](https://arxiv.org/abs/2501.19221v2) reports
competitive results in several benchmark regimes, including very large sparse
instances. Our recovery graph is materially different: 2,499 variables and
381,371 couplers give mean degree305.22 and edge density12.22%. Sparse storage
does not make this a low-degree graph. Count one-hot cliques, coefficient range
and conflict density; optimize representation only with explicit quality checks.

Existing local annealing controls show a real feasibility challenge, not a
VeloxQ advantage. In `manufacturing-anneal-pilot-v1`, the 64- and128-operation
restricted tasks each return zero feasible samples across96 returned samples
(12 small runs). Budgets are only8 reads and256 sweeps per run; these are weak
development controls, not evidence of classical intractability. Their inputs
also differ from recovery-v2. Meanwhile native CP certifies the32-operation
replacement-capacity optimum in about4seconds in the saved run. A claim that
VeloxQ beats CP on that fixture would require direct measurements.

Predeclare the pilot ladder: known-target recovery, then growing backlogs and
window widths under fixed declared budgets. Compare (a) native CP on the original
model, (b) VeloxQ and stronger annealing controls on the identical QUBO, and
(c) the constructive heuristic alone. Separate cold versus checked-heuristic
initialization if the backend actually supports it. Record feasible return rate,
best decoded objective, time to a fixed feasible target, total workflow time,
backend use cost and distinct useful schedules. Do not count duplicate samples
as operational diversity or a retained incumbent as a returned solver success.

Possible useful results include faster feasible recovery at a stated target,
better schedule quality at a fixed total budget, several distinct competitive
plans, or larger retained scheduling domains without losing the capacity benefit.
Report all declared cases, including failures. The sponsor rules reward effective
integration, quality, scaling and insight; an SDK call or chosen favorable
benchmark is insufficient. No universal solver victory is necessary to explain
a bounded, measured contribution.

Three [cold packets](STAGE2_SPONSOR_PACKETS.md) now cover the 818-bit decision,
2,078-bit enriched optimization and 2,499-bit complete optimization models.
Every coefficient, label and offset passes exact offline Ising inversion.
Both original-bound and matched witness-tightened enriched packets are retained;
the latter matches the complete model's penalty 65,791. All packets are cold,
with no reference or heuristic Spectrum. Service arithmetic/acceptance and
resources remain unverified despite exact local serialization.

No actual operating region is established yet: remote calls remain zero.
The next decisive action is a bounded actual-backend pilot after the existing
remote-use hold is explicitly lifted, using documented backend limits and cost.

## Consolidated execution order and completion criteria

The review passes now provide an exact deadline formulation, nested enrichment,
whole-recipe quantum integration, feature/scaling accounting, economic valuation
and audited offline packets. Both failed conditional release ladders remain
historical evidence; the successful trajectory bridge uses a different domain
construction. Include the official
comparable-number requirement: baseline3×3 uses72 naive time-indexed bits,
39 after simple pruning, and our selected3-bit sequence encoding on the official
instance. Disclose its classical evaluation of all six common orders and its
limited applicability; do not claim a general three-qubit factory solution.

1. **Manufacturing evidence — complete locally.** The checked 32-operation
   recovery pair, nested representation frontier and fresh 32/64/128 scaling
   references are retained with source/input hashes. The production studio uses
   actual schedules; the richer physical replay remains separate context.
2. **Price of realism — complete locally.** Six fixed-grid feature variants
   report native/pool bounds, domain counts, couplers, coefficients and build
   costs. The count-only calendar supplement fills the deliberately guarded
   large coefficient matrix. Full large-scale optimization is not claimed.
3. **Quantum connection — implemented and audited.** The whole-recipe bridge
   retains all original operations in a restricted trajectory pool. Actual QAOA,
   uniform and SA samples, exact sector costs, native references and emitted
   circuits are retained. Independent full-Hilbert replay covers the six
   18-qubit circuits; larger circuits are parsed/transpiled only. Classical
   preparation and incumbent quality are charged, and no advantage is claimed.
4. **Economics and sponsor preparation — complete locally.** Exact plan-cost
   ledgers, fee sensitivity and a separately audited capital-price example are
   saved. The three cold representations plus matched enriched penalty control
   are serialized and audited. The actual VeloxQ experiment remains held until
   remote access and credit use are explicitly authorized; offline correctness
   does not establish service integration or performance.
5. **Close the submission.** Align the implementation, manufacturing study,
   combined direction, Project Design, submission description, README, log and
   final acceptance records. The local recovery-centered review video is under
   three minutes; preserve its receipt and verify alignment with final evidence.
   Rehearse the live demo/Q&A and verify reproducibility. Public
   MIT release, final video upload, team/form details and submission receipt
   require their existing explicit release steps. The provided deadline is
   18 October 2026 at 15:00 Warsaw time.

QOBLIB trials, additional domains and unrelated algorithm exploration stay
secondary to these steps. The objective is one coherent entry supporting the
main rubric and a meaningful integrated VeloxQ backend comparison. This plan does not
establish prize eligibility or predict jury scores.

## Three-minute presentation

- **0:00–0:25:** two pumps are due; heat capacity is lost. Which resource helps?
- **0:25–1:00:** show the full-model recovery schedule and the restricted plan
  that stays late even after capacity is added.
- **1:00–1:40:** explain one assignment bit, a resource conflict, safe pruning
  and the distinction between exact reduction and discarded choices.
- **1:40–2:20:** show the 45-to-0 weighted-tardiness result, model/coupler costs,
  and measured method/reference results with their actual scope.
- **2:20–3:00:** show the conditional break-even threshold and the scaling
  frontier; state which backend results exist and what remains untested.

The live demo, video, log and design must use the same input hashes and scope
labels. A small quantum example supports the method; the consequential
manufacturing result carries the application story. The frozen all-rule factory
remains explanatory context and separately evaluated controller evidence.
