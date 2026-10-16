# Stage 2 literature collection

[Annotated reading guide](STAGE2_LITERATURE.md) · [Source catalog](sources.json) · [Download manifest](manifest.json)

The guide contains 19 main references; entry 16 also includes a follow-up paper.
PDFs are public publisher/author manuscripts. Their original copyright and license notices apply; the repository MIT license does not relicense third-party papers.
Existing contributions, including `papers/Learning to Optimize.pdf`, are retained separately.

| Guide entry | Paper | Local copy |
| --- | --- | --- |
| 1 | [Solving Job-Shop Scheduling Problems with QUBO-Based Specialized Hardware](https://doi.org/10.1609/icaps.v32i1.19826) | [PDF](papers/zhang2022.pdf) (9 pages) |
| 2 | [Deriving Compact QUBO Models via Multilevel Constraint Transformation](https://arxiv.org/abs/2404.03610) | [PDF](papers/pichugina2024.pdf) (29 pages) |
| 3 | [Solving the Extended Job Shop Scheduling Problem with AGVs — Classical and Quantum Approaches](https://arxiv.org/abs/2109.04830) | [PDF](papers/geitz2021.pdf) (15 pages) |
| 4 | [Multi-objective rescheduling of job shop scheduling problems in manufacturing using Quantum Annealing](https://doi.org/10.1016/j.mfglet.2024.09.066) | Source link; PDF unavailable |
| 5 | [Quantum annealing heuristics for the job shop scheduling problem with availability constraints](https://doi.org/10.1007/s10732-026-09594-5) | Source link; PDF unavailable |
| 6 | [VeloxQ: A Fast and Efficient QUBO Solver](https://arxiv.org/abs/2501.19221v2) | [PDF](papers/pawlowski2026veloxq.pdf) (22 pages) |
| 7 | [Penalty and partitioning techniques to improve performance of QUBO solvers](https://doi.org/10.1016/j.disopt.2020.100594) | Source link; PDF unavailable |
| 8 | [Quantum Annealing Implementation of Job-Shop Scheduling](https://arxiv.org/abs/1506.08479) | [PDF](papers/venturelli2015.pdf) (15 pages) |
| 9 | [Iterated Tabu Search for the Unconstrained Binary Quadratic Optimization Problem](https://doi.org/10.15388/informatica.2006.138) | [PDF](papers/palubeckis2006.pdf) (18 pages) |
| 10 | [High-performance combinatorial optimization based on classical mechanics](https://doi.org/10.1126/sciadv.abe7953) | Source link; PDF unavailable |
| 11 | [Tabu-Enhanced Simulated Bifurcation for combinatorial optimization](https://doi.org/10.1038/s42005-026-02538-2) | [PDF](papers/tao2026.pdf) (9 pages) |
| 12 | [Preprocessing of Unconstrained Quadratic Binary Optimization](https://users.cecs.anu.edu.au/~pcarr/qpbo/BorosRRR102006.pdf) | [PDF](papers/boros2006.pdf) (58 pages) |
| 13 | [A Multilevel Approach For Solving Large-Scale QUBO Problems With Noisy Hybrid Quantum Approximate Optimization](https://arxiv.org/abs/2408.07793) | [PDF](papers/maciejewski2024.pdf) (12 pages) |
| 14 | [Solving flexible job shop scheduling problems in manufacturing with Quantum Annealing](https://doi.org/10.1007/s11740-022-01145-8) | [PDF](papers/schworm2023flexible.pdf) (11 pages) |
| 15 | [Evaluation of Quantum Annealing-based algorithms for flexible job shop scheduling](https://arxiv.org/abs/2408.15671) | [PDF](papers/schworm2024evaluation.pdf) (6 pages) |
| 16 | [Unbalanced penalization: A new approach to encode inequality constraints of combinatorial problems for quantum optimization algorithms](https://arxiv.org/abs/2211.13914) | [PDF](papers/montanez2022.pdf) (14 pages) |
| 17 | [From the Quantum Approximate Optimization Algorithm to a Quantum Alternating Operator Ansatz](https://doi.org/10.3390/a12020034) | [PDF](papers/hadfield2019.pdf) (51 pages) |
| 18 | [Scenarios and Policy Aggregation in Optimization Under Uncertainty](https://doi.org/10.1287/moor.16.1.119) | [PDF](papers/rockafellar1991.pdf) (33 pages) |
| 19 | [Quantum algorithms for scheduling problems: a survey](https://doi.org/10.1140/epjqt/s40507-026-00494-y) | [PDF](papers/werner2026.pdf) (67 pages) |
| 16 | [Improving Performance in Combinatorial Optimization Problems with Inequality Constraints: An Evaluation of the Unbalanced Penalization Method on D-Wave Advantage](https://arxiv.org/abs/2305.18757) | [PDF](papers/montanez2023followup.pdf) (8 pages) |

To retry missing downloads: `python3 literature/fetch_papers.py` (requires curl and Poppler).
Checksums, source URLs, retrieval failures and downloaded versions are recorded in the manifest.
Downloaded availability does not mean a paper was fully reviewed or its experiments reproduced; see the evidence notes in the guide.
