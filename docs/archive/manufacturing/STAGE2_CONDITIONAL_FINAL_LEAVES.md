# Observed performance within the eight final leaves

`output/stage2-search/final-conditional-leaves/report.json` covers all 74 final method/context groups, or 592 leaf cells. `selected-and-mpc.json` contains only the eight preselected frontier methods and five MPC methods. The helper, input hashes and output hashes are retained alongside them. This is reporting over completed evidence: zero factory runs and zero policy changes.

Every cell contains the same 32 environment tapes declared for its leaf. Stochastic actor replicas are averaged within each environment before averaging environments; they do not increase the independent environment count. Multiplying the eight conditional means by their exact declared leaf probabilities recovers every reported overall mean. The helper checks this with exact rational arithmetic and cross-checks the published missing/debt/cost/carbon/success means for all 74 groups. Three tests cover actor nesting, missing/duplicate rejection and exact probability recovery.

The following values are **observed conditional means**, not causal effects of an outage, rush order or delayed supply. Different leaves have different keyed quality seeds. No confidence intervals are calculated here; a cell with 32 successes does not establish population success probability one.

| Mill | Supply | Rush | True leaf probability | CEM16 missing | MPC16 missing | CEM24 missing | Stretch32 missing | Stretch32 observed all fulfilled |
|---|---|---|---:|---:|---:|---:|---:|---:|
| Available | Normal | No | 0.195 | 1.3125 | 0.96875 | 8.875 | 0 | 32/32 |
| Available | Normal | Yes | 0.195 | 3.09375 | 3.125 | 11.09375 | 0.09375 | 29/32 |
| Available | Delayed | No | 0.13 | 1.875 | 1.59375 | 9.1875 | 0.0625 | 30/32 |
| Available | Delayed | Yes | 0.13 | 4.3125 | 3.84375 | 10.84375 | 0.28125 | 25/32 |
| Outage | Normal | No | 0.105 | 1.625 | 1.09375 | 9.0625 | 0.0625 | 30/32 |
| Outage | Normal | Yes | 0.105 | 3.65625 | 2.84375 | 10.71875 | 0.125 | 28/32 |
| Outage | Delayed | No | 0.07 | 2.5625 | 1.4375 | 8.96875 | 0.03125 | 31/32 |
| Outage | Delayed | Yes | 0.07 | 4.1875 | 4.03125 | 11.6875 | 0.25 | 26/32 |

The 16/24-order cases use H5760, while the 32-order stretch uses H14400. They are different declared calendars, so the latter's higher fulfillment rate is not evidence that adding demand improves throughput. Missing counts include realized urgent demand. Full leaf records also contain cutoff deadline debt, delivered-only tardiness, energy cost, grid energy and carbon.

For the matched CEM16/MPC16 comparison, the helper additionally verifies all 32 numerical instance pairs within each leaf and reports observed MPC-minus-CEM missing-order differences. Seven leaf means decrease and one increases slightly. These are descriptive subdivisions of existing comparisons, not new predeclared primary tests or a prior-robust guarantee. All final selection remains fixed.

Report SHA-256: `b05fcc5cb1bfb604e72c5e70fe5f97cdb7d946faf4760da5eef51596a16776a2`. Compact report SHA-256: `132d737fa04abdbad98a378ee82472f2dd13cda960db7f5262e83c546537a94a`. `output-index.json` records the exact helper and test hashes as well.
