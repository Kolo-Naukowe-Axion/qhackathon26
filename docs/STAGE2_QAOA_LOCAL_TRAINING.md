# Local QAOA training — 17 October 2026

This study improves angle training for the existing whole-recipe QAOA bridge,
using only this Mac. Both known synthetic 32-operation recovery fixtures retain
all eight component groups and the makespan register: 36 logical qubits and
262,144 invariant-sector amplitudes at cap4. The finite constructive trajectory
pools are unchanged. This does not expand the represented scheduling domain or
improve the already optimal classical constructive schedule.

## Implementation

`stage2/qaoa_training.py` supplies an analytic reversible-adjoint gradient for
all 2p gamma/beta angles of the existing ordered XY-chain circuit. The reverse
pass reconstructs forward states by applying inverse gates; it retains two
sector vectors rather than a tape of all intermediate states. The forward
simulation, W-state initialization, logical register, cost Hamiltonian, resource
penalties and QASM export are unchanged.

L-BFGS-B fits expectation or CVaR using exact classical simulator probabilities.
The CVaR derivative accounts for the moving quantile. Gamma is not wrapped at
2pi, because the coefficient-scaled cost spectrum does not generally have that
period. Every completed objective/gradient evaluation is counted and the
explicit per-start budget is enforced even inside a line search. A gradient
call includes forward and reverse work and is more expensive than a scalar
objective evaluation.

The optimizer never receives an exact-solution mask, argmin or CP solution.
The historical p2 angles provide one declared warm start. Training uses the
full exact classical energy table, including sorting for CVaR; preparing that
table already reveals the optimum to an observer. This remains classical
simulation and is not a scalable quantum implementation.

## Depth search

The frozen study uses the two existing cap4 pools, depths2/4/8/12, four starts
per case/depth, alpha0.25 and at most256 adjoint evaluations per start.
The first start extends the previous selected circuit with small-angle layers;
the second perturbs it; two additional starts use seeded random angles.
Selection minimizes the declared CVaR objective. Exact-hit probabilities are
computed after fitting and never select a circuit. Ten512-shot Born replicas
per fit use fresh sampling seeds101–110. They are replicas of a distribution,
not independent manufacturing problems.

The selected CVaR circuits are:

| Known fixture | Historical p2 optimum probability | Selected depth | Trained optimum probability |
|---|---:|---:|---:|
| Heat outage |0.625684%|12|24.857051%|
| Replacement heat capacity |1.360254%|4|26.059178%|

The shallowest circuit within1e-9 of the best CVaR loss starts the subsequent
polishing stage. The replacement p8/p12 fits do not improve that saturated
alpha0.25 objective. Failed random starts, including negligible optimum
probability, remain in the evidence. The outage p12 selected fit is a random
start, demonstrating why a warm-start ladder alone is insufficient.

The sweep contains32 completed fits and1040.483111 retained fit CPU seconds.
An intentional chat interruption stopped in-flight work. Resume retained all
completed trials, checked that model/training sources and inputs were unchanged,
and reran missing trials. The orchestration code gained resume support, so the
original report's broad `source_stable` is false; its
`model_and_training_source_stable` is true. Original and resumed runner sources
are both retained. Interrupted in-flight CPU is unmeasured. The resumed
invocation takes272.863860 seconds; this is not the entire experiment's wall
time. Separate exploratory pilots retain another115.699665 fit CPU seconds.

## Broader-tail polishing and validation — complete

The follow-up increases alpha through0.5,0.75,1.0, with two starts per case/stage
and384-evaluation caps. Final export minimizes the final expectation objective,
without choosing on optimum-hit probability. A higher hit probability from a
CVaR variant remains separately reported even if the expectation selection is
worse by that metric.

All12 polishing fits completed in388.935 seconds with unchanged source hashes.
Final expectation-trained optimum probabilities are18.303187% for outage and
25.758412% for replacement. Broader tails do not monotonically improve the
optimum-shot metric: the best observed variant is outage alpha0.25 at24.857051%
and replacement alpha0.5 at27.507555%. These are development comparisons across
predeclared objectives, not a held-out estimate of selecting the best variant.
All four variants are exported separately with their training histories.

Independent36-qubit dense replays have amplitude error below5e-16. Four18-qubit
full-Hilbert circuit replays have probability error below7e-15 and no observed
sector leakage. All80 known-pool selected returns (two cases ×four variants
×ten512-shot replicas) are valid restricted-pool optima. Logical transpilation
gives5316CX gates/depth1338 for the outage p12 circuit and1756CX/depth452 for
the replacement p4 circuit, before hardware connectivity or noise.

The final expectation angles transfer without additional fitting as follows:

| Case / fresh parent seed | Logical qubits | Transferred optimum probability | Fresh historical p2 control | Optimal512-shot returns |
|---|---:|---:|---:|---:|
| Outage /20181 |35|2.218059%|0.110627%|10/10|
| Outage /30181 |36|3.091718%|0.067633%|10/10|
| Replacement /20181 |36|22.824597%|1.048371%|10/10|
| Replacement /30181 |37|7.425522%|0.323048%|10/10|

Transfer concentration drops substantially on some pools. SA also returns the
restricted optimum in all12 control runs. These results support pool-specific
probability concentration, not a new industrial-instance generalization or
classical runtime advantage. Retained depth/polish fit CPU totals at least
1797.6 seconds, excluding115.7 exploratory fit CPU seconds and unmeasured
interrupted in-flight work. The independent audit takes18.630seconds;
its exact time and manifests are retained in its report.

The final generated summary is
[output/qaoa-local-summary-v1/report.md](../output/qaoa-local-summary-v1/report.md).
Its JSON records shot counts, ideal independent-shot requirements, all fit
comparisons and fresh-pool transfer, including failures. The independent audit
uses a separate dense per-component matrix implementation for the36-qubit
sector, literal QUBO energy spot checks, logical QASM parsing/transpilation,
and full-Hilbert Qiskit replay of the same trained angles on18-qubit cap2
circuits. The latter does not claim full-Hilbert replay of36 qubits.

Fresh parent-generation seeds20181/30181 create four new cap4 pools on the same
two physical problems. Their columns are saved before the transferred circuit
is evaluated. Angle transfer uses the new coefficient scale and no further fit.
A newly trained historical64-evaluation p2 method, uniform sampling probabilities
and32-replica/256-sweep one-hot SA provide separate controls. These fresh pools
are not held-out physical manufacturing instances. The original complete-model
schedule checker checks every selected valid return; invalid measured returns
remain recorded.

## Reproduction

The installed `.venv-odra` has Python, NumPy2.4.6, SciPy1.17.1 and Qiskit.
Despite its name, it is used here only as a local Python environment. No ODRA,
VeloxQ, VPN, physical QPU, external API, paid compute, deployment or publishing
is used. The Mac reports15 logical CPU cores and48GiB RAM; the campaign uses
four local worker processes with numerical-library threads restricted to one.

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
  .venv-odra/bin/python -m stage2.qaoa_campaign \
  --output output/NEW-QAOA-DEPTH --workers 4 --evaluations 256 \
  --depths 2 4 8 12 --starts 4
# Add --resume with the identical configuration to continue an interrupted run.
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
  .venv-odra/bin/python -m stage2.qaoa_polish \
  --campaign output/NEW-QAOA-DEPTH --output output/NEW-QAOA-POLISH
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  .venv-odra/bin/python -m stage2.qaoa_audit \
  --campaign output/NEW-QAOA-DEPTH --polish output/NEW-QAOA-POLISH \
  --output output/NEW-QAOA-AUDIT
.venv-odra/bin/python -m stage2.qaoa_report \
  --campaign output/NEW-QAOA-DEPTH --polish output/NEW-QAOA-POLISH \
  --audit output/NEW-QAOA-AUDIT --output output/NEW-QAOA-SUMMARY
```

`stage2/requirements-qaoa-fit.txt` records optional fitting dependencies.
The core Stage2 environment remains separate; no package installation was
needed. Tests in `tests/stage2/test_qaoa_training.py` compare gradients against
central finite differences at multiple depths/tail fractions, verify degenerate
quantiles, best-observed selection and the hard evaluation budget. Existing
assignment, recipe and column tests retain physical-domain checks.

The historical baseline has a smaller training budget and shallower circuits.
Probability concentration is not runtime advantage, hardware noise tolerance,
or improved schedule quality. Exact/native/SA controls remain much faster;
no quantum advantage is established.

Work is paused at the user's request after completing these runs and checks.
No training jobs remain running and no further work is scheduled.
