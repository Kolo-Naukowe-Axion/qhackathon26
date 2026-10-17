# Stage 1 readiness — 16 October 2026

> Superseded selection (17 October): the current runs use 1/3-bit order QUBOs and QAOA for both instances. See [current formulation, experiments and limits](STAGE1_COMPACT.md) and `output/stage1-selected.json`. The time-indexed results below remain retained comparison evidence.

Both mandatory computational method requirements have been exercised locally. This does not claim a completed submission, VeloxQ integration, or physical ODRA5 execution.

**Current user instruction: use neither ODRA5 nor VeloxQ; continue locally.**

| Instance | Actual method | Variables/qubits | Makespan | Feasible samples |
| --- | --- | --- | --- | --- |
| instance_2x2 | QAOA p=3, independent X mixer angles (Qiskit Aer) | 4 | 4 h | 4096/4096 (100%) |
| instance_3x3 | Classical QUBO annealing, linear cooling, 32,000 sweeps | 39 | 8 h | 511/512 (99.80%) |

Independent exhaustive machine-order enumeration gives optima 4 h and 8 h. Actual selected samples meet both optima and pass independent Python and browser interval checkers. The required root JSON files contain these actual method labels.

The complete reproduction command is `.venv/bin/python scripts/prepare-stage1.py --output output/new-stage1`. Current run selection: `output/stage1-selected.json`, pointing to `output/stage1-local-ready/`. Earlier evidence is retained.

Eighteen settings were screened on three seeds each. On ten new seeds, QAOA gave 40,960/40,960 valid measurements and classical annealing gave 5,110/5,120 valid samples. Every validation run returned its instance's exact optimum. The QAOA circuit uses 12 logical RZZ gates instead of the old circuit's 20, with more classical optimizer parameters/restarts. No hardware performance or generalization claim follows. See [STAGE1_REFINEMENT.md](STAGE1_REFINEMENT.md).

## Retained evidence

- Per run: QUBO coefficients, variable mapping, instance/model/source hashes, versions, sample counts/energies/violations, official schedule and replay.
- QAOA: circuit QASM, optimizer settings/statuses/history, final angles and actual Aer measurement counts. The verifier reconstructs expected energy/probability and reconciles raw shot counts. This is a quantum algorithm on a simulator, as allowed for A.
- Encoding audit: all 512,000 operation-start assignments at H=8 agree with independent constraints in both encodings; 13 are feasible. Invalid domain-wall states are addressed by a penalty proof and separate exhaustive small-instance tests.
- Nineteen core Python tests pass in the solver environment; the two optional IQM compilation tests also pass in the separate IQM environment. Eighteen viewer/manual tests and the static build pass, including exact matrix coefficients and all 256 one-hot energies. Coverage includes the circuit, decoder, SDK boundaries without service calls, and default preparation's exclusion of remote adapters.

## Initial VeloxQ choice

Use one-hot at H=8 as the first service candidate: 39 variables, coefficients of magnitude at most 2, 512 repetitions and 2,000 steps. These service budgets are starting values, not remote-tuned settings. The alternative domain-wall model has 30 variables, safe wall penalty 10 and larger coefficients.
- Local onehot: 10/10 seeds returned an optimum; mean feasible-sample rate 95.08% at 256 reads × 2000 sweeps.
- Local domain-wall: 10/10 seeds returned an optimum; mean feasible-sample rate 91.88% at 256 reads × 2000 sweeps.

**User hold: do not use VeloxQ yet.** No quick test, upload or service job has been made. The token must remain in the execution environment, outside code and commits. Local encoding tests do not establish remote quality, quota, latency or backend availability.

## ODRA5 hardware upgrade

Four logical qubits fit the five-qubit device. Native star compilation and local Adonis-noise experiments are prepared. The p=3 proxy currently offers a useful depth/quality compromise (39 CZ, depth 73, about 31.0% feasible at 1,024 proxy shots), with p=1 as a shallower comparison. These are not ODRA5 calibration or physical measurements.

The existing SSH account and Axion CPU association are verified. An allocated compute node reached ODRA5 and received HTTP 401; the login node redirected away. IQM 35.0.3 and a personal IQM token are required even when executing through SSH. The token-free client bundle and dedicated Python 3.12.13/IQM 35.0.3 environment are installed and verified at `~/qhackathon26-stage1`. The local dashboard still redirects to e-science, so token creation/live execution remains pending a working dashboard access route.

Hardware work is paused at the user's request. Use the verified local results. Stage 2, video, human review and submission remain separate work.
