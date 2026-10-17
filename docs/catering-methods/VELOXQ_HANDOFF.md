# VeloxQ track: handoff (17 October 2026)

For the next agent or owner of Person 1's VeloxQ track
([workplit](../CATERING_METHOD_WORKSPLIT.md)). Full evidence and tables are in
[VELOXQ.md](VELOXQ.md). This page covers the state, the rules, where things are
and what is still open.

## State in one paragraph

The adapter (`catering/methods/veloxq.py` 0.2.0) works end to end against the
service with exact integer packets. 54 service attempts are recorded in
`output/catering-methods/veloxq/job_ledger.json`, across phases C–H. Every
returned sample was decoded by `catering.run evaluate` without repair.

**Result:** VeloxQ reaches the CP-SAT optimum on the 31–35-variable QUBOs. From
256 variables up it is behind seeded SA on the same matrix, and at 2,048 it
returns no valid state. Smaller local penalties, low-conflict program pools and
a 20–128× larger budget each changed the best U by at most 1–2 lots.

**No further service jobs are authorized.** The user approves each new cap.

## Rules (do not skip)

- Token only via the `VELOX_TOKEN` environment variable; never write it to
  files, commands or logs. Check presence with `[ -n "$VELOX_TOKEN" ]`.
- `--max-service-jobs N` is the **ledger total** including every earlier
  attempt (currently 54). Set and record the cap in
  `output/catering-methods/veloxq/pilot_manifest.json` **before** submitting.
- No automatic retries. An attempt counts even if it fails.
- `ConnectError` is frequent (about 1 in 6 attempts; more often under heavy
  local CPU load).
  - If the result has a `job_id`, the job exists: recover it by id (below);
    do not resubmit.
  - If `job_id` is null, nothing was created; resubmit only if the declared
    plan allows it.
- Compare decoded (U,W,B,R) tuples, never raw energies across bundles. Do not
  modify frozen inputs; new formulations are separate bundles with
  `parent_sha256`.
- Use `.venv/bin/python`. `ortools==9.15.6755` was added to `.venv` with
  `uv pip install --python .venv/bin/python ortools==9.15.6755` (no pip in this
  venv). Node is not installed on the original machine.

## Phases and what each one showed

| Phase | Ledger | What | Finding |
|---|---:|---|---|
| C | 1 | Two-variable smoke | Service returns SPIN energies without the Ising offset, as float32 |
| D | 2–20 | Frozen bundles, 512×2,000; S3 quantum repeat; num_steps 20,000 on two | Small QUBOs: optimum. ≥256: worse than SA. 2,048: no valid row |
| E | 21–30 | Local penalties (`veloxq_penalty.py`), with and without B/R | float32-exact packets, no gain for VeloxQ; hurts SA validity |
| F | 31–34 | Low-conflict pools (`veloxq_lowconflict.py`) | Half the conflicts; CP-SAT proves optima; VeloxQ 0–1 valid rows |
| G | 35–42 | num_rep/num_steps grid (SDK defaults 4,096×5,000 and above) | U 13→11 at 512 with 128× samples; cell optimum reliably |
| H | 43–54 | Phase E/F cost functions on 1,024/2,048 at 4,096×5,000 | 2,048: zero valid everywhere; 1,024: best U 13 |

## Where things are

| Path | Content |
|---|---|
| `catering/methods/veloxq.py` | Adapter and CLI (`--num-rep`, `--num-steps`, `--timeout`) |
| `catering/methods/veloxq_penalty.py` | Local-penalty variant builder with a feasibility proof and randomized check |
| `catering/methods/veloxq_penalty_sa.py` | Same-SA comparison of source vs variants |
| `catering/methods/veloxq_lowconflict.py` | Low-conflict pool builder plus 30 s CP-SAT reference |
| `tests/catering/test_veloxq_adapter.py`, `test_veloxq_penalty.py` | 66 + 18 offline tests |
| `output/catering-methods/veloxq/pilot_manifest.json` | Caps, declared plans and results per phase (C–H) |
| `output/catering-methods/veloxq/job_ledger.json` | Every attempt with job id, packet hash and output dir |
| `output/catering-methods/veloxq/<bundle_id>-<UTC time>/` | One service run: `result.json`, `evaluation.json`, `raw-result.h5`, `ising-input.h5` |
| `output/catering-methods/veloxq/penalty-study-v1/` | Phase E variants (`bundles/build-report.json` has hashes), `sa-plan.json`, `sa-comparison.json` |
| `output/catering-methods/veloxq/penalty-study-v2/` | Local-penalty variants of the low-conflict pools (phase H) |
| `output/catering-methods/veloxq/lowconflict-v1/`, `lowconflict-v1-2048/` | Low-conflict bundles, CP references, witnesses, SA summaries |

### Large files: what was committed and how to restore

- JSON files over 10 MB are gzip assets registered in
  `output/COMPRESSED_EVIDENCE.json`. This includes large `result.json` and
  `evaluation.json` files and the variant and low-conflict bundles. Restore them
  with `node scripts/restore-compressed-evidence.mjs`. Without Node, run
  `python3 scripts/restore_veloxq_evidence.py`, which checks the same SHA256
  values.
- HDF5 files over 5 MB are committed as `<name>.h5.gz` beside their ignored
  original. Restore with `gunzip -k`. The packet hash is in each
  `result.json` under `raw_artifacts.ising_input.sha256`.
- Both rules also appear as explicit paths in `.gitignore`.

### Reproduce offline (no token)

    .venv/bin/python -m pytest -q tests/catering/test_veloxq_adapter.py tests/catering/test_veloxq_penalty.py
    .venv/bin/python -m catering.methods.veloxq_penalty --margins 1 8 --output output/NEW-PENALTY \
        --bundle output/catering-velox-scale-v3/scale-512-qubo.json
    .venv/bin/python -m catering.methods.veloxq_lowconflict --output output/NEW-LOWCONF --widths 512 1024
    .venv/bin/python -m catering.methods.veloxq --bundle <bundle> --output output/NEW-PACKET   # packet + not_run

### Submit and recover (only after a recorded cap)

    .venv/bin/python -m catering.methods.veloxq --bundle <bundle> --allow-external \
        --max-service-jobs <LEDGER TOTAL> --timeout 300 --num-rep 4096 --num-steps 5000
    .venv/bin/python -m catering.run evaluate --bundle <bundle> --samples <dir>/result.json --output <dir>/evaluation.json

A job that ended with `ConnectError` but has a `job_id` was recovered by
`Job.from_id(job_id)`. The result was downloaded and parsed with the adapter's
own `parse_samples`, and the original failure was kept under `recovery` in
`result.json`. This is not yet an adapter option. Adding `--resume-job-id` to
`catering/methods/veloxq.py` (with tests) is the first open task.

## Open questions and suggested next steps

1. **Adapter:** add `--resume-job-id` (see above). Optionally add the SDK's
   `SBMSolver` (Simulated Bifurcation, parameters `discrete_version`, `dt`) as a
   separate method ID. It was never tried.
2. **Why VeloxQ fails at scale:** a valid state needs exactly one choice in each
   of 26 blocks and no active pair among up to 487,167 conflicts. Changing a
   block's choice is a 2-flip move. Candidates not yet tried:
   - a more compact encoding with fewer blocks or programs per block,
   - decomposition into time windows (the scale doc currently advises against
     decomposing; this needs the team's agreement),
   - comparing against XY-mixer QAOA, which preserves one-hot by construction.
3. **Precision:** the backend's internal arithmetic is still unverified. The
   local-uw packets are float32-exact and did not help, which suggests
   precision is not the bottleneck.
4. **Presentation claim:** VeloxQ is a GPU service, not a physical QPU.
   Supported claim: it solves the small shared QUBOs to optimum. On the large
   penalty-dense QUBOs, classical SA/CP-SAT win under every tested setting.
   No hardness or advantage claim follows from one setting per case and no seed
   control.
5. **Decisions for the team:** whether any post-hoc formulation (local
   penalties, low-conflict pools) should become a new frozen shared release.
   Phases E and F show that low-conflict pools let CP-SAT prove optima
   quickly, which may matter more for the classical track than for VeloxQ.
