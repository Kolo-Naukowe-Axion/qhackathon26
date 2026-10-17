# Advanced dispatch audit and routing candidates

All results below are development evidence on seeds 20–23, not a held-out evaluation. Every policy used the same full physical instance for each configuration and seed. The experiments change dispatch algorithms only; machine, worker, tool, energy, quality, uncertainty and routing rules are unchanged. Full 24-order global optimality gap remains unknown. A valid partial trace is not a completely fulfilled production plan.

## Implemented algorithm changes

`stage2.advanced.AdvancedFactory` retains the independently checked calendar-gap and early empty-AGV dispatch policy. Calendar-aware process offers now declare `worker_calendar_aware=True`; the shared-worker selector can combine disjoint attendance intervals while still rejecting overlaps. The baseline remains conservative.

The new options are **off by default**:

- `routing_free_buffers=True` ranks only eligible next-process stations with unreserved input space. It can select a second-ranked station instead of repeatedly requesting an already-full nominal favorite. If every eligible buffer is full, it waits. Destination reservations and all transport checks remain in the physical engine.
- `routing_estimate_finish=True` ranks stations using the actual certified processing duration, setup, observed busy/outage state, input queue estimate, available tool location/busy time, AGV approach and known worker calendar. This is an approximate ranking, not an exact scheduling subproblem: traffic, tool life, energy and simultaneous crew feasibility are still enforced at commit. It may be combined with free-buffer filtering or used alone.
- `bom_priority="join"` subtracts `bom_join_weight` (default 24) per accepted peer and `bom_progress_weight` (default 4) times peer recipe progress from the existing priority. Lower scores dispatch first.
- `bom_priority="critical"` additionally subtracts `bom_tail_weight` (default 0.5) times the candidate component’s remaining manufacturing ticks divided by the instance time scale. Committed processing uses its observed end time; repairs and replacements use their own remaining routes.
- `bom_priority="slack"` additionally subtracts `bom_slack_weight` (default 1) times the order’s optimistic critical tail, including the remaining pump assembly and final inspection. The existing due-date term remains in the score.

The BOM estimates read public parts and committed operations only. They never read future defect draws or unrevealed shock outcomes. Certified modes include standard T/F and precision QA for precision orders even under a turbo policy. The approach does not presume that arbitrary pretrained scheduling weights transfer to this factory.

## Correctness and reproducibility

The earlier audit fixed a real prepositioning bug: `charge(a)` could accidentally dispatch a different AGV and skip charging the intended low-SOC vehicle. Future part dispatch now uses that specific vehicle. Temporary part/fleet overrides restore state on failure or exceptions. Additional fixes preserve worker role metadata when one worker fills separate setup and process intervals, and retain baseline observation semantics when calendar filling is disabled.

The current focused suite contains 22 tests, covering default compatibility, full-buffer alternatives, machine-speed and worker-calendar estimates, BOM genealogy/repair/precision estimates, disjoint-worker selection, early-dispatch QA exclusion, charging and exception regressions, full replay validation and paired reveal-prefix checks. Checker and exact-reference tests are separate.

The two new batches executed 192 complete simulator runs in approximately 113.6 seconds wall time with four local CPU processes. The second batch repeats some first-batch policies, so these are not 192 independent stochastic samples. **All 192 traces passed the independent physical checker and every four-seed policy group passed the paired prefix audit.** The empirical prefix audit is not a general proof of policy nonanticipativity. Source hashes before and after each batch matched, including engine, specification, independent checker, dispatcher and advanced policy. No GPU or quantum hardware was used.

Reports, full compressed traces, configurations, per-run objectives, source snapshots, hashes and replay/prefix issues are retained in:

- `output/stage2-search/advanced-candidates-audit/report.json` (84 runs; first candidates).
- `output/stage2-search/advanced-soft-audit/report.json` (108 runs; softer BOM and separate ETA/calendar/preposition ablations).

Audited advanced-policy SHA256: `01d827bacbc77c7492f7d9a860afd23376df62d0aa99f12c9bf98153f270f555`. The saved `audit_script.py` in each directory reproduces its corresponding run. Timestamps in traces vary; physical actions and reported objectives are deterministic for the fixed source, configuration and seed.

## Results and negative evidence

Each cell is the **sum shipped over four fixed development seeds**, including urgent orders actually revealed. Seeds 20–22 reveal two urgent orders each; seed 23 reveals none. Denominators are 102 for 24 initial orders and 54 for 12 initial orders. These are three different configurations, not evidence that one policy is universally superior.

| Policy | 24 standard, WIP2, lease, priority | 24 turbo, WIP4, lease, priority | 12 eco, WIP3, no lease, greedy |
|---|---:|---:|---:|
| baseline | 43 | 45 | 36 |
| advanced | 42 | 48 | 36 |
| free | 44 | 43 | 36 |
| eta | 47 | 47 | 36 |
| join | 38 | 46 | 37 |
| critical | 43 | 46 | 35 |
| slack | 44 | 44 | 34 |

Here `advanced` is calendar filling plus 10-minute early empty dispatch; `free` adds free-buffer filtering; `eta` also adds the finish-time ranking. The first-batch BOM variants add free-buffer filtering to `advanced`. Strong BOM bonuses frequently hurt; they remain opt-in and are not presented as a successful universal improvement.

The second batch changes individual features and softens the priority weights:

| Policy | 24 standard/WIP2 | 24 turbo/WIP4 | 12 eco/WIP3 |
|---|---:|---:|---:|
| eta_existing | 47 | 47 | 36 |
| eta_no_pre | 45 | 45 | 38 |
| eta_no_cal | 47 | 47 | 36 |
| eta_no_both | 45 | 43 | 38 |
| soft_join | 41 | 46 | 38 |
| tail | 41 | 43 | 36 |
| slack | 39 | 42 | 30 |
| eta_soft_join | 44 | 47 | 39 |
| eta_tail | 43 | 40 | 37 |

All second-batch variants enable free-buffer filtering. `eta_existing` repeats the first-batch ETA policy. `eta_no_pre`, `eta_no_cal` and `eta_no_both` disable early dispatch, calendar filling or both. `soft_join` uses accepted-peer weight 4 and peer-progress weight 0. `tail` uses accepted/progress weights 0 and manufacturing-tail weight 2. `slack` uses accepted/progress/tail weights 0 and order critical-tail weight 2. The last two policies combine ETA with the stated softer BOM rule.

The standard/WIP2 ETA candidate raises shipments from 43/102 (baseline) to 47/102 and reduces total tardiness from 144273 to 141846 minutes on these development seeds. It raises total cost because it performs more production; this is not an energy-efficiency claim. The existing advanced policy remains stronger on turbo/WIP4 throughput (48/102 versus ETA 47/102). On eco/WIP3, ETA plus the softer join bonus produces 39/54 versus baseline 36/54, while a strong slack bonus collapses to 30/54. These candidates require a fresh, frozen held-out comparison before making a general performance claim.

## Congestion observations

In one 24-order/turbo/WIP4 seed20 advanced trace, 12 orders ship. QA processing occupies 2772 total machine minutes; worker W04 contributes only 406 QA attendance minutes despite roughly 1680 available shift minutes over the horizon. Mill1 moves 32 times versus mill2 only 3; calibration kits move 8 and 7 times. Cumulative output waits are largest at heat stations H2 (432 minutes), H1 (280) and T1 (270), while completed QA output waits are small. This suggests that crew/tool placement and release/batching decisions merit attention alongside nominal machine utilization. These single-trace observations are diagnostics, not proven bottleneck bounds.

An earlier instrumented trace recorded 1448 repeated attempts to select a full nominal buffer while another eligible station had input space; repeated calls are counted, not distinct blocked parts. Free-buffer routing addresses that mechanism, but its regressions show that routing to any available alternative can worsen downstream crew/tool/transport congestion.

An irrecoverable order could theoretically retain a CONWIP slot because the baseline releases slots only after shipment. No exhausted replacement or terminal pump-scrap event was present in the inspected low-throughput examples, so that hypothesis does not explain the observed regressions.
