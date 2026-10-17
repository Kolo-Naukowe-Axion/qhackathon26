# Compute access and quantum budget

Checked 17 October 2026, approximately 15:29 Europe/Warsaw. Read-only inventory
and non-submitting scheduler checks only. No allocation, rental, QPU execution,
VeloxQ call, paid-plan selection or account enrollment was performed.

## Local Mac

`system_profiler SPHardwareDataType SPDisplaysDataType` reports:

- MacBook Pro, Apple M5 Pro.
- 15 CPU cores: 5 Super and 10 Performance.
- 16 GPU cores; Metal supported.
- 48 GB unified memory, shared by CPU/GPU/operating system and other programs.

This is not a CUDA/H100 machine. Generic double-precision state storage is
4 GiB at 28 qubits, 16 GiB at 30, 32 GiB at 31, 64 GiB at 32. Workspace and
runtime remain separate constraints; no new simulation benchmark was run.
Current recipe-bridge sector simulation is a restricted state space, not a
generic dense-register benchmark.

### Dense-state storage limits versus a usable simulation

17 October clarification. A dense statevector uses `16 * 2^n` bytes in
complex128 or `8 * 2^n` bytes in complex64. These are exact amplitude-storage
requirements, not total process memory. A 35-qubit vector alone needs 512 GiB
or 256 GiB respectively. Shots do not require a separate vector for each shot;
concurrent simulations and saved intermediate states can multiply storage.

The following budgets are **GiB**, not decimal GB. The single-vector columns
require strictly less than the whole budget. The conservative planning columns
reserve 25% of the budget and allow two statevectors; they still do not guarantee
a particular simulator's runtime or peak memory without profiling it.

| Memory budget | Single vector: complex128 / complex64 qubits | Two vectors plus 25% reserved: complex128 / complex64 qubits |
|---:|---:|---:|
| 48 GiB | 31 / 32 | 30 / 31 |
| 96 GiB | 32 / 33 | 31 / 32 |
| 128 GiB | 32 / 33 | 31 / 32 |
| 256 GiB | 33 / 34 | 32 / 33 |
| 512 GiB | 34 / 35 | 33 / 34 |
| 1,024 GiB | 35 / 36 | 34 / 35 |

For example, 32 double-precision qubits require 64 GiB for one vector; an
optimized implementation may run on a 128 GiB host, while one that holds two
vectors plus other arrays cannot fit that budget. The Mac's unified memory is
shared with the OS and other apps. CPU RAM and GPU VRAM are separate pools on
H100 systems; do not add them together as a single GPU statevector budget.

The new paired-meal code in `catering/meal_blocks.py` supports exact simulation
of an invariant one-hot sector: for block sizes k_g, amplitude storage is
`16 * product(k_g)` bytes, while circuit width is `sum(k_g)` data qubits.
Fourteen blocks with sizes 3 repeated seven times and 2 repeated seven times
have 35 data qubits, 279,936 sector states and about 4.27 MiB of complex128
amplitudes. This is an arithmetic example, not a benchmark of total working
memory. The current implementation additionally stores per-state choices,
objective/penalty arrays and working vectors, and has a default two-million-
state guard. It is not a generic 35-qubit simulator: the initialization and
all simulated gates must preserve the declared one-hot sector. Arbitrary VQE
ansatzes or noise channels may invalidate this restriction.

### Local runtime screen: shallow VQE-style circuits and a classical block

17 October, local only. Receipts are in
`output/catering-vqe-runtime-screen-v1/`. This is a circuit-execution screen,
not a trained VQE result or a convergence estimate. Qiskit2.5.2/Aer versions
are recorded in the receipt; use the receipt as authority for installed versions.
The ideal circuit has two layers of RY/RZ rotations and alternating nearest-
neighbor CNOTs,1024shots, four simulator threads and two repeats per width.

| Qubits | Dense statevector median seconds/evaluation | MPS median seconds/evaluation |
|---:|---:|---:|
| 22 | 0.126 | 0.031 |
| 24 | 0.563 | 0.032 |
| 26 | 2.309 | 0.035 |
| 30 | Not run; roughly40seconds projected from smaller widths | 0.040 measured |

MPS used zero truncation threshold. This shallow nearest-neighbor circuit has
limited entanglement across separators, making it especially MPS-friendly;
these timings do not apply to arbitrary deeper/highly connected ansatzes. The
dense30qubit estimate extrapolates a16fold state-size increase from26qubits;
actual peak memory and runtime were not measured at30. A density-matrix/noisy
simulation is outside this screen.

For500objective evaluations, the measured shallow MPS circuit implies about
20seconds of simulator execution per30qubit cluster; scoring/optimizer setup
adds time, so seconds-to-minutes is a reasonable experimental budget for this
ansatz, not a promise of a good answer. The dense extrapolation instead implies
about5.6hours per cluster. A200variable partition with six30bit clusters and
one20bit cluster repeats those costs at least six times per complete update
pass; further passes/restarts/gradient evaluations multiply the budget. Count
circuit evaluations, not just optimizer iterations. No global solution quality
or convergence time follows from these execution timings.

A separate actual paired-meal block from S3/customers6 had30encoded data bits,
16offered programs and a5462program broader local domain. Single-worker CP-SAT
proved this restricted block optimum in0.0149seconds; option generation and
bundle construction took0.370seconds. The independently checked tuple was
U7,W2,B2,R2. This is one deliberately bounded portfolio, not a full-kitchen
optimum or universal30variable timing. All measurements used the Mac; no
H100, IBM or VeloxQ execution occurred.

## WCSS via the existing `wcss` SSH alias

Authentication succeeded. Confirmed user membership in Axion/quantum groups and
Slurm association/QOS `hpc-iwowoj-1781179048`. This is the allocation previously
verified for Axion CPU work; no unrelated allocation was substituted.

Live `sinfo` reports:

| Resource | Node inventory, not an exclusive reservation |
|---|---|
| Bem CPU partitions | 48 CPU cores, roughly 190–384 GB scheduler memory per node |
| Lem CPU partitions | 128 CPU cores, 1,543,413 MB scheduler memory per node |
| Lem GPU partitions | 64 CPU cores, 1,030,000 MB scheduler memory, 4 Hopper GPUs per node |

The login host itself has only about 23 GiB RAM and is not the compute resource
to use for simulations. It was used for metadata commands only.

The official [WCSS hardware inventory](https://www.wcss.pl/kdm/) identifies the
Lem accelerators as NVIDIA H100 and advertises 96 GB per accelerator. This
was found through its indexed official page; direct web retrieval timed out.
No GPU compute node was allocated and no live `nvidia-smi` was obtained, so
actual GPU-visible memory and the CUDA/simulator stack remain unverified.

`sbatch --test-only` accepted these requests with the Axion account:

| Request | Predicted start in this transient snapshot |
|---|---|
| Bem CPU short: 16 CPUs, 128 GB, 5 minutes | 17 October, 15:43:56 |
| Lem CPU short: 16 CPUs, 128 GB, 5 minutes | 19 October, 03:55:33 |
| Lem CPU short: 16 CPUs, 1 TB, 5 minutes | 19 October, 03:56:56 |
| Lem GPU short: 1 Hopper, 8 CPUs, 128 GB host RAM, 5 minutes | 18 October, 12:30:33 |

These are scheduler predictions, not bookings or guaranteed start times. Test-only
prints prospective job IDs but does not submit jobs. A subsequent `squeue` for
the user was empty. Interactive-partition tests using `sbatch --test-only` were
rejected because those partitions require `srun --pty`; no interactive allocation
was attempted. Interactive waiting time is therefore unknown.

The account QOS displays a group GPU limit of 32 and configured resource-minute
limits (CPU 3,000,000; GPU 600,000). These are shared configured limits, not a
verified remaining personal balance. No unlimited-resource claim follows.

## Other configured resources

- Authenticated, read-only Vast.ai instance listing returned an empty list.
  There is no current instance there; no machine was rented or started.
- The existing `pracus` SSH alias timed out. Its current hardware is unverified.

## VeloxQ capacity: published scale is not account entitlement

Read-only public-source check, 17 October 2026; no VeloxQ API or job was called.
The current [VeloxQ paper, v2](https://arxiv.org/abs/2501.19221v2) reports runs
with up to 100 million sparsely connected variables. Its older indexed abstract
mentions 200 million; use the current version's 100-million figure. This is a
reported research scale for particular sparse models, not a guaranteed limit
for our kitchen QUBOs or our access tier. These are classical QUBO variables,
not simulated or physical qubits.

The [public pricing page](https://veloxq.com/) advertises unlimited problem size
for its prepaid service and lists cloud backends. It does not establish our
hackathon credit balance, enabled backends, maximum upload/nonzero count or job
limits. Our actual largest permitted run remains unverified. Memory depends on
both variables and nonzero interactions, as well as solver state and number of
parallel samples; a densely coupled scheduling QUBO cannot inherit a sparse
benchmark's capacity just from its variable count.

For project planning, compile and measure a progression of meaningful whole-
kitchen QUBOs (for example 1,000, 5,000 and 10,000 variables) before spending
credits. These are proposed test sizes, not confirmed account limits or jobs.
Record nonzero count, coefficient range, serialized size and independent
schedule validity. The quantum method can use smaller neighborhoods of the
same decision model. No capacity check reverses the existing execution hold.

## IBM Quantum versus IQM

The user clarified that the free-minute service they meant is **IBM Quantum**.
The earlier roughly 140-qubit figure remains a user-reported planning ceiling;
no exact backend or signed-in account entitlement was verified.

- [IBM Open Plan](https://quantum.cloud.ibm.com/docs/en/guides/plans-overview):
  up to 10 QPU minutes per 28-day rolling window. A separate conditional
  [180-minute promotion](https://www.ibm.com/quantum/blog/open-plan-updates)
  requires qualifying prior usage and opt-in; do not budget it as already granted.
- [IQM Resonance Starter](https://iqm.tech/products/iqm-resonance/): up to 30
  credits per month, subject to availability. Credits are not automatically
  equivalent to 30 minutes; backend-specific conversion was not verified.

The standard local `.qiskit/qiskit-ibm.json` account file is absent and the existing
Stage 2 Python environment has no `qiskit_ibm_runtime` package. This does not rule
out a browser account or configuration elsewhere. No secret was printed, and
personal balance/backend access remains unverified. No account was created.

## How many QPU minutes to budget

For a small experiment, tune parameters on a simulator, then run a frozen family
of shallow hardware circuits from the same scheduling model. Do not spend the
allowance on an open-ended hardware optimization loop. Circuit usefulness still
depends on native routing/depth/errors, independently of available minutes.

[IBM's approximate usage model](https://quantum.cloud.ibm.com/docs/en/guides/estimate-job-run-time)
uses sub-job overhead plus shots times circuit/repetition duration. Its simple
default-setting estimate is about 2 seconds per sub-job plus 0.00035 seconds per
execution. Applying that illustrative formula at 4,096 shots per circuit:

| Circuits | One sub-job | One sub-job per circuit |
|---:|---:|---:|
| 4 | 7.73 seconds | 13.73 seconds |
| 24 | 36.41 seconds | 82.41 seconds |
| 100 | 145.36 seconds | 343.36 seconds |

These are arithmetic examples, not estimates from our actual routed backend.
One proposed24-circuit design is four event cases times three frozen parameter
settings times two repeats, at4,096shots each. It is a budget example only:
the catering urgent/combined cases and corresponding circuits have not been
built, and no circuit success/optimality follows from their potential shot budget.
They assume the quoted typical timing, no mitigation expansion and the indicated
sub-job grouping; payload splitting can alter overhead. Deeper circuits, additional
settings/repeats/calibration and mitigation can increase consumption substantially.
Queue waiting is distinct from billed execution usage in job/batch mode.

Planning recommendation: prepare a small 1–2 minute pilot envelope, then a total
2–5 minute frozen demonstration envelope if actual compiled timing and remaining
allowance support it. These are proposed caps, not guaranteed required runtime.
Obtain the exact backend target and signed-in balance, compile and estimate the
complete workload before choosing a final cap. All QPU execution remains held.

## Catering objective reminder

The latest fixed-departure proposal prioritizes missed confirmed meal lots,
then excess production, then batch count, then changes to the unstarted plan.
Choose batch yields, allocation across customers and resource/timing decisions.
Freshness, departure eligibility, resource capacity and committed production are
constraints. This is not yet a calibrated monetary-cost objective. The user has
now activated catering as a direction to try; see the
[method work allocation](CATERING_METHOD_WORKSPLIT.md). The ambitious disposal/
WIP/capacity extensions are defined in a newer spec and remain unimplemented.
