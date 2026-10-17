# Capacity economics: audited valuation of actual recovery plans

17 October 2026. The completed [v2 ledger and sensitivity study](../../../output/capacity-economics-v2/report.json)
values four saved, independently checked schedules under explicit synthetic
prices. It does **not** optimize schedules for money. The schedules still
minimize weighted terminal tardiness first and makespan second.

## Assumptions and exact accounting

All amounts are illustrative PLN. Electricity repeats every 1,440 minutes:
0.50 PLN/kWh during minutes 0–360, 1.00 during 360–1,080 and 0.70 thereafter.
Attended labor costs 40 PLN/hour, with a further 10 PLN/hour during 0–360 and
1,320–1,440. Worker walking, setup crews and salaried standby are excluded.

Active machine power is T/F/S/WASH/H/QA/A = 9/12/10/4/16/3/4 kW. Active power
already includes standby. Used machines remain powered from their first start
to final end, drawing 0.5 kW in idle/setup gaps; unused machines stay off. Each
used machine costs 5 PLN to start. Plant base load is 12 kW from time zero until
completion. The default late penalty is 10 PLN per weighted late minute.
These are declared policies and rates, not optimized activation decisions or
measured industrial costs. No solar, battery, demand charge or grid cap is added.

The implementation uses exact rational arithmetic over interval boundaries,
including tariff/night crossings. Every record retains its original model,
plan and profile hashes, all nine monetary line items and energy totals.

| Saved plan | Weighted late minutes / makespan | Operating cost | Late penalty | Total before capacity fee |
|---|---:|---:|---:|---:|
| Outage complete-model reference |45 /945 |955.4875 |450 |1,405.4875 |
| Replacement complete-model reference |0 /855 |930.9458 |0 |930.9458 |
| Replacement original cap24 pool |45 /945 |951.0833 |450 |1,401.0833 |
| Replacement enriched cap64 pool |0 /855 |933.4667 |0 |933.4667 |

The two on-time plans share the original objective value 855 but have different
operating costs. That is expected: the original optimization does not distinguish
their monetary cost. Neither ledger establishes a minimum-cost schedule.

## A concrete capacity decision under declared prices

For late rate c and per-event capacity fee f, compare each saved replacement
plan against the saved outage plan. Net benefit is

`saved operating cost + c × saved weighted late minutes − f`.

| Replacement representation | Operating savings | Saved late minutes | Maximum fee at c=10 | Net benefit at c=10, f=100 |
|---|---:|---:|---:|---:|
| Complete |24.5417 |45 |474.5417 |374.5417 |
| Original pool |4.4042 |0 |4.4042 |−95.5958 |
| Enriched pool |22.0208 |45 |472.0208 |372.0208 |

Thus the original pool would reject the illustrative 100 PLN capacity fee based
on these plans, while both on-time representations would accept it. This is a
conditional comparison of actual schedules. It demonstrates a decision
consequence of representation loss without claiming optimal monetary policy.
For that fee, the complete plan breaks even at c≈1.67685; the enriched plan at
c≈1.73287. Raising the late rate cannot help the original pool's zero saved
tardiness. All 135 declared sensitivity combinations are retained.

## Repeated exposures and capital-price sensitivity

The optional illustrative scenario assumes event probability 0.3, 52 exposures
per year, three years, 5% annual discount, 50 PLN annual maintenance and 100 PLN
installation. Events are known before replanning. In no-event cases the optional
capacity stays off and differential operating costs cancel. No demand or failure
distribution has been estimated.

For the complete plan at c=10 and f=100, annual expected net benefit after
maintenance is 5,792.85 PLN, and its three-year discounted value is
15,675.3673 PLN. The separate maximum upfront purchase-price calculation assumes
**purchasing replaces the per-event lease fee**, so it excludes f from annual
purchase cash flows and subtracts installation once. Its resulting illustrative
threshold is 19,923.6343 PLN. These are different cash-flow questions; the lease
fee is not charged again in the capital alternative.

This is purchase-price sensitivity under chosen assumptions, not a calibrated
ROI recommendation, stochastic robust schedule or general conclusion about
buying a second mill. The studied resource is replacement heat capacity.

## Independent verification and reproduction

The [independent audit](../../../output/capacity-economics-independent-audit-v1.json)
matches the authoritative v2 report hash, checks nine manifest files and
recomputes every monetary line item for all four schedules minute by minute
using separate Fraction arithmetic. Its four targeted economics tests pass.
The interval ledger is not used by the independent arithmetic implementation.

Implementation: [capacity_economics.py](../../../stage2/capacity_economics.py).
Tests: [test_capacity_economics.py](../../../tests/stage2/test_capacity_economics.py).

```sh
.venv-stage2/bin/python -m unittest tests.stage2.test_capacity_economics -v
.venv-stage2/bin/python -m stage2.capacity_economics --output output/NEW-ECONOMICS
```

The report is source-stable. No VeloxQ, credentials, remote compute, hardware,
publication or paid service was used. Monetary reoptimization would require a
new objective, justified penalties and matching independent references.
