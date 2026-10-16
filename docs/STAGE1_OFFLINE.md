# Stage 1 offline preparation

Implemented 2026-10-16. No API key, package installation, GPU or network access is needed for these commands:

```sh
python3 -m unittest discover -s tests -p 'test_stage1.py' -v
python3 -m solver.stage1
```

The second command writes inspectable QUBO coefficients, a variable-to-operation mapping, and independently computed classical reference schedules under `output/stage1-preparation/`. Reference filenames deliberately differ from the required final submission filenames. The 2×2 model has 8 variables at H=4; the 3×3 model has 39 at H=8. Reference makespans are 4 and 8 hours. These are classical references, not quantum or VeloxQ results.

## Formulation

For operation o in a job's ordered chain, define binary x(o,t) at every integer start in `[sum(predecessor durations), H - sum(duration of o and its successors)]`. This removes only starts that cannot complete the chain inside H. Empty windows are retained as an unsatisfied exactly-one constraint through the constant offset.

At fixed H, minimize:

`E = sum_o (sum_t x(o,t) - 1)^2 + sum_machine_conflicts x(a)*x(b) + sum_precedence_conflicts x(a)*x(b)`.

All weights are 1. Exactly-one expansion contributes offset 1 per operation, linear coefficient -1 per variable, and coefficient 2 per pair of starts for the same operation. Capacity terms penalize overlapping half-open intervals of distinct operations on the same machine. Precedence terms penalize each adjacent job-operation pair whose selected starts violate completion order. Every term is nonnegative on binary states, so energy zero is equivalent to a feasible schedule inside H. No additional objective term trades away feasibility. Minimizing makespan requires an outer horizon search; heuristic failure cannot certify an infeasible horizon.

The preparation command chooses H from the tiny-instance exact reference so that we can verify a known feasible encoding. It does not perform VeloxQ horizon search or claim that the reference was found by minimizing the QUBO. The 39-variable result reproduces ordinary organizer-described window pruning; it is not a novel reduction or a smallest-QUBO claim. The organizer's raw count is 72; this implementation constructs the pruned model directly.

The reference enumerates independent processing orders on each machine (4 combinations for A, 216 for B), adds job precedence edges, rejects cycles, and computes earliest starts by longest paths. Any feasible schedule induces these orders; earliest starts cannot worsen its makespan. Thus the reference covers non-permutation schedules too and certifies these tiny-instance optima without relying on the document's permutation assertion. It is not a scalable reference algorithm.

## VeloxQ handoff

`solver.stage1.to_dimod(model)` constructs a `dimod.BinaryQuadraticModel` with explicit `BINARY` vartype. It imports dimod only when called. This optional conversion is prepared but has not been exercised in the current repository environment. Do not send these binary coefficients as unlabeled Ising biases/couplings.

The [official SDK](https://github.com/quantumz-io/veloxq_sdk), checked 2026-10-16, accepts dimod BQMs and uses `VELOX_TOKEN`. Its `VeloxQSolver.sample(bqm)` submits a remote job. No SDK client is instantiated by the offline pipeline. Actual backend options, result decoding, job metadata and service behavior must be checked against the team's connection instructions and a real returned result before claiming integration success.

Remaining work: implement/run the 2×2 quantum algorithm; obtain team VeloxQ access; submit the 3×3 BQM; retain real samples/settings/job provenance; independently validate and export actual required-method schedules. Neither required-method run is complete.

Per the supplied challenge §16, access is requested after the event begins and the team is declared in `#lock-in-teams`. One representative emails `support@veloxq.com`, cc `contact@qaif.org`, with subject `QPoland QUANTUM HACKATHON 2026`. No email is sent by this preparation.
