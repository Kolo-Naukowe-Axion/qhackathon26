# Stage 1 local refinement — 16 October 2026

Both remote backends are on user hold. The experiments below used actual local quantum simulation or classical QUBO samples. Their workers reject socket connections. No service token was used, no sample was repaired and no reference answer supplied an initial state or optimized angle.

## Results

| Method | Screening: seeds 0, 1, 2 | Validation: seeds 100–109 | Optimal makespan |
| --- | --- | --- | --- |
| Shared-X QAOA, p=3, 32 restarts | 95.752% valid | not selected | 4 h |
| Shared-X QAOA, p=5, 16 restarts | 99.723% valid | not selected | 4 h |
| Independent-X QAOA, p=3, 16 restarts | 100% valid | 40,960/40,960 (100%) | 4 h |
| Geometric annealing, 2,000 sweeps | 94.792% valid | not selected | 8 h |
| Geometric annealing, 8,000 sweeps | 98.372% valid | not selected | 8 h |
| Linear annealing, 32,000 sweeps | 99.805% valid | 5,110/5,120 (99.805%) | 8 h |

Every screening/validation run found an optimum. Quantum runs use 4,096 measured shots; classical runs use 512 reads. Screening and validation reuse the official instances, with different optimization/sampling seeds; they are not tests on unseen scheduling problems. All retained samples, including invalid ones, contribute to the percentages.

The independent-X mixer has one beta per qubit and layer. At p=3 it has 15 trainable angles, versus 10 for the old shared-X p=5 circuit. Both optimize mean QUBO energy from actual Qiskit statevectors. The new circuit has 12 RZZ cost gates versus 20, a 40% reduction, but its extra parameters and sixteen restarts increase classical training work. Median quantum validation time was about 7.18 s; classical validation time about 2.11 s on this Mac. Timing includes the solver work documented in each run and is not a cross-device benchmark.

The quantum validation ideal feasible probabilities were within floating-point error of one. This and the observed 100% rate describe this tiny noiseless simulator instance only. The minimum classical validation rate was 509/512 (99.414%); the 99.5% selection target was for the mean, not every seed. These results establish neither quantum advantage nor physical-device reliability.

## Selection and evidence

Twelve settings were compared in `output/stage1-local/search-01/`; six cooling-schedule follow-ups in `output/stage1-local/search-02/`. Both have research notes, JSON summaries, a TSV, all actual run evidence and a progress plot. Non-improvements remain recorded and were not promoted. Screening used a 0.1 percentage-point minimum improvement; 64,000 linear sweeps yielded only one extra valid screening sample over 32,000 across 1,536 reads, so 32,000 was retained.

Ten new seeds confirmed the selected settings in `output/stage1-local/validation-quantum/` and `output/stage1-local/validation-anneal/`. Optimizer traces in this experiment archive are losslessly compressed as `optimization-history.json.gz`; counts and model/sample JSON remain directly readable.

The selected seed-2026 runs were freshly regenerated in `output/stage1-local-ready/`. A returned 4,096/4,096 valid shots; B returned 511/512 valid samples. The root schedule files and `output/stage1-selected.json` identify these runs. Previous `output/stage1-ready/` evidence remains intact.

The quantum verifier now reconstructs the state from the saved mixer/angles and checks expected energy, ideal feasible probability, cost scale, raw counts and shot totals. It also checks model/instance hashes and independently validates every decoded schedule, as before. Tampering with angles or counts is covered by rejection tests. Evidence consistency is not external authentication of an execution.

## Reproduction

```sh
.venv/bin/python scripts/prepare-stage1.py --output output/new-stage1 --export-final
.venv/bin/python -m solver.verify --run output/new-stage1/qaoa-2x2
.venv/bin/python -m solver.verify --run output/new-stage1/anneal-3x3
```

The default preparation excludes both remote adapters. It does not create SDK packets. Historic packet preparation is available only through explicit local options; do not submit to either service while the user hold applies.

To repeat the experimental search, choose fresh directories:

```sh
.venv/bin/python -m solver.refine --output output/new-search-01
.venv/bin/python -m solver.refine --phase anneal-followup --output output/new-search-02
.venv/bin/python -m solver.refine --worker 3 --seeds 100 101 102 103 104 105 106 107 108 109 --output output/new-validation-quantum
.venv/bin/python -m solver.refine --worker 14 --seeds 100 101 102 103 104 105 106 107 108 109 --output output/new-validation-anneal
```

The parent search enforces a five-minute timeout per candidate. Plotting is optional (`requirements-experiments.txt`); solver requirements remain pinned separately. Seeds used in validation are listed explicitly and the reference is computed only after sampling for the acceptance guard.
