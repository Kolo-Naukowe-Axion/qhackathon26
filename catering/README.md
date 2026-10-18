# Catering: run, verify, inspect

Axion Kitchen chooses compatible batch programs: quantities, shared allocations,
equipment, qualified workers and phase times. Both a main and a side must reach
an order's departure to count as a complete meal. Freshness, cleaning, committed
work and resource calendars constrain the plan.

The implemented profile is `paired-course-contiguous.v3`. Start with
[the formal problem statement](../docs/CATERING_PROBLEM.md),
[the design and proofs](../PROJECT_DESIGN.md), [measured quality](../docs/CATERING_QUALITY.md)
and [the presentation plan](../docs/CATERING_PRESENTATION.md).

## View or launch

```sh
PORT=4192 npm run dev
```

Open `/catering/` for checked saved schedules and `/catering/benchmarks/` for
the retained comparisons. The static viewer does not execute a solver.

For a fresh local sample, install the foundation environment (Python 3.12+; Python 3.14.6 was
verified) and start the private studio:

```sh
python3 -m venv .venv-catering
.venv-catering/bin/python -m pip install -r catering/requirements.txt
.venv-catering/bin/python scripts/serve-catering-showcase.py --port 4193
```

Open `http://127.0.0.1:4193/?mode=live`. Its button replays the trained depth-three
QAOA circuit with frozen angles, draws fresh local samples and checks every
returned schedule. No training, credentials or external execution is needed.

## Verify without training

```sh
.venv-catering/bin/python scripts/check-catering-release.py --output /tmp/axion-check-01
```

Use a fresh output directory. The checker restores hash-verified compressed
evidence, builds/tests the viewer, checks the displayed sources and archived
quantum campaigns, reruns the mathematical audit, and performs three bounded
local sampling checks. Its receipt separates technical checks from the pending
human rehearsal, recording, publication and submission. It never calls VeloxQ
or a physical QPU. Node.js 20+ is required for the site checks.

For QAOA/VQE engine unit tests, use Python 3.11 and
`catering/requirements-methods.txt` in a separate environment:

```sh
python3.11 -m venv .venv-catering-methods
.venv-catering-methods/bin/python -m pip install -r catering/requirements-methods.txt
.venv-catering-methods/bin/python tests/catering/test_qaoa.py -q
.venv-catering-methods/bin/python tests/catering/test_vqe.py -q
```

Those unit tests perform tiny local optimizer checks. They do not rerun the
retained campaigns. One optional Qiskit equivalence test skips in this minimal
environment. For the pinned VeloxQ SDK test environment and exact offline test
command, see [VeloxQ reproduction](../docs/CATERING_VELOXQ_TUNING.md#reproduce-locally).
The live demo does not require those SDKs.

## Which evidence answers which question?

| Evidence | Scope and use |
|---|---|
| `output/catering-complete-cell-v3/` | All 32 legal programs of a narrow declared grid; 35 data qubits including idle, 1,045 invariant-sector states, optimum `(0,0,2,2)` |
| `output/catering-foundation-v3/` | S0/S1/S2/S3 fixed 33/35/31/35-bit portfolios, exact offered references and independent full-grid references |
| `output/catering-methods/qaoa/` | Frozen protocol, 400 archived runs, trained angles, controls, manifests and full return records |
| `output/catering-methods/vqe/` | E1/E2/E3/E5 CSVs, five checked exports and integration-v2 audit; old per-seed E5 angles/raw samples are absent |
| `output/catering-velox-scale-v3/` | Nested 512/1024/2048-source-bit restrictions of 18,182 local programs; measured interactions |
| `output/catering-velox-conditioned-service-v1/` | Proven penalty/no-idle representation study; actual solver widths 486/998/2022 and retained service receipts |
| `output/catering-math-audit-v1/` | Independent formulation, physical-checker and exact small-domain audits |

Compare `(U,W,B,R)` across different scalarizations, and energies only on the
same bundle. U counts **priority-weighted meal lots**; W counts discarded
component lots; each lot is ten portions. R=B in the current fixtures because
the previous unstarted plan is empty. Current plots do not demonstrate a
separate stability improvement.

QAOA is the primary reproducible live method; VQE is the second ansatz
comparison; VeloxQ supplies the larger same-model representation study.
Classical references expose both solver error and loss from restricted choices.
The larger quantum portfolios exclude better full-grid schedules. There is no
measured quantum advantage or catering physical-QPU result.

## Preserve the shared model

Use `catering.contracts.load_bundle`, `catering.qubo.energy` and
`catering.decode.decode` with the frozen variable order and bundle SHA256.
The [solver contract](../docs/CATERING_SOLVER_CONTRACT.md) defines MethodResults.
Never overwrite inputs, raw returns or manifests; new formulations get new
identities. The proof-backed VeloxQ transformation has its own identity and
does not change anyone's existing quantum inputs.

The [historical guide](../docs/archive/2026-10-17/CATERING_GUIDE_BEFORE_RELEASE.md)
preserves the earlier v2/v3 handoff. V1 omitted recovery cleaning; v2 has a
different component-demand objective. Those files remain regression evidence,
not the active results. Research sources and artifact paths stay in place.

Large evaluator JSONs are stored losslessly in the shared gzip catalog. After
pulling, `node scripts/restore-compressed-evidence.mjs` restores their exact
original bytes and paths; `npm run build` does this automatically. The current
cleanup packs 30.3 MB into 0.89 MB without changing any sample or source hash.
