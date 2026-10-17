# Cold sponsor packets: three representations and a matched-penalty control

17 October 2026. The [offline packet report](../../../output/sponsor-merit-packets-v1/report.json)
contains actual HDF5 files for the same replacement-capacity factory input:

| Representation | Bits / couplers | Penalty | Largest absolute scaled Ising coefficient |
|---|---:|---:|---:|
| Hard-deadline decision, cap900 |818 /33,817 |1 |204 |
| Nested cap64 optimization pool, original bound |2,078 /196,228 |1,514,476 |3,144,052,266 |
| Complete support-pruned optimization model |2,499 /381,371 |65,791 |170,793,616 |

The decision packet preserves every schedule satisfying its hard deadlines and
cap, not the original optimization landscape. The enriched pool is lossy even
though native CP certifies that this instance's on-time optimum is retained.
The complete packet retains the original declared discrete optimization domain
after exact support pruning. An actual solver comparison must distinguish these
questions and feasible domains.

The original-bound enriched packet is preserved. A
[separate matched-penalty packet](../../../output/sponsor-enriched-matched-penalty-v1/report.json)
sets its penalty to65,791, matching the complete model. The proof uses the saved
pre-CP list-heuristic plan of energy65,790, which is represented by the nested
pool. Every infeasible state has energy at leastU+1, while that checked feasible
state has energyU; therefore global minima remain feasible and feasible energies
are unchanged. The heuristic is a penalty certificate, **not a sampler warm
start**. Both enriched penalty variants remain available for an explicitly
declared landscape control; smaller coefficients do not establish better solver
performance.

The matched enriched packet's largest absolute scaled Ising coefficient is
136,582,206, compared with3,144,052,266 for its retained original-bound variant.
This is a coefficient audit, not a measured performance improvement.

All files are cold: there is no HDF5 Spectrum and no initial/reference solution
uploaded in the packet. Decoder records retain assignments/group labels and
columns where required. Every literal coefficient and offset passes an inverse
substitution audit, proving equality for all bitstrings, with six additional
energy spot-checks per file. The first three packets check616,814 coefficients
and constants; the matched enriched supplement checks another198,307. Labels,
sparse/dense coupling symmetry, integer dtypes, exact offsets and file hashes
are audited.

The mapping is s=2x−1, and the entire Ising Hamiltonian is multiplied by4. Returned
energies must be divided by4, including the recorded constant. The scaled Ising
fields include sums over neighboring QUBO couplings; the unit decision QUBO
does not have unit Ising fields. Files preserve exact integer values locally.
Service precision, supported account resources, initialization behavior and
acceptance are **not verified** by successful offline serialization.

The SDK is imported only after forcing the process-local `VELOX_TOKEN` empty;
its previous value is never read. The preparer calls only the pinned SDK's
local HDF5 writer and never constructs a solver or invokes an API. Source
snapshots, protocols, original input hashes and manifests are retained.

```sh
.venv/bin/python -m unittest tests.stage2.test_sponsor_merit_packets -v
.venv/bin/python -m stage2.sponsor_merit_packets --output output/NEW-PACKETS
.venv/bin/python -m stage2.sponsor_merit_packets --matched-enriched --output output/NEW-MATCHED-PACKET
```

Execution remains subject to the existing remote-use hold and a separately
approved bounded pilot. These assets establish representation and file
correctness, not service integration success, speed, useful sample diversity,
prize eligibility or a VeloxQ advantage. The main control comparison remains
native CP plus same-QUBO local methods, with raw physical schedule checks,
encoded-register validity and common operational target satisfaction reported
separately.
