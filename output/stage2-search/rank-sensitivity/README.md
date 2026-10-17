# Structural rank compiler: duration/deadline sensitivity

`report.json` retains a bounded 29-case diagnostic, with the exact source snapshot `rank_probe-source.py`. Reproduce `run.py` only in a fresh directory because it never overwrites per-case evidence. This is three-job/three-machine sensitivity, **not scaling in job count**.

The official durations were tested at H=7,8,9,10,12. Eight seeded random duration matrices (integers 1–4, seed2026) were tested at `max(job workload,machine workload)+{0,1,3}`. Complete-order scores are computed only after the structural construction attempt for independent diagnostic labeling. No LP is enabled.

Of eight feasible tested deadlines, only the official H8 case produced the nontrivial exact four-bit model. One random case had a unique feasible order and SAT fixed all nine bits, leaving zero decisions. The other six feasible cases were rejected by the compiler's exact-validation assertion; each traceback is retained. Official H9, H10 and H12 all reject. These are failures of this restricted compiler, not proofs that another quadratic formulation cannot exist.

The remaining 21 tested deadlines were certified UNSAT by structural SAT constraints and independently confirmed to have no deadline-feasible assignment across 512 original bitstrings each. Therefore the overall 23 accepted / 29 statistic must **not** be presented as 23 useful quantum models: 21 are classical infeasibility certificates and one is solved completely by classical presolve.

Each accepted numerical proof and every rejected attempt is preserved alongside its complete instance. No QPU calls, Stage1 selected artifacts or compiler code were changed. The result supports careful instance/deadline-specific language for the four-qubit example.
