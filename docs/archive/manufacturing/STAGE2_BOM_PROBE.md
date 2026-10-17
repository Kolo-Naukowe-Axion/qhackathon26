# BOM-aware priorities on the strong recovery backend

`stage2/bom_probe.py` is an experimental driver and explicit composition of existing recovery, hard portable-tool homes, optional whole-kit reservation, family admission and process-scoped routing. It does not modify physical sources or add a new priority rule. It evaluates the existing `AdvancedFactory` join/critical/slack rules on the stronger backend because earlier negative BOM experiments used weaker policies.

All three rules subtract a bonus for accepted peer components and peer recipe progress. Critical additionally subtracts the candidate's public optimistic remaining manufacturing time; slack also subtracts the whole order's public optimistic critical tail, including assembly/final QA. Lower scores dispatch first. These estimates include known committed operation ends and currently revealed repairs/replacements, but omit future quality outcomes, queueing, traffic and future resource contention. They are heuristics, not feasibility certificates or learned value functions.

The bounded protocol is192 paired TRAIN episodes: n16/n24, seeds0–7. Both use the previously declared strong WIP4/family-admission/QA-guard4/standard-machining controls, leased calibration kit and hard tool homes. Whole-kit reservation is on for n16 and off for n24, matching the existing strong-selector cohort. Main routing-off comparisons include unchanged priority, join/critical/slack at quarter/default coefficients, and corrected exact-no-batch as a separate control. A smaller QA-only finish-time-routing comparison includes unchanged priority and the three quarter-scale rules. There is no hidden full extra coefficient grid.

Default coefficients are accepted-peer24, peer-progress4, component-tail0.5 and order-tail1; quarter-scale divides all four by4. Only coefficients used by the named rule affect it. On the minute-grid instance with time scale15 and due weight1, an accepted-peer bonus24 is equivalent to6hours of due-date priority, while quarter-scale6 is90minutes. Thus the full/default join pressure is deliberately substantial. All candidate constraints remain enforced, and every episode is independently checked. Static/selector controls and all invalid outcomes are retained.

The post-run flow audit records machine occupied minutes and worker attendance by process, accepted-component waiting until actual parent consumption or horizon censoring, accepted components stranded at horizon, delay from prior manufacturing completion to QA start, delay from complete accepted kit to initial assembly, irreversible final-pump scraps, and full terminal process inventories. Pre-QA delay includes transport, station queueing and calendars; it is not solely a QA queue metric. Fewer inspections or less waiting can arise from reduced production and must be interpreted alongside shipments. No post-run metric enters the policy.

Sources, predeclared tasks and every raw result are retained in `output/stage2-search/bom-strong-recovery-training/`; the first declared tape for every policy retains a full compressed trace, and invalid traces are always retained. The driver refuses output overwrite, source drift, and seeds outside TRAIN0–31. It never executes validation or final tapes. Tests cover strong-control equivalence, bounded coefficient domains, actual independent checks and paired causality for all three rules, score response to publicly observed acceptance, and an independent flow-accounting fixture that includes stranded components.

Run `python -m stage2.bom_probe --output <new-directory> --workers 2` for the declared first-stage probe, or provide an explicit TRAIN task file with `--tasks`. Wider TRAIN confirmation should follow only an interpretable improvement over this strong control. Negative results remain part of the record and should lead to a substantial scheduling change rather than an open-ended coefficient search.

## Completed first-stage results

All192 episodes passed the independent checker and selected/committed checks. Sources stayed fixed; two-worker wall time280.08s and summed process CPU time555.22s. These are eight paired TRAIN tapes per policy, not held-out success rates. None of the n16/n24 groups fulfills every order on a complete tape, so the improvements concern throughput within96hours.

| Load | Policy | Shipped/required | Total tardiness ticks |
|---|---|---:|---:|
|16|No-BOM control, routing off|109/140|119212|
|16|No-BOM control, QA routing|114/140|111673|
|16|Quarter join, QA routing|114/140|114865|
|16|Quarter slack, routing off|110/140|117269|
|16|Corrected exact-no-batch, routing off|113/140|114180|
|24|No-BOM control, routing off|109/204|265463|
|24|Quarter join, routing off|116/204|257833|
|24|Default join, routing off|110/204|261245|
|24|Default critical, routing off|115/204|260868|
|24|Quarter slack, routing off|114/204|255804|
|24|No-BOM control, QA routing|116/204|264106|
|24|Quarter join, QA routing|109/204|261450|
|24|Corrected exact-no-batch, routing off|110/204|267369|

For n24, quarter join improves six tapes, loses one and ties one against its routing-off control. The worst regression is two shipments and the best gain three. Accepted components stranded at horizon fall23→9, total accepted-component waiting falls91143→71800minutes, and initial assembly starts rise117→125. QA machine occupied minutes rise26938→27673 across the eight runs, while pre-QA completion-to-start delay falls130258→127010minutes. This supports a kit-feeding explanation: more inspected inventory reaches complete assemblies, rather than merely accumulating partial kits. Ready-kit-to-assembly wait rises5273→6727minutes, so every intermediate delay does not improve. Descriptors are censored and production volume differs; they are not pure utilization or efficiency estimates.

QA routing without BOM also improves n24 to116shipments and leaves nine accepted components stranded, but combining routing and quarter join loses that gain. Keep the two hypotheses separate. For n16, the strongest tested effect is QA routing itself, and no BOM variant improves on its114shipments plus lower tardiness. Higher critical/slack weights frequently regress; all24 policy-group summaries and individual rows remain retained.

The prepared192-episode follow-up `output/stage2-search/bom-strong-recovery-paired-train32-tasks.json` compares n16 no-BOM routing off/on, and n24 routing off/on, quarter-join/routing-off, and corrected exact-no-batch/routing-off. All use TRAIN0–31. Seeds0–7 selected these candidates;8–31 are new to this specific probe. This is still TRAIN confirmation, not validation or final evidence. No further coefficient grid is proposed.

Remaining limitations suggest an order-level completion policy if confirmation fails: the existing BOM cache drops consumed parents, so a newly assembled pump loses accepted-peer join pressure, and the baseline negative remaining-step coefficient favors longer unfinished routes. Propagating known kit investment through pump genealogy and the value of releasing a CONWIP slot would be a substantial causal scheduling change. It requires a separate explicit policy and matched controls; this driver has not implemented or claimed that improvement. Aggregate QA staffing also remains uneven across shifts, so unused early-shift attendance is not a proof of globally available capacity.
