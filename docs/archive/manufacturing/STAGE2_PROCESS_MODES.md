# Careful welding and assembly: bounded TRAIN ablation

Careful modes mostly reduce throughput in this screen. Assembly-only at n24 is a small conditional lead; it has not earned promotion into the selected n12 policy. All96 retained TRAIN runs pass independent physical replay, terminal reserve and empirical paired-prefix causality. No validation or final tape was used.

`stage2/process_modes.py` adds `ProcessModesMixin` above the frozen admission + kit reservation + hard portable homes + QA specialist + calendar factory. The standard default reproduces its physical traces and metrics exactly. `process_modes={'S':'careful'}`, `{'ASSEMBLY':'careful'}` or both substitute only ordinary standard-mode requests. The substitution runs before parent preview, tool preparation and commit. ETA mode selection uses the same choice; repair ETA context is restored even on exceptions. Rework requests retain their original modes; repair assembly remains standard. Certified QA and the precision-order T/F turbo guard remain unchanged.

The existing physical tables, not new assumptions, define the tradeoff:

| Process | Standard manufacturing step risk | Careful step risk | Processing time | Processing power |
|---|---:|---:|---:|---:|
| Welding S |.04|.015|×1.5|10→8 kW|
| Assembly |.025|.01|×1.5|4→3.2 kW|

These probabilities are the authoritative `quality.manufacturing_defect_probabilities`, before the existing wear contribution and compounded history. The legacy mode descriptive defect field is not used as an alternative risk model. Careful processing also consumes50% more fully attended crew time and wear, and welding consumes50% more tool life per job. Setup duration remains unchanged; the engine applies selected power across the whole operation. Repair residual risk stays.02.

## Complete paired screen

Seeds0–7 were run in each load/mode combination, with two local workers. The96 runs took106.24 wall seconds. The TRAIN routing teacher supplies the exact prior for each load; hard homes, kit reservation, family admission, calendar filling and no prepositioning are common. Contexts are n12/WIP8/QAguard4, n16/WIP4/guard0 and n24/WIP4/guard4. The source SHA256 values before and after match. The new module is frozen at `b79c94eb63f0ddadb674b6c0bed8ea8c2d25aa212a6704e4c90deff130e5836b`.

| Initial orders | Careful choices | Shipped/demand | Complete tapes/8 | Deadline debt, min | Failed QA/inspections |
|---:|---|---:|---:|---:|---:|
|12|neither|108/108|8|27460|29/461|
|12|welding|96/108|6|61183|23/418|
|12|assembly|105/108|6|37707|26/455|
|12|both|93/108|4|69053|21/413|
|16|neither|110/140|0|125169|33/493|
|16|welding|103/140|0|126756|28/474|
|16|assembly|103/140|0|134431|29/473|
|16|both|100/140|0|136339|28/465|
|24|neither|109/204|0|265463|35/519|
|24|welding|109/204|0|269332|32/516|
|24|assembly|113/204|0|262300|35/520|
|24|both|103/204|0|270054|33/497|

Demand includes the revealed urgent orders. Deadline debt is the existing engine metric `total_tardiness_ticks`: actual delivery lateness for shipped orders plus horizon-censored lateness for unshipped orders. It equals the independent checker's `terminal_deadline_debt_ticks`; the checker's separately named `tardiness_ticks` covers delivered orders only. Fewer failed inspections may partly reflect reduced completed work. Even inspection fractions compare different reached jobs and wear histories, so this table does not isolate a causal quality benefit.

For n24 assembly-only, five paired seeds improve shipments and three regress, for net+4. Its QA failure count remains35, despite slightly more inspected work. The small gain could arise from interacting schedules, power and quality; it is not evidence that assembly quality alone caused improvement. n12 welding on seed4 is a severe retained regression:12→1 shipments, with production stalled after tick2537 and the last tool service ending2597. The kit restriction prevents its declared partial-kit fragmentation pattern; it is not a proof against every congestion deadlock.

Aggregate energy costs, processing minutes, repairs, scraps, replacements and every per-seed delta are retained in `output/stage2-search/process-modes-train8/summary.json`. `report.json` records every run, exact weights, source hashes, trace hashes, validity and causal audits. `n12-s4-welding.json.gz` preserves the severe regression, alongside every other compressed raw trace. The8-tape screen supports keeping standard for n12/n16 and retaining n24 assembly-only for a separate validation decision; no further experiment or selection is implied here.

Seven tests cover exact default equivalence, preview/preparation/commit duration and power consistency, actual tool-life usage, repair context restoration, unchanged certification, malformed options, and independently checked paired tapes for all four variants. Run `python -m unittest discover -s tests/stage2 -p test_process_modes.py -v`. Reproduce the screen with `python -m stage2.process_modes --workers 2 --output OUTPUT_DIR`; the CLI prohibits final seed IDs10000+ and more than two workers.
