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
