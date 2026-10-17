# Stage 2: bounded quantum action selection

`stage2/quantum.py` implements a real QAOA circuit algorithm on **at most five total encoded variables**, including slack. Its current execution is a classical statevector simulation. No ODRA5 job is launched by this module, and no VeloxQ call is made.

The input is the actual factory's frozen concurrent-start QUBO. The surrounding classical simulator supplies legal candidate operations, conflicts and resource capacities. The sampled selection can be returned to the dispatch controller as real scheduling actions. This does not encode the entire factory into five qubits.

## Integration API

```python
from stage2.qubo import build_qubo
from stage2.quantum import select_qaoa

q = build_qubo(candidates, conflicts, capacities)
result = select_qaoa(q, seed=seed, layers=1, shots=1024)
selected_candidate_ids = result["selected"]
```

The result follows the `stage2.qubo.select` structure: selected IDs, reward, explicit feasibility, raw bits/energy, repair status, independent exact reference, QUBO summary and elapsed time. It additionally retains the complete QUBO coefficients/candidate mapping, circuit, optimized angles, actual counts, probabilities, optimizer budget, uniform reference and hashes.

If the QUBO has more than five **total** bits, it is solved by explicitly labeled classical simulated annealing instead. The result records `method: sa`, `requested_method: qaoa`, `quantum_algorithm_simulated: false`, and the cap/fallback reason. The sampler never silently drops candidates or slack to fit the device. An upstream candidate-pool restriction is a separate classical decision and must be disclosed.

An empty QUBO returns `classical_empty_pool`; it is not counted as a quantum circuit. Simulator results report `quantum_executed: false`, `physical_quantum_executed: false`, and `quantum_algorithm_simulated: true`.

## Circuit and objective

The algorithm starts in `|+>^n` and alternates:

`exp(-i gamma H_cost / scale)` and `exp(-i beta sum_i X_i)`.

The cost is the QUBO energy, using the repository's upper-triangular-once convention. With `x_i = (1-Z_i)/2`, a linear term contributes `-a_i/2` to its Z field and a pair term contributes `b_ij/4` to ZZ and `-b_ij/4` to each endpoint's Z field. Constants affect only global phase. Circuit export uses H, RZ, CX and RX; a ZZ rotation is decomposed as CX/RZ/CX.

The ansatz follows the original [QAOA construction](https://arxiv.org/abs/1411.4028). Rotation angles follow the [documented RZZ exponential convention](https://quantum.cloud.ibm.com/docs/en/api/qiskit/qiskit.circuit.library.RZZGate).

The default optimizer is deterministic seeded coordinate search with **256 maximum exact expectation evaluations**, three starts, and one QAOA layer. Two layers are supported. Optional `optimizer="scipy"` uses L-BFGS-B if SciPy is installed and explicitly falls back to coordinate search if unavailable. This is bounded local angle optimization, not a guarantee of globally optimal angles.

Training uses exact **noiseless simulator expectations**; it is not shot-noisy hardware training. Sampling then performs a fresh seeded 1,024-shot Born draw from the optimized circuit. The optimizer never uses the exact optimal selection to select returned actions.

## Feasibility and postselection

Physical core feasibility is checked with `QUBO.feasible(selected_core)`. It is **not** inferred from energy zero. A feasible action selection generally has negative reward energy, while a feasible core with inconsistent slack can have positive penalized energy.

The output selection is the highest-reward **observed feasible sampled core**, with deterministic tie-breaking. The independent exact reference is evaluated afterward for reporting; it does not supply the returned actions. If no feasible core is observed, classical greedy repair is explicit in the result.

Separate quantities are reported for:

- Feasible core probability.
- Exact reward hit probability within this frozen candidate pool.
- QUBO ground-state probability, including slack consistency.
- Zero-penalty encoding probability.
- Actual shot fractions and raw bitstring counts.

Basis index bit `i` is variable/qubit `i`. Raw count strings read `q[n-1] ... q[0]`, so decoding reverses the printed string to recover the variable vector.

## Actual local factory example

The measured `selector-pilot-sa.json` trace supplied a five-variable, six-coupler concurrent-start decision at tick 283. This pool already fits five qubits; no candidate trimming was needed. This is an archived local decision, separate from the later complete checked QAOA factory run. Its source artifact SHA-256 is `821d42b1d269df45d123d97518a49efc21bdb7cd7aa36e81e3f9101c02a6be58`; its numerical instance SHA-256 is `fad56b11381c030d6f5fc40c39bb918675d8931fd140be7b168cbbebb2f144ca`. The captured decision and provenance are preserved with the local experiment artifacts. Rebuilding its QUBO and running the simulator with seed 283 and 1,024 shots produced:

| Quantity | QAOA p=1 | QAOA p=2 |
|---|---:|---:|
| Ideal feasible core probability | 85.28% | 95.17% |
| Ideal exact pool-reward hit probability | 8.72% | 13.63% |
| Observed exact-reward shot fraction | 8.30% | 13.96% |
| Selected sampled actions | C0 + C4 | C0 + C4 |
| Selected reward / exact pool optimum | 496.9697 / 496.9697 | 496.9697 / 496.9697 |
| Logical circuit depth before measurement/routing | 18 | 32 |
| Approximate local elapsed time | 2.4 ms | 6.6 ms |

These are **local simulator measurements on one factory decision**, not end-to-end factory quality, hardware measurements, or evidence of quantum advantage. Updated exported evidence, including source/instance hashes and the captured decision, was saved under `/private/tmp/stage2-qaoa-factory-v2-tick283-p1/` and `...-p2/` during development; persistent experiment artifacts should be retained by the main experiment runner. The audit was rerun after exact integer-GCD resource normalization was added to the QUBO builder; all checks passed and these probability values were unchanged.

The matching uniform distribution has an exact-pool-reward hit probability of **3.125%**. With 1,024 shots, even uniform sampling is overwhelmingly likely to observe an optimal five-bit assignment. Therefore "best sampled solution equals the exact optimum" is a weak quality claim here. The module reports the equal-shot uniform baseline and its actual best sampled feasible reward. Local probability amplification can be discussed; whole-factory speedup or quantum advantage cannot be inferred.

## Reproducibility and audit

`save_result(result, new_empty_directory)` saves full `result.json`, `problem.json`, actual `raw-counts.json`, and `circuit.qasm`. Existing evidence is never overwritten. The complete QUBO and the QASM each have SHA-256 hashes.

For one captured decision:

```sh
python3 -m stage2.quantum /path/to/decision.json --layers 1 --shots 1024 --seed 283 --output /path/to/new-run
```

The input JSON contains `candidates`, `conflicts`, and `capacities`, as recorded in a factory `qubo_decisions` entry.

Mechanical audit:

```python
from stage2.quantum import audit
print(audit(verify_qiskit=True))
```

The completed audit checked 20 random QUBOs, 468 basis-state Ising energy identities, and 40 independent Qiskit probability comparisons across one/two layers and one–five qubits. It also checked slack-inclusive fallback, seeded count reproducibility, feasibility independent of energy zero, and a one-shot case returning a suboptimal sample without borrowing the exact answer. All passed. Qiskit probability discrepancies were below `1e-12`.

## ODRA5 boundary

Five logical variables fit the qubit budget. That alone does not establish hardware feasibility: device connectivity, native gates, routed depth, calibration, queue status and bit mapping still require verification. The exported circuit has **not** been transpiled or submitted to ODRA5. A later hardware comparison should retain the same QUBO, angles, shot count and decoding rules, and identify simulation-assisted angle training explicitly.

The classical controller still handles complete physical state, omitted candidate alternatives, transport, maintenance and replanning. A five-qubit selection contributes one restricted scheduling decision. It is an honest hardware-integration target, not a claim that five qubits solve the full factory.
