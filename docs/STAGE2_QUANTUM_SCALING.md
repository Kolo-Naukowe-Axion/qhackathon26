# Simulator frontier beyond the hardware profile

`stage2/quantum_scaling.py` is an optional, separate NumPy CPU implementation. The original five-total-bit hardware-target profile in `quantum.py` and the physical factory/dispatcher are unchanged. This module accepts the existing `QUBO` object, including every encoded slack variable, with an explicit total-bit cap of at most24. It neither truncates actions nor silently falls back to a different solver.

```python
from stage2.qubo import build_qubo
from stage2.quantum_scaling import Budget, select_qaoa
q = build_qubo(candidates, conflicts, capacities)
result = select_qaoa(q, seed=0, layers=2, shots=1024,
    budget=Budget(max_bits=24, memory_mib=1536, seconds=180,
                  evaluations=32, reference_core_bits=16))
```

The standalone CLI also times `build_qubo`; caller-side candidate generation remains outside its scope. All factory legal-action construction and crew enumeration must be charged separately in any end-to-end comparison.

## Correctness and limits

The state starts in `|+>^n`. Each layer applies `exp(-i gamma (QUBO-offset)/scale)` and then `exp(-i beta sum X)`. The offset changes only a global phase. Coefficients use the frozen upper-triangular-once convention. Basis-index bit `i` is variable/qubit `i`; printed count strings run from the highest bit to bit0. Energies use float64, amplitudes complex128. Chunked butterflies batch small strides and bound large-stride scratch allocations.

The nine tests in `tests/stage2/test_quantum_scaling.py` compare full complex amplitudes against the frozen scalar simulator for each size1–5, including two layers and a slack-bearing QUBO. An independent three-bit dense diagonal-plus-Kronecker-Rx calculation checks amplitudes up to the known global phase; an analytic one-bit expression checks gate signs. Tests separately verify upper-triangular energies, endian order, resource/conflict classification, reproducible counts, total-bit and preallocation guards, deadline/evaluation exhaustion, and an observed suboptimal sample that stays unchanged when the exact reference is disabled.

A numerical-array allowance of `64 * 2**n + 16MiB + 128*min(2**n,chunk_states)` is checked before allocating. This conservative allowance covers numerical workspaces, rather than serving as an OS process-memory limit; Python/runtime baseline and retained output objects are additional. Default cap20 and allowance1024MiB require an explicit higher allowance to run24bits. The elapsed deadline is cooperative and checked between chunks. Exceeding any budget raises `BudgetExceeded`; it is not reported as a successful QAOA run. One final reconstruction evolution is separately reported in addition to all charged optimization evaluations. No GPU, noise model, hardware calibration, transpilation, QPU submission or physical quantum execution is involved.

## Evidence and costs

The returned result retains full QUBO coefficients, candidate/resource mapping, hashes of the problem and implementation sources, all optimized angles and improvements, precision/sign/endian conventions, logical gate counts, seeds, budgets, actual shot counts and classified observations. The full probability vector is hashed without serializing millions of entries. Ideal feasibility, exact-pool reward hit, zero-penalty and QUBO-ground probabilities are distinct; slack consistency is not mistaken for physical core feasibility.

Angle search uses a bounded seeded random initialization and coordinate refinement on exact noiseless statevector expectation. This optimizer is a prototype, without a convergence guarantee; small-budget poor results do not establish an intrinsic QAOA limitation. Its simulator expectation computation enumerates the full basis. The best feasible observed sampled core is returned. If no feasible core was observed, a classical greedy repair is marked explicitly. The independent exact reference never chooses the QAOA output.

Controls retain equal-shot uniform counts, independently enumerated exact core subsets (only up to the declared core cap), and seeded single-flip SA, including its greedy warm start, sweeps, restarts and repair. Uniform gets the same number of sampled bitstrings. Exact, SA and QAOA do different amounts of computation, all timed separately. This is not a claim of equal computational budgets or quantum speedup.

## Measured CPU kernel frontier

Evidence: `output/stage2-search/quantum-scaling-prototype/kernel-{16,20,22,24}.json`, with the retained `kernel-benchmark.py`. These are sparse ring-conflict synthetic QUBOs with no slack, deterministic rewards and fixed angles; they measure kernel scaling, rather than factory performance or angle-search quality. Each size was run in a separate process, with numerical-library thread environment variables set to1. Times are single local measurements and are not confidence intervals.

| Total bits | Energy preprocessing | One-layer evolution | Two-layer evolution | Peak process RSS |
|---:|---:|---:|---:|---:|
|16|0.003s|0.003s|0.007s|38MiB|
|20|0.049s|0.071s|0.136s|71MiB|
|22|0.301s|0.372s|0.702s|147MiB|
|24|1.383s|1.671s|3.003s|451MiB|

An earlier kernel run, retained under `kernel-before-metadata-freeze/`, measured24-bit p1/p2 at0.880/1.737s with443MiB RSS and a two-layer norm difference below`5e-13`. The table uses the final frozen-source rerun. These local timings vary with concurrent load and are diagnostic measurements, not matched speed claims. These CPU measurements give no reason to spend GPU time on this prototype yet. Dense cost preprocessing, repeated angle search, larger circuits and serial replanning remain separate scaling costs.

## Checked expanded-crew pools

Methodology supplied retained JSON fixtures from independently checked complete factory traces at `output/stage2-search/selector-domain-training-audit/expanded-pool-fixtures/`. Each core bit specifies an operation plus a complete worker assignment. Selected and committed candidate/worker identities were checked by that experiment. Their classical candidate pool remains a restricted controller domain, rather than a global factory encoding. These fixtures use the earlier batch-bonus reward. The later `selector_reward.py` no-batch/priority-lex ablations changed that objective and substantially improved classical downstream results; these saved pools must not be described as the strongest current scheduling formulation.

The bounded pilot protocol is `quantum-scaling-prototype/cohort-protocol.json`: actual pools11bits=6core+5slack,19bits=13core+6slack,23bits=14core+9slack; layers1/2; seeds0/1/2;32 angle evaluations and1024shots each. Every run and control is retained, including weak outcomes. No reserved final evaluation tape was executed. The current prototype only solves those fixed saved pools, without feeding its selections into new factory runs.

The first23-bit p1/seed0 run took16.99s and sampled reward666.67 against exact775.44; equal-shot uniform obtained698.25 and SA775.44. Exact core enumeration took0.00086s; SA took0.00453s. Its ideal exact-reward probability was0.0053%, below uniform0.0183%. This example confirms feasible simulation beyond five bits while providing negative evidence for the tested solver settings. End-to-end advantage cannot be inferred from a probability change or an occasional best-shot pool optimum.

All18 runs finished in166.0s summed end-to-end CPU wall time, with no repair. The complete `cohort-summary.json`, concise `aggregate.json`, input/source snapshots and every result are retained under `quantum-scaling-prototype/`.

| Total bits | Layers | QAOA exact-reward hits | Equal-shot uniform hits | SA hits | Median QAOA total time |
|---:|---:|---:|---:|---:|---:|
|11|1|3/3|3/3|3/3|0.024s|
|11|2|3/3|3/3|3/3|0.030s|
|19|1|3/3|1/3|3/3|1.049s|
|19|2|3/3|1/3|3/3|1.879s|
|23|1|1/3|1/3|3/3|17.713s|
|23|2|0/3|1/3|3/3|33.550s|

Uniform uses the same counts for the same seed at both depths, so the two rows are not independent uniform trials. These are three fixed pools and three sampling/optimizer seeds, not18 independent factories, an out-of-sample test, or a statistical advantage result. The19-bit probability amplification and its observed sample hits are useful algorithm diagnostics; the exact14-core reference at23bits still costs about0.0009s, and SA about0.0048s. The bounded QAOA implementation is not competitive with these classical controls in this pilot. More layers did not improve the23-bit best-shot result under the declared small angle budget; stronger optimization is not ruled out.

`independent-record-audit.json` additionally replays all retained sample energies/feasibility and observed-selection identities, checks both count totals/source hashes, and recomputes all three reference optima with the original scalar core enumerator. All checks pass. Numerical implementation SHA-256: `126004e765bbe78c4a9e2fe6797077a0c68fc1b1928210641f2d21ddd10c5273`.

Production outcomes, a globally encoded factory optimum and hardware advantage remain unclaimed.
