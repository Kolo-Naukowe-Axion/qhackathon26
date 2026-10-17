# Stationary-battery optimization over the same factory

`stage2/energy.py` changes the stationary-battery dispatch algorithm. It retains the original generator, load, solar profile, tariff/carbon profile, grid caps, action table, losses, SOC bounds and terminal requirement. `EnergyFactory` combines the mixin with the baseline factory; `EnergyAdvancedFactory` combines it with calendar filling and early AGV dispatch. The engine, specification, advanced scheduler and independent checker are unchanged.

## Causal policy

The default `solar-tariff` policy uses current observed load/SOC/cap and the public deterministic daily price/solar profiles. It reads no generation seed, future defect outcome or future realized disruption. Battery actions retain their exact physical meaning:

- Charge: draw 10 kW, SOC +9 units.
- Discharge: supply 9 kW, SOC −10 units.
- Idle: no battery exchange.

A full charge/discharge cycle has 81% energy efficiency under the existing units. The policy compares marginal charging import against the value of the energy that can later be discharged after those losses. It charges during a cheap interval when a future peak interval remains, respects actual grid headroom and SOC capacity, and avoids filling after the final useful peak merely to end with unused stored energy. A sufficiently large partial solar surplus can justify charging even at peak tariff.

At peak, discharge is selected only when avoided grid import exceeds the low-tariff replacement cost after losses. This can include a partial discharge benefit with solar curtailment: the physical discharge action still supplies exactly 9 kW, and the bus equation limits curtailment to available solar. Export and disposal of excess battery output remain forbidden. A grid emergency takes priority when a legal action is available within the configured reserve.

The default `reserve="terminal"` retains at least the terminal minimum throughout the execution. On the frozen instance initial SOC equals that reserve, so no future charging forecast is needed to maintain its terminal guarantee. A load that cannot satisfy both the grid constraint and that conservative reserve remains an infeasible policy execution; the physical checker catches it. All measured default runs were electrically feasible.

The optional `reserve="recovery"` allows SOC down to the physical minimum while enough future low-price ticks remain in the calendar, and repays the terminal requirement afterward. It does **not** prove that those future ticks have charging headroom. All measured development runs recover successfully, while a deliberately saturated-grid test fails its terminal target. That failure is retained in the test suite. The default remains the conservative terminal reserve.

`objective="carbon"` uses the same decision logic with the public carbon profile. Cost and carbon need not have exactly the same optimum. The empirical comparison below uses the cost policy and reports both outcomes.

For static production policies every operation, part/tool move, worker walk, event and QUBO decision is identical across battery variants. Shipped orders and tardiness are identical too. A future production controller that uses SOC or energy-cost observations could change its scheduling decisions; that coupled case requires a new evaluation.

## Exact conditional reference

`fixed_load_dp(trace, objective="cost"|"carbon")` solves the stationary-battery problem on a saved realized load/cap/solar trajectory. It is explicitly **clairvoyant and conditional on that fixed trajectory**. It is not a causal controller, a production-scheduling optimum or a bound on the unrestricted factory objective.

For each integer SOC state and time tick, the Bellman recurrence tests every permitted battery action, rejects electrical or SOC violations, and retains the least cumulative grid objective. Final states must meet the original terminal minimum. Nonnegative objective coefficients make importing extra power while curtailing extra solar dominated, so the minimum-import bus balance for each action is sufficient.

kW and cost/carbon coefficients are validated at 1e−4 precision and converted to integer edge costs. The DP uses integer comparisons and backpointers; it introduces no SOC relaxation or discretization beyond the existing integer model. With the frozen 5760-tick, SOC 120..2400 instance there are 13,138,560 time/state combinations and at most three action transitions per state. Backpointers require approximately 14 MB. The saved plan is replayed into a full physical trace and checked independently. An exhaustive eight-tick reference and forced-grid-discharge cases test the exact solver.

If a source trace contains controller observations, they remain historical source observations in this counterfactual reference and are labeled accordingly; the DP never claims to replay that controller causally. Full-factory global optimality gap remains unknown.

## Running and artifacts

```sh
.venv-stage2/bin/python -m stage2.energy compare \
  --orders 8 12 24 --seeds 20 21 22 23 --workers 4 --advanced --dp \
  --output output/stage2-search/energy-v1-advanced

.venv-stage2/bin/python -m stage2.energy compare \
  --orders 8 12 24 --seeds 20 21 22 23 --workers 4 --dp \
  --output output/stage2-search/energy-v1-base

.venv-stage2/bin/python -m unittest discover -s tests/stage2 -p test_energy.py
```

The two frozen reports retain every trace, per-run production/energy/carbon metric, battery action count, conditional reference, source snapshot/hash and verification issue. Their common static production settings are WIP4, standard mode, calibration lease and priority selection. Both use the same full physical instance for each initial order count and actual seed. Every seed is development evidence; no held-out claim is made.

The final batches contain 72 causal traces and 48 conditional DP references: 120 traces in total. All full physical checks and terminal requirements passed. All battery variants retained identical physical scheduling actions within their paired production policy. Every four-seed causal policy group passed the empirical reveal-prefix audit. The audit remains a falsification test rather than a general nonanticipativity proof. Source hashes before/after matched in both batches. The complete focused checker/reference/advanced/burn-in/energy suite passes 100 tests, including 15 battery-specific tests.

The baseline-factory batch took 9.99 seconds wall time and the advanced-factory batch 10.89 seconds, each with four local CPU workers and run concurrently. Runtime was Python 3.14.6 and NumPy 2.5.4. No GPU, cluster connection or quantum hardware was used.

## Controlled development results

Each number below sums four actual tapes (seeds 20–23). Demand totals are 38, 54 and 102 for 8, 12 and 24 initial orders because seeds 20–22 reveal two urgent orders while seed 23 reveals none. Investment cost is unchanged at 150 per run and is excluded from this **energy cost** table; complete total costs remain in the raw reports. Production counts differ between the baseline and advanced scheduling algorithms, so energy totals across those algorithms are not an efficiency ranking.

| Production algorithm | Initial orders | Shipped/demand, all battery variants | Legacy energy cost | Terminal reserve | Recovery reserve | Exact conditional energy cost |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 8 | 38/38 | 1921.44 | 1838.76 | 1824.00 | 1813.42 |
| baseline | 12 | 42/54 | 2409.97 | 2313.68 | 2292.44 | 2288.73 |
| baseline | 24 | 48/102 | 2381.90 | 2286.68 | 2265.68 | 2259.14 |
| advanced | 8 | 38/38 | 2022.05 | 1940.58 | 1925.69 | 1915.01 |
| advanced | 12 | 43/54 | 2599.39 | 2501.22 | 2480.45 | 2478.29 |
| advanced | 24 | 46/102 | 2297.48 | 2203.22 | 2184.73 | 2176.14 |

The conservative default reduces per-run energy cost by 3.71–4.58% across the 24 paired scenarios. The lower-reserve policy reduces it by 4.51–5.44%, with carbon reductions of 4.15–4.90%. All measured schedules preserve their original production, transport, lateness and physical-resource decisions. Grid kWh can increase because shifting imports across tariffs/carbon profiles incurs conversion losses; these results are not a claim of universally lower electricity consumption.

For the advanced scheduler, recovery energy cost remains 0.025–0.699% above the exact fixed-load cost reference per scenario; for the baseline scheduler the range is 0.093–0.878%. These are conditional battery gaps, never global factory gaps. Separate exact carbon-optimal traces are retained, including small cases where the cost-optimal and carbon-optimal plans differ.

## Mechanism activation

Reports include measured activation alongside the energy results. In the legacy runs the stationary battery charges 200 times and never discharges; the original conservative start guards keep net load below the current grid cap. The causal strategies actively charge and discharge hundreds of times. The absence of emergency net-load ticks does not show that grid limits never constrain production starts.

Raw blank stock stays strictly positive in every measured n8/12/24 run: the seed 20 minima are 22/18/6 per type. Thus finite raw stock is genuinely nonbinding in these cases. Delivery still occurs, but the data do not support calling stock scarcity a demonstrated difficulty.

Other mechanisms are active. In the advanced n8/seed 20 trace there are 41 QA operations, 1 failed inspection with repair, 70 family setups, 90 worker walks, 38 tool transports, 7 tool services and 6 machine maintenance operations. Several input buffers reach capacity. The advanced n24/seed 20 trace has 5 multiunit heat batches and full input occupancy at 10 stations. Output-blocking durations and buffer occupancy are derived from committed process/move records; reaching capacity alone does not prove that a dispatch opportunity was denied. All underlying physical records pass the independent checker.

The deterministic viewer examples in `energy-v1-advanced/showcase-baseline.json`, `showcase-terminal.json` and `showcase-recovery.json` use the first development scenario (8 initial orders, seed 20). They show the same physical production with different SOC/grid trajectories. They are visualization examples rather than independent evaluation evidence.

Frozen energy source SHA256: `af64114ac4f0d8ff80fb27e1358b46fa0ad1e8353b9add5e91fc95e2c3ac9271`. The source snapshots and exact hashes are retained beside both reports.
