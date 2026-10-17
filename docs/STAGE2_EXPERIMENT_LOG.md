# Stage 2 research run — 16/17 October 2026

Authorized window: 20:13 UTC to approximately 04:43 UTC. GPU allocation ceiling:
500 GPU-hours, not a spending target. The user explicitly excluded autoresearch;
this work uses ordinary model construction, independent checks and experiments.

## Model construction and falsification

The initial blueprint had 15-minute AGV spokes and a one-hour hall crossing.
Exact route lower bounds show 24 nominal pumps cannot finish in 96 hours on
four payload-one AGVs. This was a physical capacity contradiction, not evidence
that a larger optimizer or quantum computer was needed. The coarse instance
and implementation are retained under `output/stage2-search/snapshots/coarse-v0`.

The refined model uses one-minute transport and handling, while retaining the
original hour-scale manufacturing, shifts, due dates and disruptions: 5,760
ticks, 15 machines, four AGVs, finite destination reservations, blocking output,
portable tools, wear/service, qualified crews, robotic tending, material BOMs,
batches, manufacturing-mode/wear quality risks, bounded repair/replacement,
grid/solar/battery dynamics, delayed delivery and urgent revealed orders.

A second necessary-capacity certificate concerns one calibration kit:
4,872 minutes of nominal certified QA plus at least 480 minutes of servicing
exceed its qualified worker calendar of 5,040 minutes. This certificate assumes
no additional kit rental. The integrated model now permits one priced rental
with an eight-hour lead time and physical arrival at the tool store.

Several pilot failures were implementation/policy defects and were corrected:
counting output as input inventory; treating an old numeric tool reservation as
a permanent Boolean lock; repeatedly transporting a tool away before its worker
arrived; withdrawing WIP admission from jobs when later orders were released;
and walking during breaks. Independent corrupt-trace tests and fresh checks
guard against accepting their output as valid evidence.

## Evidence rules

Pilot numbers are diagnostic and change as the model is repaired. Final
comparisons use frozen source snapshots, complete instance tables, disjoint
training/validation/test tapes, identical physical models, independent trace
checking, and retained raw measurements. A feasible partial trace does not mean
all orders were fulfilled. Exact local QUBO optima do not give a global factory
optimality gap. No physical ODRA5 result or quantum speedup is claimed.


## First frozen comparisons (21:34 UTC)

Physical core `e96a2cd9...` is frozen and shared by grid, sequential learning and
threshold controls. The 2,688-case load/WIP/mode/rental grid passed every trace
check; 188 allocated seconds on 32 CPUs (6,016 CPU-seconds). The stronger 48-action
static grid then measured all 6,144 TRAIN episodes in 489.7 seconds wall time.

Fresh ordinary test tapes 1000–1031, 32 tapes per workload (not the reserved
stratified final set), give these unfinished-order means:

| Method | 8 initial | 12 initial | 16 initial | 24 initial |
|---|---:|---:|---:|---:|
| Tuned static | 0 | 2.375 | 5.656 | 12.875 |
| Scratch sequential PPO | 0.719 | 3.375 | 6.156 | 13.219 |
| One-action learned bandit | 0.344 | 3.438 | 5.656 | 13.531 |
| Initial open-loop CEM | 0.188 | 2.844 | 5.344 | 12.969 |
| Random dynamic actions | 0.031 | 6.094 | 8.125 | 15.375 |

All 640 test episodes passed physical replay. Static completed 32/32 at load 8
and 12/32 at load 12; scratch PPO completed 21/32 and 0/32. This is negative
evidence for scratch RL, not grounds to remove the baseline. Initial CEM used a
noisy single-training-tape incumbent, fixed in the next version. Actor evaluation
was argmax; stochastic evaluation is available separately and keeps actor replicas
nested within each factory tape. Raw data: `output/stage2-search/axion-results/learning-v1-6116807/`.

Jobs 6116889 and 6116894 test behavioral-cloning warm starts, validation-retained
PPO, paired reranked CEM and causal queue/energy thresholds. Their reused teacher
precomputation cost is reported separately. No GPU was allocated to these small
CPU-bound policies.

A structural compiler reduced the official B example to four interpretable pair
order variables. An independent stage-by-stage recurrence checked all 216 machine
orders, all 512 full assignments and all 16 reduced assignments; exactly five
deadline-8 schedules survive, all accepted by the unchanged official validator.
Classical partial-DAG/SAT preprocessing is charged. QAOA sampling concentration
improves over uniform on this tiny QUBO, but 1,024 uniform shots also find an
optimum with overwhelming probability, so no quantum speedup is claimed.


## Capacity and controller results (22:08 UTC)

All 128 initial rollout-MPC cases, 2,304 longer-horizon cases, and 1,024 stronger
routing/calendar cases passed replay. Retained under `axion-results/`.
At 12 initial orders, calendar-only dispatch with the tuned routing teacher
reduced mean missing work from 1.875 to 1.0 on TRAIN0–31; complete cases rose
14/32 to 17/32. At 8 orders the same calendar change worsened tardiness, so it
must not be marketed as universally better. Early vehicle prepositioning and
aggressive BOM bonuses often worsened congestion; all outcomes are retained.

Scenario lookahead with four independent futures per decision improved TRAIN0–7
means: at load12 missing1.75→1.375; at16 missing5.625→4.125; at24
missing13.625→12.625. Load8 remains complete with tardiness1060→304minutes.
The comparison used 1,116 allocated seconds ×32 CPUs; planning is expensive.
One-future lookahead at load12 was worse (3.5missing), evidence that noisy online
selection is not automatically beneficial. New bank-based closed-loop forecasts
preserve threshold-controller memory and compare2/4/8future samples next.

The full24-order factory can finish all eight TRAIN cases by240 factory hours
with WIP6/standard/rental;192h leaves0.625missing on average. At load16,192h
finishes all8; load12 finishes all8 at144h. These change the horizon, not physical
features, and retain late due dates: completion is not on-time production.
The 96h factory remains the main pressure benchmark. Global secondary gaps are
unknown; no larger horizon is presented as an algorithmic speedup.

The three-semantic-bit B model now independently retains every one of the five
H8 feasible orders, using c=1-a+ab and E=a+d+ab-2ad-bd. Exact validation uses all216
machine orders and512 full assignments; construction uses structural cuts and
SAT proofs, no complete-schedule labels. Three bits are information-theoretically
minimal only for a deterministic decoder preserving these five distinct orders,
not for arbitrary classical presolve returning a single answer. Tiny QAOA improves
concentration, not end-to-end speed. Original Stage1 selected artifacts are untouched.

A real480-minute common burn-in now supplies reachable WIP/active commitments;
all48 development witnesses and common-prefix checks pass. Detailed exported
public state is not a standalone restart checkpoint. A full executed prefix is
retained as the reachability witness. Final stratified tapes10000+ remain unused.

## Physical flow improvements (22:36 UTC)

The fine development frontier (1,344 valid cases, 252.6s on six local workers)
now includes ten initial orders plus possible urgent arrivals: the selected
prior12/QAguard2 policy completes all16 validation tapes100–115. Eleven initial
orders completes14/16 under its best tested calendar policy. These are
validation-selected results, not reserved-final performance.

Hard portable-tool homes materially improve the12-order validation cohort:
calendar control191/210 orders,8/16 complete tapes; hard homes208/210,14/16,
mean tardiness7705.25→5072.56minutes. All128 paired validation traces across the
tested contexts pass physical, terminal and causal-prefix checks. Soft homes
regress badly under high WIP; QAguard4 also regresses on this validation cohort.
Retain these interactions rather than assuming independent gains add together.
Selection evidence: `tooling-selection/selection.json`; source8117e603.

Observed assembly deadlock: A2's six input places hold two components from each
of three different products. An accepted missing rotor cannot leave QA1 because
its assigned assembly buffer is full. A separate whole-kit target/reservation
heuristic rescues TRAIN n12/seed4/guard4 from7/12 to12/12 orders, with unchanged
buffers, routes and independent replay. It does not guarantee freedom from all
deadlocks: unreserved QA-output blockers, returning defective pumps and
irrecoverable kits remain possible. Larger TRAIN search1152/1152 valid in132.8s
on32CPUs finds a family-admission/kit policy completing8/8 TRAIN cases at n12.
Confirming promising candidates on TRAIN0–31 precedes validation selection.
Sources frozen as v7-kitting, kitting277a5b97. No final tapes used.

Separate864-case tool-map/WIP/guard search is fully valid,88.5s on32CPUs. Mixing
one mill home into hallB sometimes helps n12 but does not establish a general
improvement. The2048-case family-admission-only search is fully valid,714.4s on
six local workers. Best n12 mean missing0.5 on TRAIN0–7; n24 still12.25 missing.
Workload, physics and all unfulfilled orders remain in every objective.

Completed896 selector cases all pass replay with zero selected/committed
mismatches. QAOA mode includes22,127 actual≤5-variable statevector calls among
23,674 local calls; larger local models use explicit classical fallbacks. Many
calls are uncoupled and must not be presented as hard quantum subproblems.
At n12, TRAIN mean missing: priority1.875, QAOA1.4375, SA1.21875. At n16,
priority5.15625 beats QAOA5.625. No consistent quantum advantage is established.

Warm-started PPO fits16,320/16,192 episodes in about1800s per seed on32CPUs.
Ordinary test1000–1031 results still trail strong static scheduling at low loads;
mean missing at n8 is0.375/0.1875, versus static0. Retained cost and negative
results are in `axion-download-2225/learning-v2-6116889/`. The enlarged MPC bank
cohort288/288 valid used1045.9 allocated seconds×32CPUs; TRAIN and VALIDATION
rows must be separated before performance reporting, not pooled as a test set.

The user stopped ODRA/VPN work. Normal SSH recovered without VPN; bounded CPU
experiments and local quantum simulation continue. GPU allocation remains zero
apart from the previously recorded near-zero-duration hardware verification.

## Recovery, objective diagnosis and certified primary bounds (23:25 UTC)

The frozen v8 paired recovery campaign6117261 completed768/768 valid TRAIN and
VALIDATION executions in74allocated seconds×32CPUs. TRAIN n12 family/guard4/kit
control improves28/32complete and1.40625meanmissing to31/32 and0.0625 with
physical accepted-component repacking. VALIDATION15/16complete stays15/16, while
meanmissing0.6875→0.125: a large stall is removed, but one case still misses two
orders. The latter are original P11, permanently scrapped after standard-mode
assembly+repair inspection, and urgent U01, still late. Earlier notes calling
both urgent were incorrect. n11 recovery reaches16/16validationcomplete with
mean cutoff debt2118minutes. No final tapes were used.

The384case paired TRAIN0–31 routing/recovery follow-up6117294 is fully valid,
39allocated seconds×32CPUs. n13 WIP6/guard4 without scoped ETA completes30/32
and453/456orders, versus27/32 and449/456 for WIP8. n14 WIP6/guard4/QA-only ETA
completes25/32 and476/488orders, versus21/32 and466/488 for WIP8 without ETA.
These are training-selected candidates. Standard assembly outperforms the three
new slower careful-mode heuristics on36 deliberately selected failed tapes;
all36traces are valid and retained, with no validation/final promotion.

The69case strong-recovery MPC pilot6117282 is fully valid,373allocated seconds
×32CPUs. At n16 on TRAIN0–7, no-planning meanmissing3.875 falls to2.75 with two
independent futures and2.5 with four. At n24 on TRAIN0–3 it falls12.25→11.5→10.75.
These small, partly failure-selected cohorts do not establish generalization.
All conditional futures receive physical-only checks; actual runs receive the
full immutable-tape checker. Full720case TRAIN/VALIDATION confirmation6117307
was frozen before execution, with roles separate and independent planning seeds.

The stronger1632case local-selector campaign6117286 is fully valid,163allocated
seconds×32CPUs. At n12 the strong priority decoder completes31/32(meanmissing
0.0625), whereas exact fixed-pool dispatch completes6/32(meanmissing3.0625).
QAOA actors7/13/29 give meanmissing2.59375/0.71875/3.625, so selecting only actor13
would be misleading. A later causal first-divergence audit isolates a concrete
surrogate defect: at tick420 the extra-batch reward chooses a two-part HEAT job
instead of a higher-priority rotor, also occupying the worker longer. Changing
only that tick's selection, then resuming exact dispatch everywhere, rescues
TRAIN seed2 from10/14→14/14 and seed4 from2/12→12/12. Worker-assignment alternatives
exist, but are not the demonstrated main cause; broader crew expansion alone
regresses. Reward ablations are pending. Quantum optimization cannot correct a
bad objective merely by solving its local QUBO more accurately.

The separate offline continuation audit used12coupled boundaries and39exhaustive
feasible-subset continuations over six TRAIN context/tapes. All are valid; exact
local reward is lexicographically worse than its realized one-tick continuation
oracle at8/12boundaries. QAOA, uniform and random-tie controls pick the exact
same actions at all12pools. This is a selected-state mechanism audit, not a
future-peeking deployed policy or a quantum advantage result.

The576case stronger fixed-policy horizon campaign6117258 is fully valid,
88allocated seconds×32CPUs. Resources, due dates and physical rules are unchanged;
only the cutoff changes. Its selected candidates complete all8TRAINcases at
n16/H144h, n20/24/28/H192h. n32/H240h completes7/8. These are extra calendar-time
results, not algorithmic speedups or a claim that all candidate policies work.

For n32/H240h, eight full frozen-v7 witnesses were rerun and independently checked.
Seven fulfill every order. TRAIN seed6 ships33/34, and a quality/material proof
shows one miss is globally unavoidable for this realized tape: P05's original
housing must fail both keyed inspections under every legal mode; fulfilling it
requires a second housing blank. All34orders would therefore require at least
35housingblanks, but only30+4exist. A conservative minimum-step quality floor,
exact keyed fractions and material knapsack give lowerbound1, attained by the
witness. All8cases attain the primary missing-order lower bound. The full deadline
debt/cost optimum remains unknown. This is TRAIN8, not held-out success or a
universal robust-policy guarantee. Source-bound proof and fresh checked witnesses
are under `quality-material-primary-bound/`; two independent audits agree.

Before final evaluation, the evaluator was hardened and development-tested for
actor seeds reaching callback weights, source/instance anchoring, exact horizon,
terminal reserve, independently reconstructed outcomes/carbon/cost, and protocol
probabilities/leaf identities. Separate strict cross-source comparisons preserve
old/new dispatch identities while requiring identical physical/checker sources
and paired instance hashes. No final factory outcome has yet been inspected.

## 2026-10-16 23:51 UTC — full TRAIN reward/routing confirmations

- Axion6117350, frozenv13:2240/2240 valid TRAIN0–31 selector-reward executions; zero decode mismatches. At n12, original exact326/424,6/32complete; corrected no-batch422/424,31/32; priority-lex422/424,31/32; strong priority422/424,31/32. Corrected exact mean cutoff-debt3505.53/no-batch and3439.03/lex versus3452.63/priority. n16 corrections regress fulfillment versus original exact, so no universal gain. All three QAOA/SA/uniform actors retain results; under priority-lex, all n12 throughput/late metrics match exact for all actors. No-batch QAOA actor mean missing0.07292 vs SA0.08333 vs uniform0.28125 (same32environments, actors nested); exact/priority0.0625. These development results do not establish a quantum gain.
- Axion6117376, frozenv14:192/192 valid TRAIN32 cases. n16 scoped QA routing improves442→449/552 shipments; n24 QA routing427→446/808; quarter join440/808. n24 quarter join lowers accepted-component waits376621→278740minutes and stranded92→67, while QA routing gives65stranded. The earlier TRAIN8 tie between QA routing and quarter join did not persist on32 tapes.
- Axion6117375, frozenv11:432 speed/mode cases;428 valid,4 invalid turbo n24/TRAIN4 maintenance/outage overlaps. Invalids are retained and cannot be candidate winners. n12 turbo/WIP6/guard0 completes TRAIN0–7 with mean debt3261.625; n16 eco/WIP6/guard4 mean missing2.875 vs standard/WIP4/guard4=3.875. Both are small-screen selection evidence only. Separate128-case TRAIN32 confirmation6117452 submitted, final untouched.
- Allocated elapsed:6117350=227s×32CPU,6117375=46s×32CPU,6117376=31s×32CPU. Source and raw data: `output/stage2-search/axion-download-2348/`. No GPUs or physical quantum calls used.
- Evaluator now supports held six-action adaptive checkpoints and explicit static corrected-reward composition.22 evaluator+10 comparator tests pass; exact artifact/source/feature/action/context/tensor contracts, canonical identity, actual QAOA telemetry and direct physical execution are tested. Unsupported reward/MPC/checkpoint option combinations fail before execution.

## 2026-10-17 00:14 UTC — scenario planning and independent learned-policy replay

The720-case frozen strong-MPC study6117307 is complete: all720 actual traces valid. TRAIN0–31 and reusedVAL100–115 remain separate in `axion-download-0001/strong-mpc-confirmation-6117307/root-independent-summary.json`. Replanning uses sixWIP/QA actions every1440minutes, independent scenario tapes, risk.25 and physically checked futures.

| Initial orders | ReusedVAL static mean missing | Two futures | Four futures | Selected interpretation |
|---:|---:|---:|---:|---|
|12|0.125|0|0|Both finish16/16; four-future mean debt2855 versus two2887.94 and static2979.81 |
|13|0|0.1875|0.1875|Static finishes16/16; planning regresses |
|14|0.375|0.375|0.375|Mean debt6440.88→6000.38/6000.25; no primary improvement |
|16|3.6875|2.0625|2.1875|Two futures wins on this development cohort; four costs more and is worse |
|24|11.75|11.25|10.9375|Primary gain, but very incomplete at96hours |

These controls are their exact original strong contexts, not the upcoming fully tuned static grid. For example, WIP6 alone already improves16-order performance. Planning cost is material: summed mean per-episode planning wall at12 is75.55s(two)/156.39s(four), versus no rollout planning in the static control; at24 it is125.24s/248.11s. Allocated job cost2429s×32CPUs; noGPU/QPU.

Independent six-action v12 post-fit seals/replays validate all3selected fits:144/144 selectedVAL traces pass anchored physics, terminalreserve, independentmetrics andcanonicalidentity; all keys match retained selected checkpoints. PPO2026 learns constantWIP6/guard4 at12 and16; matchingstatic controls reproduce every physical outcome. PPO2027's16-order switching policy is worse than that constant control. CEM is a learned open-loop8segment time policy (not state-adaptive RL): at16 it has31missing across16VALtapes versus44 for its best matching used static action; at24 it has164 versus188. Its12-order schedule completes16/16 with totaldebt48840, versus50175 for constant6/4. These are development-selected results, pending the broader matched static control and untouched test.

Optional maintenance availability correction now has actual end-to-end replay evidence. Guarded-v12 replay6117469 runs144/144 selected cases: every operation/move/walk/event/energy/metric/admission list matches the original traces; no guard activation in these cases. New guarded-MPC development6117467 (6CPUs,267seconds) has6/6 anchored+identity-valid traces on0/100 at12/16/24; all six metrics exactly match corresponding original720-cohort rows. The separate turbo24/TRAIN4 diagnosis retains4invalid originals and4guarded valid traces.

Legacy saved-checkpoint preflight6117477 failed before factory execution: duplicate keyword expansion in the context-static weights merge rejected a real inherited `policy_seed`. This was corrected with ordered dictionary merging and a realistic override regression before any final execution. Failed1s×32CPU allocation retained; repeat preflight6117483 uses new immutablev18p1 source.

The final analysis plan and its prospective third-static-slot clarification are retained under `final-preparation/predeclared-analysis-plan{,-v2}.json`. No reserved final factory has run.

## 2026-10-17 00:32 UTC — global source/policy freeze and reserved final launch

The guarded factorial is complete:9216/9216 TRAIN cases and192/192 reusedVAL cases valid. At24orders, staticgrid TRAIN-best466/808, original427/808; VAL-selected234/402 versusoriginal214/402. CEM6 retains238/402 on the same reusedVAL (four fewer missing than broadstatic); these are selection data, not final generalization. At12, selectedstatic ships210/210with cutoffdebt47641; at16,CEM6 has31missing versus35broadstatic. Exact artifacts/options/costs retained; neither RL nor quantum superiority assumed.

The actual frozen CEM6 time schedule plus corrected local QUBO integration completed264/264 physically/identity-valid TRAIN0–7 cases, with all33predeclared seed0traces and allthree stochasticactors. QAOA average fulfillment worsens at everyload; at24 it averages118.33/204 versuspriority128/204. Exact local optimization also regresses. No VAL/final adapter selected. Recorded14126actualsimulatedQAOAcalls,6875coupled,7150trivialone-bit,zero physicalQPU and zero decode failures. The prior264 packaging failures from omitted bom_probe dependency remain separately retained. See STAGE2_HYBRID_SCHEDULE.md and STAGE2_METHOD_SELECTION.md.

Full local Stage2 suite:378tests PASS in123.487seconds. New concrete finalspecs receive114 actual DEVELOPMENT0/100 executions, allvalid and strictload/select audited; frontier adds18validactualruns. Legacy preflight42valid and guardedMPC6valid previously retained. Independent reviewer verifies allcheckpoint/source/actor/domain contracts.

Final globalbundle `final-frozen-bundle-v20p2/` is sealed atSHA256 `496e56ca28b89a94a2bc86a3dcabd22bcfe8ed09b6f82355a497ac959473f44f`. It binds43policy/checkpoint/protocol/provenance/launchfiles plus two40-file source snapshots, before any reserved factory execution. Two prior unused bundle versions retain provenance-only packaging corrections; no final outcomes were available. Current physical core identityd98b8624…, legacydispatchgroupe96a2cd9…; engine/spec/checker/blueprint identical. Final protocolfile8093da40…; embeddedprotocolpayloadbb8e159b… are distinct hashes.

All10contracts freeze successfully ON Axion before launch. Jobs6117508–6117517 evaluate cheap24groups, quantumdet6groups, stochastic9groups×three freshactors, legacy7methods×3contexts, frontier9groups and fiveMPCcontexts. Everygroup uses the same256tapes (32perexogenousleaf, trueleafprobabilityweights); no protocolsharding. Dependencies cap at192CPUcores;0GPU/QPU. SelectedcheapIDs12static-grid-12,16cem6-2026-16,24cem6-2026-24 and frontier map are immutable. All policies/hyperparameters are closed to final-outcome tuning; remaining work is verification, statistics, offlineproofs, packaging and visualization.

##17October2026,01:23UTC — all final cohorts complete

All ten jobs6117508–6117517 completed:74groups,23,552valid rows, zeroinvalid,41declared paired comparisons. `final-complete-report/` replaces partial exports for current results; originals preserved. Independent complete-audit seal covers592original retained physical/identity/terminal/metric/telemetry replays, all-row fresh numerical anchors and unchanged globalpolicy/source seals. Finalcost70.41778allocatedCPUh,68.58411literalepisodeCPUh; these are included in overallresearch allocation, not added again.

MPC16−selectedCEM missing−.38922,exploratory95%[−.56797,−.21625];MPC24−selectedCEM+1.24672,[1.06828,1.42094]. Both predeclared quantum97.5%primary intervals includezero. No newselectedpolicy or reopenedfinal test. TRAIN-only neighborhood6117537completed at25m11s with12184grid+24witnessruns,13.43allocatedCPUh,0GPU; independent checks pending. Exactreference6117555is onefresh16CPU/2h boundedsearch on unchangedmodel/instance, checked1567warmstart/fixedseed2027; noserializedproof continuation or flagship claim. See `STAGE2_RESULTS.md` for current conclusions.


### Stage2 technical research closeout — 2026-10-17 03:29:54 UTC

All tracked research cluster jobs are finished; the requested monitoring and handoff window remains active. The immutable 03:16 ledger records 431.9967 allocated CPU-hours including failed jobs, zero recorded GPU-hours and zero physical-QPU/VeloxQ calls. Final evaluation used 70.4178 allocated CPU-hours within that total. Local setup, audits and agent inference are not a complete host-wide meter. ODRA/VPN troubleshooting remains stopped under the user hold. No autoresearch, Stage2 commit, push, deployment or submission was performed.

The unchanged final benchmark has 74 groups, 23,552 valid executions and 41 contrasts. Independent audits freshly check 592 original retained traces and rebuild every row's numerical anchor. Preselected classical fulfillment is 94.9844% at 12 initial orders/96 hours and 91.0156% at 32 initial orders/240 hours, with substantial lateness in the latter. This is the tested-controller frontier; failures at 16/24 do not prove physical infeasibility. MPC improves 16 but worsens 24 against the selected CEM. Useful adaptive-RL and quantum advantage remain unestablished. Actual QAOA uses at most five total bits, including slack, in restricted local decisions with recorded classical fallback.

Exact reference job 6117555 reports FEASIBLE 1541 and CP lower bound 1524 on the identical four-pump fixture: interval [1524,1541]. Raw CP/hint identity rejections for reservations before pump birth remain preserved. A separate derived witness changes only move74.start from 1382 to 1420, preserving physical actions, timings and recomputed metrics; both unchanged general checkers pass. Six mutation/scope tests and a second independent review pass. Auditing and normalization run no new factory or solver, change no frozen checker and add no final sample. Evidence: final-independent-audit/reference-2h-6117555/ and reference-2h-methodology-review/. This does not bound the rich stochastic factory's global gap.

Portable v2 is 10,097,277 bytes, SHA 8a54050496537a794e17bdf73c7d47ed323798f0ae7e67e8152f6d49e3c0aaa1. Its 2,436 indexed files, 24 predeclared replays and 29 separate supplements verify in 10.84 seconds in isolated Python 3.14.6 with only NumPy 2.5.4 and pip installed. Supplemental records are hashed; their entire analyses are not rerun by this compact verifier. Portable v1 and the full 116.8 MB v2 archive remain byte-stable; the full archive independently reproduces all 41 contrasts and 592 retained replays. Read docs/STAGE2_RESULTS.md and output/stage2-search/stage2-portable-final-v2-closeout-receipt.json.

The local 4187 research view shows the final frontier, TRAIN neighborhood, conditional leaves, posthoc proof and current reference interval with qualifications. Frozen final-export SHA 6a66d36b2ea032b773a2b550d8773c13a0c4ea3f1fab0ef3565894853746fd60 remains unchanged. GitHub rechecked at 03:26 UTC is still private: the public-MIT requirement is unmet; completed video, team and form receipt remain unverified. Preserve the other chat's Stage1/root presentation changes and the publication hold.


Stage2 authorized eight-hour research window completed at 2026-10-17T04:14:35.500900+00:00. Technical evidence and local handoff are complete; all tracked research jobs are finished. See output/stage2-search/research-closeout.json and docs/STAGE2_RESULTS.md. Publication hold remains; repository private at the04:11UTC live recheck, with video/team/form receipt unverified. No further experiments or policy changes are scheduled.
