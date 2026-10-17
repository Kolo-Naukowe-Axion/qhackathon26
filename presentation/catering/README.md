# The little catering kitchen — checked V3 replay

Run `PORT=4192 npm run dev`, then open <http://127.0.0.1:4192/catering/>.
The normal `npm run build` includes this static page. No API or solver runs in
playback, and no credentials are embedded in the page.

## What the viewer explains

A complete meal needs a main course and a side course at the same fixed departure.
The kitchen must schedule batch quantities, shared allocations, equipment, workers
and prepare/cook/pack/clean phases. The scene uses the checked operation times,
identified attendance, complete-meal handovers and discarded component records.
Main and side reservations are never separately counted as delivered meals.

Choose the **complete small cell** for the encoding walkthrough: all 32 legal
programs plus 3 idle choices, 35 data qubits. It replays an actual retained QAOA
sample, observed 13 times in the declared p1/seed2026 trial, with tuple (0,0,2,2).
The initializer and mixer-only controls also attain that optimum. This is a
correctness example, not an advantage claim or the larger six-customer kitchen.

Choose **larger S0/S1/S2/S3** for the changing-portfolio experiment. The default
QAOA view is the final accepted plan from seed2026, traced to its actual retained
sample and exact step bundle. The source selector also offers the exact result
on that same accepted-step portfolio, and the independent raw-grid classical
reference. These are different domains with explicit labels. All eight larger
QAOA runs, including seed2027 and their gaps, appear under Model & results.

The replay includes mandatory C2 recovery cleaning at minute70–80, with W2.
Repair ends at60; C2 waits until the clean and cannot resume cooking before80.
Cleaning occupies equipment and the cleaning worker, is visible on the timeline,
and can be inspected through C2 or the recovery-clean bar.

## Interaction and visual direction

The room retains the pixel-game art, native directional chef sprites and timber
controls. Selected program tokens reveal each batch's full phase instructions.
Expand x to inspect any option or idle bit. A checked “Skip batch” intervention
sets that program to0 and its anchor's idle bit to1; the actual plan, complete
handovers, discarded components, worker tracks and metrics all change together.
This is a manual intervention, never a synthetic solver result.

Playback supports seeking, speed, looping, restart, per-operation timeline
inspection and Space while no control is focused. The optional decode tour holds
the clock while explaining programs, course pairing and timed instructions.
Reduced motion starts paused. The Model & results dialog provides inputs,
constraints, objective/penalty equations, measured results, source paths and hashes.

Positions and walking are illustrative; the physical model has no travel-time
constraint. Worker tracks are continuous through recorded attendance changes;
cleaning has a separate approach to cookers so sprites can pass without overlap.
The viewer reconstructs pose and props from replay time, so seeking and pausing
are deterministic. The portrait layout crops the scene around the working kitchen.

## Rebuild from retained evidence

```sh
.venv-stage2/bin/python presentation/catering/build-data.py
node --test tests/catering-replay.test.mjs tests/catering-motion.test.mjs tests/catering-translation.test.mjs
npm run build
```

The exporter runs no optimization. It loads V3 bundles, verifies the actual cell
receipt/sample hash, independently decodes and checks displayed samples, verifies
the final larger plan against its accepted raw sample, reconstructs the same-domain
exact reference and checks raw classical plans. It rejects invalid or mismatched
results. It exports five cases and sixteen source views to replay-data.json.
Every source view retains a source SHA-256 and, where applicable, exact bundle hash.
Tests check source identity, bit selections, one-hot validity, complete-meal counts,
recovery-clean boundaries, interventions and continuous motion across every view.

The earlier V1 exporter and its incorrect outage results are superseded. The
original uncommitted UI was backed up locally before this integration in
/private/tmp/qhackathon-catering-ui-before-v3.tgz; historical backend evidence stays
unchanged. Generated background art/provenance is documented in assets/README.md.
The unused art references are retained because repository cleanup is deferred.

VeloxQ's separate method owner receives larger inputs of the same model, currently
512/1024/2048 variables. See docs/catering-methods/VELOXQ.md. Their results will
be integrated once measured; no service or hardware result is invented here.
