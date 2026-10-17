# Observed final CPU-simulation tradeoffs

All contexts use a 96-hour factory horizon. ★ marks the preselected classical controller; no final reselection. These are weighted episode process CPU seconds, not normalized speedups. Actors are nested within 256 environments.

## 12 initial orders (+ realized urgent orders)

| Exact method ID | CPU s/episode | Mean missing | Weighted fulfilled | Actors |
|---|---:|---:|---:|---:|
| `static-grid-12` ★ | 3.331 | 0.07500 | 94.984% | 1 |
| `static-matched18-12` | 2.854 | 0.08328 | 92.734% | 1 |
| `original-strong-12` | 3.174 | 0.07453 | 95.219% | 1 |
| `ppo6-2026-12` | 2.705 | 0.03031 | 96.969% | 1 |
| `ppo6-2027-12` | 2.691 | 0.03031 | 96.969% | 1 |
| `cem6-2026-12` | 3.015 | 0.04906 | 96.812% | 1 |
| `mpc-4future-12` | 156.190 | 0.03766 | 96.969% | 1 |
| `no-batch-sa-12` | 3.445 | 0.11828 | 92.812% | 3 |
| `no-batch-qaoa-12` | 3.652 | 0.15031 | 91.818% | 3 |
| `no-batch-uniform-12` | 3.484 | 0.14005 | 91.146% | 3 |

## 16 initial orders (+ realized urgent orders)

| Exact method ID | CPU s/episode | Mean missing | Weighted fulfilled | Actors |
|---|---:|---:|---:|---:|
| `static-grid-16` | 3.161 | 2.60297 | 11.344% | 1 |
| `static-matched18-16` | 3.342 | 2.41938 | 12.594% | 1 |
| `original-strong-16` | 2.518 | 3.45734 | 0.938% | 1 |
| `ppo6-2026-16` | 3.346 | 2.41938 | 12.594% | 1 |
| `ppo6-2027-16` | 3.355 | 3.15453 | 6.625% | 1 |
| `cem6-2026-16` ★ | 3.411 | 2.69063 | 8.797% | 1 |
| `mpc-2future-16` | 113.182 | 2.30141 | 17.406% | 1 |
| `no-batch-sa-16` | 2.691 | 3.36807 | 0.792% | 3 |
| `no-batch-qaoa-16` | 2.957 | 3.27161 | 2.245% | 3 |
| `no-batch-uniform-16` | 2.706 | 3.23646 | 1.880% | 3 |

## 24 initial orders (+ realized urgent orders)

| Exact method ID | CPU s/episode | Mean missing | Weighted fulfilled | Actors |
|---|---:|---:|---:|---:|
| `static-grid-24` | 10.631 | 10.39531 | 0.000% | 1 |
| `static-matched18-24` | 3.751 | 11.93922 | 0.000% | 1 |
| `original-strong-24` | 2.706 | 11.59922 | 0.000% | 1 |
| `ppo6-2026-24` | 2.750 | 11.59922 | 0.000% | 1 |
| `ppo6-2027-24` | 2.750 | 11.59922 | 0.000% | 1 |
| `cem6-2026-24` ★ | 3.766 | 10.02094 | 0.000% | 1 |
| `mpc-4future-24` | 255.350 | 11.26766 | 0.000% | 1 |
| `no-batch-sa-24` | 2.890 | 11.67688 | 0.000% | 3 |
| `no-batch-qaoa-24` | 3.175 | 11.67797 | 0.000% | 3 |
| `no-batch-uniform-24` | 2.916 | 11.67906 | 0.000% | 3 |

Fit costs below are shared across all three loads and are shown once per checkpoint; they are neither episode CPU nor uniquely attributable total development cost.

| Shared checkpoint | Fit episodes | Reused VAL episodes | Fit wall s | Configured workers |
|---|---:|---:|---:|---:|
| ppo6 / fit 2026 | 9048 | 816 | 1200.165 | 32 |
| ppo6 / fit 2027 | 9368 | 816 | 1205.536 | 32 |
| cem6 / fit 2026 | 9096 | 720 | 1216.086 | 32 |

Source hashes, exact definitions, runtime packages/SLURM IDs, independent mean-recomputation checks and as-of shared accounting are retained in `report.json`. No prior search or training is assumed free. The families have different action domains and outer controls; this is not an equal-budget tournament. Historical source versions are retained per manifest. No bootstrap or simulator was run to make this table.
