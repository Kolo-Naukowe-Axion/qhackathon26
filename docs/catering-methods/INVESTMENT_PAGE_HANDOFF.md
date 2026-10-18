# Handoff: investment report page

Goal: add a public page `/catering/investment/` that answers the challenge
question “what should the kitchen invest in?” as a readable report. The data
is ready and checked; the page only displays it. No solver, training or
service call runs on the page or is needed to build it.

Background and wording: [CATERING_INVESTMENT.md](../CATERING_INVESTMENT.md)
and “Claims to keep precise” in [CATERING_FINAL_HANDOFF.md](../CATERING_FINAL_HANDOFF.md).
The submitted video and final release receipt already exist; a new page means
a new release check (see the last section).

## What is ready

| Item | Path |
|---|---|
| Page data (the only input of the page) | `presentation/catering/investment/data.json` |
| Exporter (reads retained results, no solving) | `scripts/export-catering-investment.py` |
| Retained CP results, two seeds | `output/catering-investment-v1/{seed,skills-seed}-{2026,2027}/` |
| Experiment code | `catering/investment.py` |
| Pin test: data.json equals a fresh export, key decisions | `tests/catering/test_investment.py` |

Regenerate after any change to the retained results or the exporter:

```sh
.venv/bin/python scripts/export-catering-investment.py
.venv/bin/python -m pytest -q tests/catering/test_investment.py
```

Do not rerun `catering.investment` for the page: each variant is a 240 s CP run.

## data.json (`schema: catering-investment.v1`)

- `question`: the headline question.
- `case`: the S3 lunch. `meals` = 14 meals (`meal_ids`), `lot_size` = 10, so
  `total_meals` = 140. `workers` (skills today: W1 prepare+pack, W2 clean, W3
  cook), `equipment`, `available_minutes` per resource (320 each), `outages`
  (C2 20–60 min), `urgent`, `horizon_minutes`, `time_origin` (10:30), `grid_minutes`.
- `method`: CP 240 s, 2 CP workers, seeds 2026 and 2027, `optimality_proved:
  false`, zero quantum/VeloxQ/QPU calls, `tuple_order`, `reproduce` command.
- `variants[]`, in the order of `catering.investment.VARIANTS` (12 rows):
  - always: `id`, `label`, `short` (chip/axis label), `kind`
    (`none`/`equipment`/`worker`), `description`, `scenario`, `status`;
    `skills` for workers, `resource` for equipment.
  - `status: "unsupported"` (only `second-pack`): has `reason`, no numbers.
    Show it as “not modelled”, never as zero or a guess.
  - `status: "checked"`: `tuple` [U,W,B,R], `meals_served` (of 140),
    `extra_meals_vs_today`, `waste_portions`, `served_meals`/`missed_meals`
    (meal ids), `handovers` [{meal,time}] (minutes from `time_origin`),
    `worker_minutes` {W: {prepare,pack,cook,clean,recovery_clean,total}}
    (attended minutes), `resource_minutes`, `batches`, `programs` (complete
    program register = QUBO bits before any cut), `register_multiplier`
    (vs today), `per_seed` (both seeds, identical tuples), `solver_status`
    (`FEASIBLE` = time limit before proof), `objective`, `bound`,
    `instance_sha256`.
- `decision`: `today_missed_lots` 5, `best_missed_lots` 3, `extra_meals` 20,
  `fewest_skills_sufficient` = `worker-pack`, `equally_few_skills` =
  [`worker-prepare`, `worker-pack`], `equipment_improved_service_in_runs` =
  false, `bottleneck`, `claims` (five sentences matching
  CATERING_INVESTMENT.md, safe to print verbatim), `price_of_realism`.
- `notes`: scope sentences to show near the table.
- `source_files`: path + SHA-256 of every file read, for an evidence list.

The highlight rule is in the exporter: lowest U, then fewest added skills,
then smallest register. It is a structural tie-break, not a price: call it
“sufficient with the fewest added skills”, never “cheapest” or “best investment”.

## Suggested page (report order)

1. **Answer first.** “In these runs a packing (or prep) helper serves 20 more
   meals per lunch; a third cooker serves none more.” Built from `decision`.
2. **Options table / bar chart** of `meals_served` for every variant, grouped
   equipment vs people; highlight `equally_few_skills`; unsupported
   row labelled “not modelled”. Show the tuple and waste as secondary columns.
3. **Why: the bottleneck.** Stacked bars of `worker_minutes` (by task) against
   `available_minutes` for today vs `worker-pack`: today W1 is attended
   300 of 320 minutes; with a packing helper W1 drops to 140. Text from
   `decision.bottleneck`.
4. **Who still misses lunch.** `missed_meals` today vs `worker-pack` (5 → 3 meals).
5. **Break-even calculator (client-side only).** Inputs: margin per meal and
   cost per extra shift, empty by default. Output: `extra_meals × margin −
   shift cost`. Do not prefill prices; the project assumes none.
6. **Price of realism.** `programs` / `register_multiplier`: flexibility costs
   qubits (×8.3 flexible, ×2.0 helper); link to `/catering/benchmarks/#scaling`.
7. **Scope and sources.** `notes`, `method` (best found in 240 s, not proved
   optimal; classical study, no quantum calls), `source_files`, download link
   to `data.json`.

“Generate report” can be a print-friendly view of the same page
(`@media print`, `window.print()` button) plus the `data.json` download.

## How to build it (follow the benchmarks page)

- Copy the structure of `presentation/catering/benchmarks/`: `index.html`,
  `investment.js` (ES module, `fetch('data.json')`), `investment.css` (reuse the
  benchmarks palette and Manrope fonts from `/assets/branding/`).
- Export pure functions from `investment.js` (e.g. `optionRows(data)`,
  `breakEven(data, margin, shiftCost)`), and keep DOM code behind them, so
  Node tests can import them like `tests/catering-showcase.test.mjs` imports
  `benchmarks.js`. Add a test there that pins 12 variants, `worker-pack`,
  and the unsupported row.
- CSP in `vercel.json`: `script-src 'self'` — no CDN scripts, no inline
  `<script>`; inline styles are allowed. Charts: hand-written SVG or CSS bars.
- Escape every string inserted with `innerHTML` (see `escape` in `benchmarks.js`).
- `scripts/build.mjs` copies all of `presentation/`, so the page deploys
  without build changes.
- Add `node --check presentation/catering/investment/investment.js` to the
  `check` script in `package.json`.
- Link it: nav in `presentation/catering/index.html` (`benchmark-links` and
  `evidence-navigation`), the benchmarks header nav, and
  `docs/CATERING_INVESTMENT.md`.

## Wording rules

- Say “best plan found in 240 s”, not “optimal”. Both seeds agree. Do not
  claim equipment can never help or that +20 meals is the maximum.
- The single-task helper is a sufficient skill set, not the cheapest hire.
- No invented prices, wages or margins.
- Second packing line: “not modelled (the core profile has one packing line)”.
- This is a classical what-if on the same model; do not attribute it to QAOA,
  VQE or VeloxQ.
- Meals are lots of 10: U=5 means 50 of 140 meals missed.

## Before committing

1. `.venv/bin/python -m pytest -q tests/catering` and `npm test && npm run
   check` (Node ≥20; the release checker also needs Node and npm).
2. Open the page through the local server and check desktop and phone width.
3. If the live/video route mentions the page, edit `scripts/catering-showcase/story.json`,
   then `npm run docs:write`. The live route has only 15 s of margin.
4. `scripts/check-catering-demo.py` must print READY FOR REHEARSAL; then run
   `scripts/check-catering-release.py --output NEW_DIR` and record the new
   receipt as in earlier commits, so the submitted commit is covered.
