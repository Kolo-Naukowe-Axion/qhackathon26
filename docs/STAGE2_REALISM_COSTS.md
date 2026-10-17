# Quantitative price of realism: explicit variable families

`stage2/realism_costs.py` supplements the stable encoding audit with numerical costs of declared time-indexed representations and a reconstruction/ablation of actual frozen local QUBOs. It builds no global QUBO, changes no physical source and launches no factory, quantum or hardware jobs. Current evidence is `output/stage2-search/realism-costs-v3/`: complete numerical instances for8/12/24 orders, family reports, frozen source/blueprint copies, input hashes and a source-stable manifest.

These are allocated family sizes **before linking, presolve and feasibility pruning**, not necessary variable lower bounds. Some families replace or derive others, so their counts must not be added into a complete-global total or divided by five to claim lossless compression. The executable report deliberately leaves both total and reduction ratio null. Scenario/history copies, nonanticipativity, risk arithmetic, global power balance and linking/quadratization auxiliaries remain uncompiled and uncounted.

## Declared representations and counts

The table uses the full minute-grid24-known-order instance: horizon H=5760,15 machines,10 workers,2 halls,4 AGVs,24 graph nodes,3 material families and6 possible tools including the rental. Boundary-state arrays have H+1 cells; tick-action arrays have H cells. These rows describe the known-order single-trajectory envelope. Maximum urgent births are separately reported, not silently included in these counts.

| Feature / chosen variable family | Allocated bits |
|---|---:|
| Nominal manufacturing starts over machine/mode/time |8,976,072|
| Bounded-quality production-start envelope, **including** nominal starts |25,143,624|
| Worker hall indicators / walking-occupation flags |115,220 /57,600|
| Tool physical-node indicators / carrier-or-absence states |829,584 /172,830|
| Tool remaining-life counters / node-service starts |345,660 /820,944|
| Machine wear counters on exact rational grid |1,123,395|
| Machine family indicators / maintenance starts |345,660 /85,290|
| Reserved-or-present input counters / output-blocked flags |207,396 /86,415|
| Potential-part location/terminal-state indicators |30,971,136|
| Part acceptance flags / BOM-consumption event envelope |967,848 /967,680|
| Finite raw-stock counters |103,698|
| Nominal loaded-pickup choices across AGV/endpoints/time |42,281,760|
| AGV node indicators / SOC counters |553,056 /184,352|
| AGV charger-occupation flags |46,080|
| Stationary idle/charge/discharge indicators / SOC counters |17,280 /69,132|
| Heat batch-family activation starts |33,846|
| Rental request-time indicators / derived in-horizon arrivals |5,760 /5,281|

Each JSON row retains its exact formula and omissions. Representative formulas are W×2×(H+1) worker hall indicators, T×N×(H+1) tool-node indicators, and `(H+1)Σ ceil(log2(limit+1))` binary counters. Tool location additionally needs four carrier states and an absent/unborn state; workers have separate walking occupation. Node flags alone do not describe in-transit motion. Raw counters use capacity34=30 initial+4 delivered blanks per type, giving6 bits per counter; integer top-code bounds still require constraints.

Machine wear needs special units. Eco wear is3/5 per processing minute, so the common rational grid has denominator5. Wear limit1050 becomes5250 scaled units, requiring13 bits per machine counter. A slow-mill housing eco operation lasts169 minutes and consumes507 scaled units=101.4 wear. Using11 integer-wear bits would lose this physical state. Tool life is integer processing minutes (600→10 bits); AGV SOC uses integer traction/charge units (160→8); stationary SOC is already integer units of1/60 kWh (2400→12). Fractional quality-risk products are not encoded merely because these counters are counted. The grid represents mathematical decimal-table values, not every IEEE rounding artifact.

The quality envelope has44 potential production slots per order: two possible component versions each contribute their normal route plus one repair-and-QA pair; the single pump contributes assembly/QA plus one repair-and-QA pair. Thus there are1056 slots for24 known orders, or1144 including the maximum two urgent births, versus384 nominal slots. Failure, replacement lead time and birth gates can force many slots inactive. The25,143,624 count expands only known-order slots over the same certified modes, stations and relaxed start windows; it is an alternative envelope to the nominal-start count.

Transport has79 legal nominal endpoint alternatives per order, with recipe/leg identity retained: housing26, rotor26, flange21, pump6. Each starts loading at an integer tick, names one of four AGVs, and must leave enough time for shortest loaded travel plus one-minute loading/unloading. There are42 same-hall4-minute alternatives and37 interhall8-minute alternatives. Summing `4×max(0,H−duration−order_release+1)` gives42,281,760. These are **loading/pickup choices**, not empty-dispatch choices. Empty preposition, earlier reservation start, vehicle continuity, lane occupancy and tool/repair/scrap transfers require additional modeling.

Heat-family starts can share the already counted member manufacturing-start variables, but need batch activation/compatibility/capacity and setup links. Likewise matched BOM lineage is fixed data; acceptance, birth and consumption must still be linked. Rental arrivals can be derived from requests, so their5281 indicators are optional redundant state rather than5281 independent investment decisions. Requests at ticks0–5759 include late arrivals after the horizon; zero-lead and horizon endpoints are explicitly tested.

## Actual local constraint-family ablation

The frozen input is the independently checked `checked-qaoa-8/trace.json`, SHA256 `a66e7861532b77cd0578aa88a1a03a79d243ecff7931ff24eea8950cb44fb023`. All148 offer/candidate/conflict/capacity records are reconstructed independently. Rebuilt complete encodings agree with recorded core/slack/total bits, couplers, capacity encodings and integer-GCD scales. Each ablation keeps the same candidates/rewards; removed constraints are structural diagnostics and are never executed as factory actions.

| Encoding on the same148 pools | Sum of slack bits across calls | Sum of couplers across calls | Max total bits |
|---|---:|---:|---:|
| Reward only |0|0|5|
| Worker conflicts only |0|130|5|
| Machine conflicts only |0|20|5|
| Tool conflicts only |0|16|5|
| Same-unit conflicts only |0|0|5|
| All pair conflicts |0|130|5|
| Power only |9|71|11|
| Full recorded formulation |9|187|11|
| Full without worker conflicts |9|87|11|
| Full without power |0|130|5|

Conflict families overlap: the machine/tool pairs in this realization are already covered by worker conflicts. Their individual counts cannot be summed, and removing a duplicate penalty may change coefficients without changing coupler count. The zero same-unit count reflects the prefiltered actual offers, not permission to process one unit twice. Pair exclusions use no extra bits. Power uses exact integer-GCD normalization, removes redundant rows, uses pair penalties for unit capacity, and otherwise adds bounded binary slack.

Only ticks1726 and3785 require slack:6 and3 auxiliary bits, yielding11- and6-bit QUBOs. Both were explicitly classical fallbacks. Tick3790 has a genuine two-bit simulated power-conflict circuit without slack. Across the full trace,146 calls actually simulate QAOA,51 are coupled and94 are trivial one-bit calls; no physical processor runs. Most measured simulated coupling comes from worker conflicts. Sums above count repeated local encodings, not simultaneous physical qubits.

Calendar legality, travel, tool life/location, buffer/BOM readiness, certification and hidden-event guards are prefiltered classically. They therefore add zero **auxiliary bits in this frozen local selector**, while carrying real classical planning/state costs. This decomposition is the honest engineering tradeoff; it does not establish a globally lossless QUBO or a full-policy optimality gap.

## Reproduce and scope checks

```sh
.venv-stage2/bin/python -m unittest discover -s tests/stage2 -p test_realism_costs.py -v
.venv-stage2/bin/python -m stage2.realism_costs --orders 8 12 24 \
  --trace output/stage2-search/checked-qaoa-8/trace.json --output NEW_DIRECTORY
```

Twelve tests check arithmetic/endpoints,79 route alternatives against independent same/interhall counts, real bridge/release changes,44-slot bounds, fractional wear units, counter/lease sensitivity, disjoint worker attendance, overlapping conflict reasons, actual checked trace reconstruction, nonmutation, rejection of corrupted conflict metadata, and retained numerical-instance/source/blueprint hash agreement. The actual local ablation takes about0.02 CPU wall seconds; this is counting/reconstruction time, not solver speed or training cost. Core enumeration is capped at12 candidates; larger pools retain structural counts with a null exact-reward field.

Version1's integer-wear count was caught by independent root review and is superseded. Version2 corrected units; version3 additionally preserves complete instances, source copies and blueprint hashes. Earlier reports remain as development history. Quantifying these families substantially improves the challenge's price-of-realism account, but no complete global linking/contingency QUBO, global secondary gap or quantum advantage is claimed.
