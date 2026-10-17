# Method selection: development evidence and rejected directions

The strongest inexpensive learned controller in these experiments is the selected six-action CEM **time schedule**. The richer PPO networks and18-action domain do not establish a stronger state-adaptive controller. Strong static tuning closes much of the apparent learned-policy gain. Scenario MPC can improve deadline debt at substantial inference cost. The actual learned-schedule/QAOA integration works physically but regresses on fulfillment and is unselected. The main sections record TRAIN and explicitly reused-validation evidence. A separately labeled post-final diagnostic appears at the end; it does not change selection or establish global optimality.

## What each method can actually choose

All recent comparisons use the full96-hour minute-grid factory, including physical crew/tool attendance, transport, finite buffers, maintenance, wear, quality, legal repair/replacement, urgency, energy and calendar constraints. The physical core remains frozen. Tool homes, kit reservations, physical repacking, admission rankings, routing and the maintenance guard are disclosed scheduling choices; different algorithmic restrictions are not silently treated as the same candidate domain.

| Method | Decision domain | Interpretation and restriction |
|---|---|---|
|Strong static factorial|WIP4/6/8 ×QA protection0/4 ×T/F eco/standard/turbo ×QA ETA routing off/on ×completion credit0/270; n24 also quarter join|288 fixed policies across n12/n16/n24; guard on, reclaim off, priority decoder. Fixed per-context physical backend choices retained.|
|Six-action PPO|Public32-feature state; WIP4/6/8 ×QA protection0/4 every720minutes|Actual PPO training, but selected policies often reproduce a constant controller exactly.|
|Six-action CEM|The same six actions in eight720-minute segments|Learned open-loop time schedule, not state-adaptive RL. Static fallback remains eligible.|
|Eighteen-action PPO/CEM|Adds T/F eco/standard/turbo to the six actions|A larger action space and a neural network are not evidence of a better solution. Guard and identity checks are built into this separate fit.|
|Scenario MPC|Six WIP/QA actions, planning every1440minutes, two/four independently resampled futures|Classical simulator lookahead with shared candidate futures; actual hidden tape replaced before continuation. No global search or quantum claim.|
|Corrected local QUBO|One frozen offered operation/crew assignment per candidate, explicit conflicts and power capacities|Exact means optimal only for the current local linear reward/domain. Sequential priority can still find a better physical continuation.|
|CEM6 + local QAOA hybrid|The frozen selected CEM6 schedule plus corrected no-batch local selection, guard on|Actual integration, unchanged candidate construction. Actor seeds are independent of environmental tapes. Later realized pools can diverge after different actions.|

The original six-action and MPC studies are separately frozen. Guarded replay reproduces all144 selected six-action validation trajectories exactly; six guarded-MPC development replays reproduce their original metrics. This is evidence for those executions, not a claim that all720 original MPC cases already ran the new guard. A prior mode screen retained four physically invalid maintenance/outage overlaps; those rows remain invalid and are not candidate winners.

## Strong controls change the comparison

The declared static grid completed9216/9216 independently checked TRAIN episodes:32 common environmental tapes per policy. No16-tape fallback was needed. Reused validation then measured192/192 valid episodes. Before validation, the third-candidate rule was prospectively clarified to global TRAIN top2 + the matched18-action TRAIN winner + the original guarded prior, deduplicated to at most four policies/context. Original plans, all policy ranks and source manifests remain retained. This is not an enlarged validation search.

The table gives **summed missing orders across16 reused VAL100–115 tapes**, containing210/274/402 realized demands at n12/n16/n24. Selection repeatedly uses these tapes; these are development comparisons, not unbiased final estimates.

| Selected/control method |n12 missing|n16 missing|n24 missing|
|---|---:|---:|---:|
|Original guarded strong static prior|2|59|188|
|TRAIN-selected matched18-action static|2|44|190|
|Broader TRAIN-grid/reused-VAL static winner|0|35|168|
|Six-action PPO2026|0|44|188|
|Six-action PPO2027|0|50|188|
|Six-action CEM2026|0|31|164|
|Eighteen-action PPO2026|0|44|180|
|Eighteen-action CEM2026|2|40|172|
|Scenario MPC, two futures|0|33|180|
|Scenario MPC, four futures|0|35|175|

The matched static row is the winner **selected on TRAIN**, not the retrospectively best of every fixed action on VAL. In particular, the already measured constant standard/WIP6/guard4 also has zero n12 missing; the matched TRAIN winner happens to be turbo/WIP6/guard4 and misses two on VAL. PPO's apparent n12/n16 benefit over the older WIP4 prior must not be credited as dynamic intelligence: physical trace comparisons reproduce its selected behavior with constant standard/WIP6/guard4. Some nominal PPO switches occur too late to alter any downstream physical event.

The broader static winners are n12 standard/WIP8/guard4 +QA routing +credit270; n16 eco/WIP6/guard4 +QA routing, credit off; and n24 standard/WIP6/guard4 +QA routing +credit270 +quarter join, kit reservations off. Their missing totals0/35/168 are stronger full-portfolio controls. CEM6's31/164 misses at n16/n24 therefore improve by four orders each on this reused selection cohort, rather than by the much larger gap to the old WIP4 priors. At n12, broader static debt47641 is lower than CEM's48840 with equal fulfillment. Four-future MPC debt45680 is lower again, at substantial inference expense.

MPC comparisons retain their original contexts and finite policy bank. More futures are not monotonically better: n16 two-future missing33 beats four-future35; n13 both planning variants miss three orders where their static control misses none. One sampled future had already regressed in an earlier, weaker-backend experiment. Planning is an evaluated option, not a default theorem of improvement.

## The actual learned-plus-quantum test is negative

The corrected hybrid pilot ran264 checked TRAIN episodes on eight common tapes/context: priority/exact at actor7 and SA/QAOA/uniform at actors7/13/29. All264 pass anchored physics, the independent identity supplement, source checks and selected/committed equality. All33 first-tape traces and every raw row are retained. Actors are nested within environments; three actors do not triple the number of independent environmental tapes.

| Hybrid local selector |n12 mean missing|n16 mean missing|n24 mean missing|
|---|---:|---:|---:|
|Priority|0|2.625|9.500|
|Exact no-batch|0.250|2.875|9.750|
|SA, three-actor mean|0.042|2.792|10.000|
|QAOA, three-actor mean|0.042|3.125|10.708|
|Equal-shot uniform, three-actor mean|0|2.917|11.042|

QAOA is worse than priority on primary fulfillment in all three contexts and does not consistently beat uniform/SA. Choosing only its best actor would conceal this variability. The integration is unselected and stops without validation or a final adapter. Its telemetry contains53779 local calls,14126 actual simulated QAOA calls,6875 coupled QAOA calls and7150 trivial one-bit QAOA calls;3883 fallback calls occur across methods. There are zero repairs, decoder mismatches or physical-QPU calls. The largest encoded pool has25 total bits; the largest actually simulated circuit has five. Larger local pools use disclosed classical fallback, so their encoded size must not be labeled a quantum execution.

The first frozen hybrid submission omitted the flow-metric module and retained264 invalid worker rows before simulation. That packaging failure is preserved as6117500. The dependency-complete v19p1 rerun6117503 adds an actual frozen-worker smoke and retains the successful264 separately; failed rows are not silently relabeled valid.

## Substantive negatives and reversals

- Local reward design mattered more than solver branding. The old extra-batch bonus made exact dispatch sacrifice higher-value work; correcting it rescues n12 exact TRAIN fulfillment326/424→422/424. A one-tick offline continuation audit demonstrates surrogate regret without claiming a global oracle. Corrections can regress n16, so they are not universally promoted.
- Expanding crew alternatives correctly enlarges a local domain, but does not fix a myopic objective. Its unselected regressions remain visible. Full-factory optimality is not certified by exact local QUBOs.
- Completion credit initially gains two n16 shipments on TRAIN0–7, then reverses449→446 across TRAIN32. It is rejected in that fixed n16 context. At n24, quarter-join credit improves440→454/808; interactions with WIP/routing are then tested in the declared factorial rather than assumed additive.
- Observed-dead scheduling-slot reclaim leaves the main100-run physical results unchanged. A diagnosed binding slot is real but still adds no shipment; late remaining physical route duration can exceed the horizon. Reclaim is unselected and does not erase failed orders or good inventory.
- Release-aware family admission fills visible early scheduling gaps but severely harms setup economy. All128 paired TRAIN runs are valid; n12 shipments422→406 and n16 matched465→387, with zero shipment wins in either context. Setup minutes rise37%/92%. The direction stops without validation.
- Slower careful assembly/welding can reduce per-step risk while consuming more scarce attended time and wear. Later stronger-backend selective/all-careful tests fail to improve primary fulfillment; they remain negative rather than an assumed quality cure.
- Hard tool homes and legal physical kit repacking produce larger useful gains than decorative neural or quantum components. They remain disclosed heuristics with retained counterexamples, not universal deadlock prevention or proof that every stochastic tape is solvable.

## Actual compute and evidence scope

All workloads below use CPUs; no H100 use is implied. Allocated CPU-seconds and actually consumed CPU-seconds are different quantities. Do not sum Slurm allocation rows together with their `.batch`/`.extern` records.

| Experiment | Actual budget/evaluation cost |
|---|---|
|Strong static TRAIN grid6117473|Two32-CPU parts,540s/1303s allocation elapsed;58976 allocated CPU-s,48616 consumed CPU-s;9216 episodes.|
|Static reused validation6117486|26s/21s allocation elapsed on32CPUs;1504 allocated CPU-s,874.608 consumed CPU-s;192 episodes.|
|Six-action PPO2026/2027/CEM2026|Actual fit wall1200.165/1205.536/1216.086s,32 workers each; worker rollout CPU28682.036/29317.276/31627.777s. Teacher/prior and replay costs are additional.|
|Eighteen-action PPO/CEM|Actual fit wall600.505/602.931s; worker CPU13790.681/15372.884s, plus parent CPU and post-fit replay.|
|Strong MPC720-case confirmation|2429s allocation elapsed×32CPUs. At n12 planning wall averages75.55s/tape with two futures and156.39s with four; n24 averages125.24/248.11s.|
|Rejected release-aware admission6117495|17s×32CPUs;544 allocated CPU-s,467.643 consumed CPU-s;128 episodes.|
|Rejected hybrid6117503|34.56s driver wall;36s×32CPUs allocation,1152 allocated CPU-s,1006.514 consumed CPU-s. Prior packaging failure adds32 allocated/3.300 consumed CPU-s.|

The hybrid's CEM checkpoint is not free pretraining: it retains9096 fit and720 reused-validation rollouts, its1216.086-second fit, source hashes and shared-prior cost references. These campaigns are purposefully strong comparisons, not one rigorously equal-cost tournament: domains, prior-search costs and inference budgets differ. The original broad neural/static and later strong-backend experiments must also not be pooled across changing algorithmic restrictions as if they were one controlled result.

Primary retained sources are `axion-static-control-v16-submission/{train-part0,train-part1}`, `axion-static-control-validation-v16p2-submission/{validation-part0,validation-part1}`, `axion-adaptive-evidence-2349/`, `axion-adaptive-modes-2359/`, `axion-download-0001/strong-mpc-confirmation-6117307/`, `axion-release-admission-v18-submission/` and `axion-hybrid-schedule-v19p1-submission/`, all under `output/stage2-search/`. Static retention-audit JSONs carry exact weights/options, TRAIN rank, immutable report/source hashes and paired-instance equality. Hybrid `retention-analysis.json` carries every actor result and literal execution telemetry. Detailed method audits remain in the corresponding `STAGE2_*` documents. Final policy selection, execution and claims require their separately frozen protocol.


## Separately labeled post-final rare-PPO diagnostic

This appendix was added after final evaluation closed. It does not revise the
original development selection rationale, tune a policy, or add replay runs to
final estimates. Source: the retained [posthoc report](../../../output/stage2-search/final-independent-audit/postfreeze-rare-ppo-10062/report.json)
and its [declaration](../../../output/stage2-search/final-independent-audit/postfreeze-rare-ppo-10062/declaration.json).

For the frozen n16 PPO6-2026 and matched static18 control at actor900000, missing
orders agree on all256 original final tapes. The declared posthoc diagnostic
chooses the first ascending seed with differing full metrics:10062, the only
such seed under the recorded tolerance. This is an outcome-selected illustration,
not one of the predeclared eight visual/activity tapes or an independent extra
sample. Both unchanged-policy witness replays pass the anchored checker and
identity supplement, reproduce their original metrics, and preserve final
source hashes; exactly two factory replays are recorded.

On that tape PPO changes from action3 (standard/WIP6/QA guard4) to action1
(standard/WIP4/guard4) at tick3600, returning to action3 at4320. The first actual
physical divergence from the constant static controller is a transport at3723.
Thus this policy is not literally constant on every possible execution, even
though earlier development traces often coincide exactly with static control.
Both methods ship9 of18 demands here; PPO's deadline debt24550 exceeds static's
24496, and its total cost757.50048 exceeds733.97194. A real rare state-dependent
change therefore exists without a demonstrated primary benefit; it worsens these
secondary outcomes on this deliberately selected tape. Matching full metrics on
the other255 tapes does not itself prove complete physical trace identity.
