# Technical claim register — 17 October 2026

Authority is the local [challenge PDF](../Quantum_Hackathon_2026_ERP_Challenge.pdf), especially §§4–6,8–14 (SHA256 `821b7d47a02cdf1d1e5bacc730ad030683d37a56e282b98c4e221675b01d1e99`). This is a read-only evidence audit plus this register, not organizer approval or a claim of submission. New results require an explicit dated update.

The defensible narrative is: **both mandatory baselines actually run and attain their exact optima; a certified instance-specific reduction preserves all five deadline-feasible B machine orders in three semantic bits; a much richer physical factory has checked classical/hybrid execution, genuine small simulated QAOA decisions, scoped exact references and measured development improvements.** Neither a full-factory quantum compression nor quantum advantage is established.

## Claims and exact evidence

| Claim that can be made | Evidence and required qualification |
|---|---|
| Both computational Stage1 gates are exercised | [Current selection](../output/stage1-selected.json), [A run](../output/stage1-compact-ready/quantum-2x2/run.json), [B run](../output/stage1-compact-ready/quantum-3x3/run.json). Concurrent Stage1 work selected actual1-qubit/p1 A and3-qubit/p2 B QAOA Aer runs,4096/4096 feasible shots each; root schedules independently recheck at exact4h/8h. The compact order-cost formulation pays factorial classical tabulation and is a separate representation from the Stage2 deadline-feasibility reduction below. The older4-qubit A/39-bit annealed B remain retained historical comparisons. See [fresh read-only audit](../output/stage2-search/current-stage1-readonly-audit-2359.json) and [full scope](STAGE1_COMPACT.md). No administrative eligibility/submission claim follows. |
| B at H8 has an exact three-bit deadline-feasibility QUBO | [Model/proof/verification](../output/stage2-search/rank-three-final/structural/), [independent root audit](../output/stage2-search/rank-three-root-audit.json). `E=a+d+ab−2ad−bd`, `c=1−a+ab`; three couplers, no encoding auxiliaries. All five machine orders are retained, including a non-permutation order. Three is minimal only for a deterministic computational-basis decoder retaining five distinct orders. It is not a general qubit lower bound or an exact makespan polynomial over arbitrary instances. Five order classes differ from the13 feasible time assignments in the older time-indexed audit. |
| The three-bit circuit genuinely ran in simulation | [Six QAOA runs](../output/stage2-search/rank-three-final/qaoa/summary.json): p1 ideal ground probability92.95% mean, p2 95.09%;1024 Aer shots/run, all selected observed samples validate at8h. Uniform already succeeds with probability5/8 per shot and succeeds at the equal-shot budget. Classical presolve remains real cost: prior770 DAG checks,90 SAT queries/172 nodes, plus14 additional queries/14 nodes; later exhaustive checks are validation. No quantum speedup follows. |
| Small simulated QAOA decisions affect an extended-factory execution | [Checked eight-initial-order trace](../output/stage2-search/checked-qaoa-8/trace.json), [historical summary](../output/stage2-search/checked-qaoa-8/summary.json). Fresh current-checker replay passes:10/10 including urgent orders. Its148 requests contain146 actual simulated circuits,94 trivial one-bit calls,51 coupled simulated calls, and2 oversized classical fallbacks. Max actual circuit5 total bits; max offered QUBO11 bits, with maxima5 core/6 slack. Zero physical calls, repairs or selected-versus-committed mismatches. A QAOA request is not automatically a quantum call. |
| Exactness exists on declared same-instance deterministic fixtures | [One-pump reports](../output/stage2-search/tiny-reference-final/): OPTIMAL566 automatic,1007 full attendance,576 delayed dispatch,139 compressed; each has a complete checked witness and equal CP bound. Corresponding heuristic times616/1018/616/158 use the identical fixture. [Multi-pump summary](../output/stage2-search/multi-reference-summary/report.json) proves two-pump automatic863 versus stronger heuristic1238. The longer frozen automatic run also proves three-pump optimum1191 (bound1191), versus heuristic1860. The later bounded16-worker same-instance run improves the four-pump witness1732→1567; the independently tightened interval is now[1480,1567], with no optimum claim (CPbound1466 remains separate from the stronger analytic1480). See [long reference evidence](../output/stage2-search/multi-reference-3600/). No stochastic flagship secondary gap follows. |
| A development tool-home cohort improves materially | [Sealed development selection](../output/stage2-search/tooling-selection/selection.json), [raw validation report](../output/stage2-search/tooling-routing-validation16/report.json). At n12, calendar control191/210 shipped and8/16 complete becomes208/210 and14/16 with hard homes; deadline debt123284→81161. These16 tapes100–115 informed selection and are not untouched tests. New kit/mode/recovery pilots have their own cohorts; do not attach this14/16 result to a different combined policy. |
| Real complexity is exercised, while some features remain inactive | [Activity audit](STAGE2_ACTIVITY.md) links hashed valid TRAIN0/VAL100 traces:14/15 machines, setups, actual full buffers/blocking, BOM joins, batches, maintenance, tool services, charging, worker walks, rental and bounded repair. F3 and stationary discharge are unused in those cases; raw stock stays≥18. A separate n32/WIP32 stress activates stock exhaustion but performs poorly. Enabled, exercised and binding are different claims. |
| Full-model secondary optimality remains unknown | Same-model classical heuristics and independent physical checking support performance comparisons; exact frozen candidate pools and simplified deterministic references do not close unrestricted factory policy/deadline-debt/cost gaps. Zero missing orders attains the nonnegative primary lower bound on a realized execution. A stronger nonzero example is now independently checked: n32/H14400/TRAIN6 has34 demands and34 housing blanks, but unavoidable P05 original-housing scrap means fulfilling all demands needs35 blanks. The checked33-shipment witness attains missing-order lower bound1. See [independent certificate audit](../output/stage2-search/quality-material-primary-bound/independent-seed6-audit.json). This is one realized-tape primary optimum at a240-hour horizon, not an all-tape policy or secondary optimum. |

The one-pump fixtures explicitly deactivate shocks, quality risk, alternative modes, calendar breaks, portable-tool moves and binding life/wear/traction/energy limits; singleton heat and continuous staffing are declared. Their exactness is conditional on scope guards and the CP model-to-execution argument. The flagship checker independently validates executions; it does not prove a solver's search completeness or general nonanticipativity.

## Metric, size and cost vocabulary

Actual comparison tiers are physical validity/terminal reserve, missing orders, **unweighted cutoff-censored deadline debt**, and energy-plus-investment cost. Some training/search methods additionally declare a CVaR term or bounded reward surrogate. `Factory.finish.total_tardiness_ticks` uses `max(0, shipped_tick_or_horizon−due_tick)` for every order. Checker `terminal_deadline_debt_ticks` matches it; checker `tardiness_ticks` counts shipped orders only. TRAIN0 hard homes has8347 total debt versus6907 delivered-only minutes. Due/family ranking weights do not implement contractual weighted tardiness. Carbon is measured separately; no hard operating/carbon cap or priced-carbon/churn objective is implemented. Macro action/weight-change counts do not measure schedule-stability penalties. Active operation/move preservation and reachable burn-in are narrower, supported claims.

Core bits choose offered actions; auxiliary/slack bits encode remaining local capacity; **total** is their sum. Local pair-conflict penalties need no extra bits, but classical feasibility filtering, tool/transport planning and omitted candidate alternatives still cost work. CP variables are not qubits; an allocated five-wire IQM proxy register is not five semantic scheduling bits. Offline native compilation is not physical ODRA execution or calibrated noise evidence.

[Encoding audit](../output/stage2-search/encoding-audit-24.json) counts8,976,072 nominal manufacturing-start alternatives at H5760, one-minute resolution,384 nominal operations. It explicitly omits other variable families and is not a complete global QUBO or a valid “millions-to-five” lossless reduction ratio. The [quantitative follow-up](STAGE2_REALISM_COSTS.md) now supplies26 explicit numerical variable families, a44-slot/order bounded-quality envelope and actual local constraint-family ablations. It retains source/instance hashes in `output/stage2-search/realism-costs-v3/`. Global linking, risk/contingency and nonanticipativity costs remain uncompiled; these are declared family counts, not a complete-global formulation. Classical preprocessing, exact-expectation angle search, teacher generation/training, rollout planning and full physical episode execution must accompany sampling costs. Local result timing has method-dependent encoding scope; angle-search timing is nested and must not be added twice. See [evaluator timing definitions](STAGE2_FINAL_EVALUATION.md).

## Formal delivery status and remaining obligations

| Challenge requirement | Audited state |
|---|---|
| Working A/B with official JSON (§§4,14) | Local computational evidence and correctly shaped integer-hour outputs verified. |
| Manufacturing extension and extended schema (§§5,14) | Supported. A separate richer executable domain is allowed. Baseline files stay unchanged. |
| Integrated reduction/comparison/scaling and same-model reference (§5) | Actual local QUBO/factory integration, matched heuristics and scoped CP references exist. Full global secondary gap remains unknown; retain that limitation and measure candidate restrictions. Quantitative declared-family costs and local ablations now exist in the follow-up above; a complete global encoding/gap is still unproved. |
| Public MIT repository with separated code (§6) | Local MIT LICENSE and baseline separation exist. At audit, `git ls-files stage2` returns no tracked files: current Stage2 work is local, not yet in the tracked delivery snapshot. Live read-only GitHub metadata at17October00:42UTC verifies the repository is private, so the public-source requirement is currently unmet; deadline contents/publication remain separate. Stage2publicationhold is preserved. |
| Project Design, dated log, run instructions and AI disclosure (§§6–8,12) | Files exist and README discloses AI. An initial stale-blueprint contradiction was reported; root has now synchronized the Stage2 sections of README/Project Design and prepended a dated log update, while preserving historical entries. [Current implementation entry](../stage2/README.md) records the executable scope. Final chosen-method/evidence synchronization remains necessary before delivery. |
| ≤5-minute video, ≤3-minute live demo plus Q&A (§§9–10) | Completion not established by this audit. Demonstrate the program, model, own decisions, development process and limitations; team understanding is an explicit requirement. |
| Team declaration, form submission by18 October15:00 UTC+2, scheduled defense (§§6,10,13) | Administrative status unknown here; no submission or organizer contact is claimed. |

The original coarse15-minute transport/full-attendance model and current one-minute/short-tending profile are different numerical models. Their capacity results cannot be presented as solver progress on unchanged physics. Likewise the environment proposal's weighted tardiness, priced carbon, schedule churn, emergency procurement, machine leasing and interruption/resumption remain proposals or unsupported mechanisms unless separately implemented and checked. The reserved256-tape protocol starting10000 was globally frozen and executed from00:32UTC on17October. Completed-cohort results now exist; the dated final update below supersedes earlier preparation status. Development-inspected1000–1031 tapes must not be relabeled untouched. No VeloxQ or physical ODRA execution, external checkpoint transfer success, completed publication, video or submission is established.

Post-audit evaluation hardening is documented in [the cross-report audit](STAGE2_CROSS_REPORT_AUDIT.md): actor override, anchored numerical instances, terminal feasibility, independent metrics and model-bound protocol weights. The strict postprocessor admits differing algorithm-source groups only with identical physical/verifier hashes and matching per-tape instances. Its eight actual DEVELOPMENT smoke episodes and nine tests establish contract execution; they are not reserved final measurements.

## 23:51 UTC update — corrected selector objective and simulator scope

The full contiguous TRAIN0–31 corrected-objective confirmation is retained at
[selector-reward-6117350](../output/stage2-search/axion-download-2348/selector-reward-6117350/).
All2240 executions pass the physical checker and selected/committed audit. At12 initial orders, exact original reward ships326/424 and completes6/32 factories; no-batch and priority-lex both ship422/424 and complete31/32, matching the strong priority policy on fulfillment. This is development evidence after training diagnostics, not an unseen test. The correction changes only reward semantics on identical offered physical constraints.

Under priority-lex, QAOA, SA and equal-shot uniform have identical12-order fulfillment for all three declared actor seeds7/13/29. No-batch has mixed actor outcomes, and the16-order exact corrections do not improve primary throughput. These results support the scoring diagnosis, not a universal solver improvement or quantum advantage. All actor results remain visible in the [complete summary](../output/stage2-search/axion-download-2348/selector-reward-6117350/root-independent-summary.json).

The separate [24-bit CPU simulator prototype](STAGE2_QUANTUM_SCALING.md) is correct against amplitude/energy references and solves saved11/19/23-total-bit crew pools. Those pools use the earlier batch-bonus objective. It has not replaced the five-bit factory backend, nor executed23-bit QAOA selections inside new full factory runs. At23 bits, the tested32-angle-evaluation/1024-shot p1/p2 settings are slower and less reliable than exact core enumeration and SA; stronger QAOA settings remain untested.

The432-case speed/mode development screen contains428 valid and4 invalid executions. The four turbo24-order TRAIN4 cases overlap a revealed F2 outage with maintenance; they remain failures. A narrowly optional maintenance-availability guard is being audited separately, without rewriting the frozen physical engine or upgrading earlier evidence.


## 17 October 01:00 UTC — untouched evaluation, still finishing

The globalpolicy/source seal is `final-frozen-bundle-v20p2/global-freeze-index.json`
(SHA496e56ca28b89a94a2bc86a3dcabd22bcfe8ed09b6f82355a497ac959473f44f).
Eight cohorts now have23,040 valid executions,576 original retained traces freshly
rechecked, and all2048 numerical config/tape instances freshly rebuilt.
The16/24-order MPC cohorts are still pending. The latest complete *partial*
aggregation is [seven-cohort report](../output/stage2-search/final-partial-0051-report/report.json);
MPC12 finished afterward. Selection stays fixed before final outcomes; final
rank reversals do not trigger policy switching.

- The selected96-hour controls fulfill everyorder with weighted frequencies
  98.97%(10initialorders),97.92%(11),94.98%(12),88.22%(13),80.66%(14),
  8.80%(16) and0observedof256(24). These are empirical model/tape results,
  not universal capacity limits or deployment guarantees. A zero-success
  bootstrap interval0–0 is suppressed; an explicitly assumption-bound
  conservative one-sided probability bound is reported instead.
- At16, selectedCEM6 meanmissing2.6906 is worse than the PPO-found constant
  control2.4194 and broadstatic2.6030. CEM24 retains an improvement:10.0209
  missing versus11.5992original and10.3953broadstatic. These controls
  have exact distinct contexts and recorded selection costs.
- QAOA minusSA at12 is+0.03203missingorders with nominal97.5%interval
  [−0.01438,+0.07938]; QAOA minusuniform is+0.01026 with
  [−0.04260,+0.06365]. Both includezero. No quantum improvement or
  equivalence is established. Across the three actualQAOAcontexts:452338
  simulatedcircuits,174965coupled,272854trivialone-bit,40455oversize
  classicalfallbacks; maximumactual5totalbits, maximumoffered25bits in
  QAOAruns. Othercomparatortrajectories offer up to27. No physicalQPU.
- The fixed32-order/240-hour policy fulfills everything on91.0156% ofweighted
  tapes; primary-optimum attainment is93.4375%, including trivialzero
  witnesses. This extends the calendar; resources and due dates are unchanged.
  Its mean deadline debt113997.54minutes remains large. It is not a96-hour
  scaling victory or a full secondary optimum.
- A separately declared posthoc audit-only replay supplies a full nontrivial
  final witness: seed10020,32demands,31shipments,L=U=1. P32/pump/1 must fail
  initialQA(.0076995 below everylegalmode's≥.01risk) and repairQA
  (.0054375<.02); finalpump replacement is not allowed. Independent physics,
  canonicalidentity, literalkeyeduniforms and originalmetrics agree. See
  [proof witness](../output/stage2-search/final-independent-audit/nontrivial-proof-seed10020/report.json).
  It is excluded from all256-tape estimates and the first-per-leaf presentation
  replay set. No deadline/cost optimum is proved.

The [final retained-activity audit](STAGE2_FINAL_ACTIVITY.md) quantifies the
physical work in exactlyeight predeclared traces per12/32context, without
promoting feature activation, capacity contact or eighttracecounts to binding
constraints or all256-tape rates. A bounded TRAIN-only schedule-neighborhood
audit now studies controller headroom; its offline per-tape oracle is neither
a deployedpolicy nor a generalization result, and changes no final selection.

## Complete final evidence —17October2026,01:22UTC

This supersedes the partial-cohort status above. All ten cohorts/74 groups now
complete23,552 valid executions. [Full report](../output/stage2-search/final-complete-report/report.json):
41 declared paired contrasts; [independent seal](../output/stage2-search/final-independent-audit/complete-audit-seal.json):
592 original retained full physical/identity/terminal/metric/telemetry replays,
every row freshly numerically anchored, global policy/source seal unchanged.

MPC16 improves mean missing to2.30141 versus selectedCEM2.69063; paired exploratory
95% difference−0.38922,[−0.56797,−0.21625]. It fulfills all demand with probability
0.17406. MPC24 misses11.26766 versus selectedCEM10.02094; difference+1.24672,
[1.06828,1.42094]. MPC12 improves against the selected cheap policy, while13 is
uncertain and14 regresses descriptively. No general look-ahead or RL superiority
is established. The selected-incumbent map remains pre-final and unchanged.

The [decision page](STAGE2_RESULTS.md) collects final capability, compute and
proof limits. [Material conservation](STAGE2_CAPACITY_BOUNDS.md#material-envelope-of-the-held-full-factory)
shows32 initial orders is the largest with no stock-only obstruction on both rush
branches; passing this condition does not establish a feasible schedule. The separate ideal independent-key
quality ceiling is a necessary-event relaxation, not achievable headroom or a
theorem about SHA independence. Two posthoc rare-PPO traces and one nonzero-proof
trace remain excluded from population estimates and the592 original replays.

### Later proof and terminology clarification

The independently reviewed `output/reference-bound-extension/` supplement raises
the guarded deterministic four-pump arithmetic bound to1482, hence[1482,1567]
with the checked witness. Actual saved CP bound1466 remains unchanged; no full
stochastic-factory gap follows. The later shipment-progress curve is descriptive
inside the fixed32-order/H14400 runs, not new shorter-horizon tests.

Quantum telemetry `qaoa_calls` counts selector invocations whose result has
`quantum_algorithm_simulated=true`. Earlier wording “simulated circuits” refers
to those actual simulated selection calls, not unique programs, total shots,
angle-objective evaluations or physical circuit executions. “Coupled” means a
nonzero coefficient in the encoded QUBO, including slack coupling; it does not
certify entanglement of every resulting state. Counts and outcomes are unchanged.

### Completed reference follow-up, 17 October 03:16 UTC

Job 6117555 completed on the unchanged four-pump reference: CP-SAT reports
FEASIBLE with incumbent 1541 and lower bound 1524. The current scoped interval is
**[1524,1541]**; 17 minutes is an upper bound on unknown incumbent suboptimality,
not the actual gap or an optimum proof. The older CP 1466, arithmetic 1482 and
incumbent 1567 records remain historical artifacts.

The raw output and its 1567 hint fail the general identity supplement's
birth-at-dispatch rule because the reference permits early empty/parked AGV
reservations. Their physical pickup and loaded motion occur after canonical
birth and source completion, as verified by a narrow reference-only audit.
A separate 1541 witness delays only move74's reservation start 1382→1420,
preserving every physical timing and recomputed metric, and passes both
unchanged general physical and identity checkers. The raw rejection is retained;
neither the original solver artifact nor a frozen checker is rewritten.
[Audit and source hashes](../output/stage2-search/final-independent-audit/reference-2h-6117555/report.json),
[second review](../output/stage2-search/reference-2h-methodology-review/final-seal.json).

This is separate reference evidence, not another final execution or an extension
of the 592-original-trace audit. The final 74 groups, 23,552 executions, 41
contrasts and selected policies are unchanged. Research allocation is complete:
431.9967 CPU-hours including failed jobs, zero recorded GPU-hours and zero
physical-QPU calls. [Immutable ledger snapshot](../output/stage2-search/final-compute-0316-summary.json).
