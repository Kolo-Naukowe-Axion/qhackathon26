# QAOA evidence

Method and results: [docs/catering-methods/QAOA.md](../../../docs/catering-methods/QAOA.md).
Simulation only; no QPU or VeloxQ call.

| Path | Content |
|---|---|
| `selection-v1/` | Optimizer/depth selection on TRAIN cases (cell, S0, S1); script and per-row medians |
| `plan-v1.json` | Frozen protocol: settings, budgets, seeds, bundle hashes, adapter source hash |
| `train-v1/summary.json`, `test-v1/summary.json` | Per (case, setup, budget) table with references |
| `train-v1/runs.json`, `test-v1/runs.json` | One row per run (seed): status, evaluations, P(opt), P(valid), best checked tuple |
| `*/manifest.json` | SHA-256 of every per-run file, the plan and the adapter |
| `archives/qaoa-train-v1-runs.tar.gz` | Raw per-run folders for TRAIN (`result.json`, `training.json`, `evaluation.json`) |
| `archives/qaoa-test-v1-runs.tar.gz` | Raw per-run folders for TEST (S2, S3) |

Archive hashes (SHA-256):

    eddc8c73ae8a5571039b5a902061a26203f4e605fc7e6d23701e1810cbdb1aa7  qaoa-train-v1-runs.tar.gz
    e19069047c1bed61505d24f42768b423a44f01b6a6e159cd7a8bc23f1b2a1ca1  qaoa-test-v1-runs.tar.gz

Restore the raw folders next to their manifests and verify:

    tar -xzf archives/qaoa-train-v1-runs.tar.gz
    tar -xzf archives/qaoa-test-v1-runs.tar.gz

Each extracted file's SHA-256 must match `train-v1/manifest.json` / `test-v1/manifest.json`.
