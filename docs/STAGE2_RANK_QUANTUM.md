# Four-qubit baseline-B QAOA candidate

The structurally compiled four-bit deadline QUBO runs as an actual QAOA gate circuit in classical simulation. All twelve sampled best schedules pass the unchanged official Stage 1 validator with makespan eight. This is a separate research candidate; no official selected Stage 1 artifact was replaced and no physical quantum job was submitted.

Code: `stage2/rank_quantum.py`. Frozen experiment: `output/stage2-search/rank-quantum-final/summary.json`. Reproduce into an empty directory:

```sh
.venv/bin/python -m stage2.rank_quantum --output /path/to/new-empty-directory
```

Requires Qiskit and Qiskit Aer. The recorded versions are Qiskit 2.5.2 and Aer 0.17.2. Every run retains its raw measured counts, OpenQASM 2 circuit, angles, exact basis audit, selected schedule, model/instance/source hashes and solver metadata. Each model directory also contains a frozen copy of its structural proof report.

## What is being solved

This experiment uses the official three-job, three-machine instance, canonical SHA-256 `bb2babdc50eb249b7ad522dedef5e5fdfe35d7991ddbfee5189ea71950a84d41`. The decision is whether a schedule completes by `H=8`; the energy is a feasibility penalty, not the exact makespan function.

The primary SAT-only model is:

`E(a,b,c,d) = 2 + 3b − 2c − d − ab + 2ac − ad − 3bc − bd + 2cd`.

Its six couplers act directly on four logical qubits. The optional cut-weight-LP variant has five couplers:

`E_sparse(a,b,c,d) = 1 + 2b − c + ac − ad − 2bc − bd + cd`.

Both retain all five deadline-feasible machine-order schedules, including a schedule with different orders on the final machine. All other four-bit assignments have positive energy. They are exact only after the certified, deadline-specific presolve described in `docs/STAGE2_RANK_PROBE.md`.

The primary construction used 770 partial-DAG longest-path evaluations, 90 SAT queries and 172 DPLL search nodes, with no complete-schedule labels and no LP during construction. The optional sparse construction adds a twelve-variable cut-weight LP. Both constructions are classical work and their certificates are retained. SAT presolve can itself produce satisfying assignments; no claim is made that quantum computation was necessary to discover a feasible schedule.

## Circuit and validation

Each run prepares `|+⟩⁴`, then applies p layers of the normalized quadratic cost unitary and transverse-X mixer. Cost terms compile to RZ and CX–RZ–CX gates; mixers compile to RX gates. Coordinate search minimizes the exact statevector expected energy, using four starting angle vectors, at most 512 objective evaluations, and seeds 2026, 17 and 83. This optimizer uses energy, not a target list of optimal schedules. It is a simulator-trained circuit, with no hardware training or noise claim.

The exported circuit is independently executed by Qiskit's `Statevector`, whose sixteen basis probabilities must match the separate simulator to absolute error below `1e−12`. The maximum observed discrepancy over twelve runs was `3.89e−16`. Aer then actually samples the measured circuit for 1024 shots, independently of the exact probability calculation.

Every one of the sixteen possible rank samples is expanded through the certified equality decoder, converted to an earliest-start physical schedule, and checked using the unchanged `solver.stage1.validate`. Zero energy must agree exactly with valid makespan at most eight. Raw Qiskit strings use `q3 q2 q1 q0`; the semantic vector is `[a,b,c,d]=[q0,q1,q2,q3]`. The explicit reversal is checked for every observed string.

The selected schedule is the lowest-energy **observed** sample, breaking ties by count and then basis index. There is no exact-answer fallback. All twelve selected samples have energy zero, makespan eight and an empty official-validator error list. A separate exhaustive classical reference also reports optimum eight.

## Measured simulator results

The values below average three angle-search/sampling seeds. Single-shot ideal probabilities come from exact circuit simulation; sampled fractions come from Aer counts. Uniform sampling has exact success probability `5/16 = 31.25%` per shot.

| Model | p | Ideal ground probability, mean | Range across seeds | Sampled ground fraction | Logical CX count | Unrouted depth |
|---|---:|---:|---:|---:|---:|---:|
| SAT-only primary | 1 | 66.07% | 66.07–66.07% | 65.69% | 12 | 18 |
| SAT-only primary | 2 | 77.28% | 70.93–84.94% | 76.60% | 24 | 32 |
| Sparse optional LP | 1 | 70.00% | 70.00–70.00% | 70.05% | 10 | 15 |
| Sparse optional LP | 2 | 81.24% | 76.40–90.84% | 80.96% | 20 | 29 |

The p1 coordinate searches converge to the same angles across the three seeds; these are three sampling runs, not three distinct p1 local minima. The p2 seeds expose optimizer variability. The best individual primary p2 run has ideal ground probability 84.94%; the optional sparse p2 maximum is 90.84%. These maxima are selected-run observations, not expected performance guarantees.

Angle optimization used 143–288 actual objective evaluations per run, below the 512 cap. Runs took approximately 0.02–0.04 seconds each on the local simulator, excluding import and prior compilation costs. Timing is diagnostic only.

## Interpretation and limitations

The useful result is that a fully decoded, exact tiny deadline instance fits four logical qubits with an interpretable structural certificate, and a genuine QAOA circuit increases its ideal single-shot ground-state concentration. This creates a concrete candidate circuit for eventual device connectivity/calibration checks.

It does **not** demonstrate quantum advantage. At equal 1024-shot budget, uniform sampling also finds a valid optimum in every recorded run; its theoretical no-success probability is `(11/16)^1024`, approximately `2.33e−167`. Best-of-1024 makespan therefore provides no meaningful advantage evidence. Exhaustive classical scheduling solves this tiny instance in milliseconds, and structural preprocessing plus simulator angle search performs real classical work.

Four logical qubits alone do not establish ODRA5 execution feasibility. Both coupler patterns need native connectivity/routing assessment; the displayed depths omit physical routing and noise. No backend credentials, QPU calibration or physical success rate was tested. The large Stage 2 factory remains a separate hybrid optimization problem, and this experiment makes no claim that its entire scheduling state fits four qubits.
