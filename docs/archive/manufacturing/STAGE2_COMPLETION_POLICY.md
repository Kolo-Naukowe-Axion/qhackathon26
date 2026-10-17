# Lineage completion credit and observed-dead scheduling slots

`stage2/completion_policy.py` adds two independent optional controls over frozen recovery/scoped routing. Both are off by default. Every order and physical part remains in the model and unfulfilled-demand/tardiness objective. Machine time, staffing, transport, buffers, inspection draws, repair/replacement opportunities and good inventory remain unchanged.

## Check the mechanism before claiming a benefit

The retained n12/seed15 trajectory permanently scraps original pump P11 at tick5370. At that time only P11/U01/U02 remain admitted, occupying3/8 slots; all revealed orders were already admitted by3205. Its unused slot is not an admission bottleneck. An actual checked regression test proves reclaim leaves every physical operation, move, energy row, event and metric identical on this trajectory while retaining the14-order objective and unfinished debt. The earlier n16/n24 control tapes0–7 contain no permanently scrapped final pumps; n24's retained seed0 traces across all12 BOM/routing policies also contain no pump or exhausted-replacement scrap. Thus the initial slot hypothesis is a code possibility, not an established explanation of these failures. Evidence is retained as `completion-value-training/preimplementation-slot-evidence.json`.

## Completion credit

The policy identifies each live final pump through the actual initial ASSEMBLY operation's three parent IDs. All three distinct housing/rotor/flange parents must belong to the order and remain physically consumed. It propagates their known completed investment onto the pump through final QA, observed repair, and accepted-pump shipping. Unassembled components, fake/uncommitted pump records, scrapped/disposed/shipped pumps receive no credit. No quality uniform, seed-specific order key or unrevealed outcome enters the rule.

The tested moderate credit is a270physical-minute virtual advance of the existing due priority: `due_weight * 270 / (tick_minutes * time_scale)`. This corresponds to three consumed components at the earlier moderate90minute accepted-peer scale. It therefore has the same4.5hour interpretation across contexts with different due coefficients. On the n12 due-weight0.25 context it subtracts4.5 priority units; on n16/n24 due-weight1 it subtracts18. It is a heuristic value for completing an order/freeing a scheduling slot, not an added physical deadline or optimal value estimate. It may starve upstream work or accelerate a pump whose later inspection fails; all regressions remain in the experiment.

## Observed-dead reclaim

A scheduling slot can be reclaimed only after a public final-pump scrap, or after an original component and its sole legal replacement are both scrapped/disposed with no live/unreleased alternative and no live final pump. A failed first inspection, a pending replacement, lack of current stock or an uncertain future outcome is insufficient. The frozen factory has no replacement for a final pump and permits only one component replacement. Changing those rules requires re-auditing this inference.

The adapter removes an observed-dead order only from the admitted scheduling set and excludes it from immediate readmission. It temporarily filters the admission ranking's local order view and restores the original dictionary in `finally`. Every actual order and component remains present in the factory, trace and objective. Existing good components are not scrapped or relocated; assembly-space reservations are not magically released. This may leave stranded inventory and can worsen congestion despite admitting another order. Normal in-flight moves and physical completions continue. The policy is not a deadlock guarantee.

Reclaim logs when failure becomes known, whether an admitted slot was removed, occupancy/WIP, and publicly released pending orders. A binding-slot indicator additionally requires the pre-reclaim WIP limit to be full and a released non-dead order waiting outside it. It is not enough merely to count a retired order. The admission adapter preserves deepcopy/factory references for future scenario use; no MPC composition is selected here.

## Bounded experiment

The first protocol contains100 TRAIN episodes: credit0/270minutes ×reclaim off/on, on n12 tapes0–7+diagnosed15 and n16/n24 tapes0–7. Contexts are explicit: original strong n12 control; no-BOM QA-only-routing n16 candidate; quarter-join/routing-off n24 candidate. These are development-selected strong controls; comparisons are paired within each context, and their performance is not an unbiased rate. A separately declared eight-episode seed15 extension at n16/n24 tests whether that observed failure can become WIP-binding at four slots. Its role remains diagnosed TRAIN evidence.

The driver freezes source hashes, rejects output overwrite and non-TRAIN0–31 seeds, independently checks every actual trace, and retains invalids plus the first declared tape and diagnosed15 traces. It records all debt/cost/fulfillment metrics, flow diagnostics, terminal inventories and actual credit/reclaim telemetry. Credit evaluation counts/distinct priority ticks are not committed-action or total-waiting statistics. Sources/raw results are under `output/stage2-search/completion-value-training/`; the extension tasks are `output/stage2-search/completion-value-diagnosed15-extension-tasks.json`. No validation or reserved final tapes are executed.

Eight tests cover exact default equivalence; actual consumed lineage and physical-time interpretation; safe slot reuse without order/part deletion or readmission; live-pump/pending-replacement exclusions; exception/deepcopy restoration; actual physical checks and paired causality; the real nonbinding seed15 trace; and the bounded2×2 domain. The implementation makes no global optimality or universal recoverability claim.

## Completed TRAIN results

All100 main episodes passed the full checker and selected/committed checks, with source hashes unchanged. Wall time106.80s on two workers; summed CPU211.75s. Credit/reclaim effects are paired within the same fixed context.

| Context | Credit | Shipped/required | Total tardiness ticks |
|---|---:|---:|---:|
|n12,9tapes|0min|120/122|36494|
|n12,9tapes|270min|120/122|34710|
|n16,8tapes|0min|114/140|111673|
|n16,8tapes|270min|116/140|103985|
|n24,8tapes|0min|116/204|257833|
|n24,8tapes|270min|116/204|245486|

For n16, three tapes gain one shipment, one loses one, and four tie. Stranded accepted components fall14→5. This is a candidate for broader TRAIN confirmation, not a general improvement claim. For n24, total throughput ties but order mix and upstream flow change: stranded accepted components rise9→24 and pre-QA delay127010→140021minutes. The lower deadline debt is accompanied by a real upstream-starvation regression. n12 retains the same unfulfilled orders, and some tapes' tardiness increases despite the lower aggregate.

Dead-slot reclaim has no physical/metric effect in the100-run main study. It retires P11 on n12/seed15, correctly labeled nonbinding. The separately declared eight-run n16/n24seed15 extension also passed every check, in10.89s wall time. It demonstrates a genuinely binding observed-dead slot at n16/WIP4, but reclaim still yields no extra shipment:13/18 with or without it, and one control's tardiness worsens by one tick. At n24/seed15 no dead-slot trigger occurs; completion credit improves13/26→14/26 independently of reclaim. A trigger is not a demonstrated throughput benefit, so reclaim is not promoted.

In the n16 extension, no-credit reclaim retires P11 at5002 and admits P12 with758minutes left. With completion credit, P11 scraps at5423 and reclaim admits U01 with337minutes left. U01 had no prior processing, and its optimistic initial-BOM critical duration is496minutes even using independently fastest certified legal modes/machines and ignoring every setup, crew wait, queue, transport and possible failure. Thus U01 cannot finish after that late admission. This is a bound at the observed state, not proof that a different earlier global policy could not fulfill it. The explicit computation is retained in `completion-value-diagnosed15-extension/public-critical-tail-diagnostic.json`.

## TRAIN32 confirmation and reused validation

The declared192-episode TRAIN0–31 confirmation completed as Axion job6117451 against the immutable v15-completion snapshot. Every episode passed the full checker and source checks; all50 overlapping local replicas matched their metrics exactly. Reclaim stayed off. Results are retained under `output/stage2-search/axion-completion-v15-submission/results/`, with paired analysis and Slurm accounting alongside them.

| Context | Credit0 shipped/required | Credit270 shipped/required | Credit0→270 tardiness ticks |
|---|---:|---:|---:|
|n12|422/424|422/424|110484→97888|
|n16, QA-only routing|449/552|446/552|455188→430282|
|n24, quarter join|440/808|454/808|1027346→988921|

The n16 first-eight-tape gain reverses over all32: nine tapes gain shipments, eleven lose, and twelve tie. Complete episodes fall1→0. Credit is therefore rejected for this n16 context despite lower aggregate deadline debt. For n24, fifteen tapes gain shipments, six lose, and eleven tie. Increased stranded accepted inventory and pre-QA delay remain visible; improved throughput does not imply every flow measure improves.

The separately declared reused VALIDATION100–115 overlay completed80 episodes as job6117459, with all physical/source checks passing. It compares credit0/270 at n12 and n24, retaining the n24 QA-only/no-credit control. These tapes have already been used for selection elsewhere; this is explicitly reused validation, not an unbiased final evaluation. The maintenance-outage guard is off in this earlier overlay; subsequent guarded static-control comparisons are a separate protocol.

| Reused-validation context | Shipped/required | Complete tapes | Tardiness ticks |
|---|---:|---:|---:|
|n12 credit0|208/210|15/16|47677|
|n12 credit270|209/210|15/16|41948|
|n24 quarter join, credit0|214/402|0/16|516515|
|n24 quarter join, credit270|227/402|0/16|489447|
|n24 QA-only, no credit|216/402|0/16|518550|

The n24 credit candidate raises total cost12086.709→13420.9825 while producing13 additional orders; this is not an energy-saving result. Raw rows, first-tape traces, immutable sources and submission/accounting records are under `output/stage2-search/axion-completion-validation-v15p1-submission/`. The TRAIN job used1088 allocated CPU-seconds (1014.780 consumed); validation used512 allocated CPU-seconds (468.373 consumed). Neither used GPUs. No reserved final tapes were executed. These are provisional candidates pending the stronger, declared static-control factorial; no further credit-scale search is proposed.
