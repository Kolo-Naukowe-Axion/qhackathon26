# Four-bit rank candidate: offline IQM routing

The isolated baseline-B QAOA circuits compile to the five-qubit IQM Adonis star-topology proxy, with all sixteen logical measurement probabilities preserved after actual measurement-wire mapping and physical-ancilla marginalization. **This is offline compilation, not an ODRA5 execution or current ODRA5 calibration check.**

Runner: `stage2/rank_iqm.py`. Results: `output/stage2-search/rank-iqm-final/summary.json`. Reproduce in the existing separate environment:

```sh
.venv-odra/bin/python -m stage2.rank_iqm --output /path/to/new-empty-directory
```

This imports `solver.odra.compile_candidate` and `classical_probabilities` read-only. No official Stage 1 artifact or runner was changed. It never constructs a provider, authenticates, submits a job, or samples a remote backend.

## Actual proxy compilation costs

Each circuit uses the fixed source angle-search seed 2026 from the earlier QAOA experiment. Eight routing seeds are tried; the existing compiler selects minimum CZ count, then depth, then transpiler seed. Angles are preserved during routing.

| Model | p | Native R | Native CZ | Depth with measurement | Depth before measurement | Preserved ideal deadline probability |
|---|---:|---:|---:|---:|---:|---:|
| SAT-only primary | 1 | 29 | 16 | 32 | 31 | 66.07% |
| SAT-only primary | 2 | 48 | 33 | 62 | 61 | 84.94% |
| Sparse optional LP | 1 | 22 | 13 | 26 | 25 | 70.00% |
| Sparse optional LP | 2 | 40 | 27 | 51 | 50 | 90.84% |

All four circuits contain four final measurements. The backend has five physical proxy qubits, with star edges `(0,2),(1,2),(2,3),(2,4)`. Reported physical circuit width is five; this includes the backend register and does not imply all five qubits carry independent scheduling decisions. The semantic model has four decision bits and no encoding auxiliaries.

The p2 probabilities above belong to the single fixed angle seed. They differ from the three-seed means in `STAGE2_RANK_QUANTUM.md`; they must not replace those means without labeling the source seed.

## Equivalence and retained evidence

For every circuit, logical and routed probabilities are compared over all sixteen classical outcomes. The maximum absolute discrepancy is `1.39e−15` across the four candidates, below the `1e−10` gate. Imported source-circuit probabilities also agree with the earlier Qiskit 2.5.2 experiment to below `1e−12`.

The actual classical-to-physical measurement mapping is saved twice: native circuit wire indices and qubit indices after removing measurements. These can differ because Qiskit can reorder qubit lists when removing classical registers. Reusing the original index order without remapping would give incorrect marginal probabilities.

Each candidate directory retains the logical QASM, native OpenQASM 3, native QPY circuit, original structural model, source QAOA result, native gate/depth/layout report, complete logical/native probability vectors, hashes and package versions. The recorded environment uses Qiskit 2.1.2 and IQM client 35.0.3. QPY artifacts were independently reloaded and their sixteen marginal probabilities rechecked.

The primary structural construction still costs 770 partial-DAG checks, 90 SAT queries and 172 DPLL search nodes. The sparse variant adds its disclosed twelve-variable cut-weight LP. All compilation, presolve and angle training are classical work.

## Remaining hardware questions

These native counts establish a concrete small proxy circuit. Live ODRA5 connectivity, current calibration, allowed native instructions, scheduling, noise and access remain unverified. No hardware success rate follows from exact noiseless probability preservation. Physical access is separately blocked by the existing SSO/service configuration; this experiment does not bypass that dependency.

Uniform sampling already finds a deadline-feasible order at equal 1024-shot budget in the tiny experiment. There is no quantum speedup claim, and no claim that the large Stage 2 factory fits this four-bit model.
