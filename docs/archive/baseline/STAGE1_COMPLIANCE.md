# Stage 1 formal compliance audit — 16 October 2026

> Superseded selection (17 October): the current runs use 1/3-bit order QUBOs and QAOA for both instances. See [current formulation, experiments and limits](../../STAGE1_COMPACT.md) and `output/stage1-selected.json`. The time-indexed results below remain retained comparison evidence.

Verdict: the current local implementation satisfies the technical Stage 1 baseline in the supplied challenge specification. It is ready to be treated as an implemented and verified baseline. Organizer acceptance and submission completion have not been established.

Authority: `Quantum_Hackathon_2026_ERP_Challenge.pdf`, sections 2, 4.1–4.3, 6, 12 and 14; cross-checked against the opening deck's Stage 1 and deliverable slides. The exact Stage 1 wording on PDF page 2 and JSON contract on page 7 were also checked visually.

| Formal requirement | Current evidence | Assessment |
| --- | --- | --- |
| A: the 2×2 QUBO solved with a quantum algorithm on hardware **or a simulator**, returning a feasible schedule (§4.1) | Four-qubit domain-wall QUBO, cost-phase/X-mixer QAOA circuit, BFGS parameter optimization, measured Qiskit Aer shots, retained model/angles/QASM/counts | Satisfied locally |
| B: the 3×3 QUBO solved on **any** quantum, hybrid or classical QUBO solver, returning a feasible schedule (§4.2) | The actual 39-variable one-hot BQM is sampled by `dwave.samplers.SimulatedAnnealingSampler`; feasible returned samples are decoded directly | Satisfied locally |
| Each operation once; correct duration; no machine overlap; technological precedence (§2) | Every retained sample is assessed; selected root schedules pass independent interval validation | Satisfied |
| Correct official instance data and integer-hour output schema (§14) | Transcribed operation data match the PDF tables; root JSONs have `instance`, `method`, `makespan`, `schedule`, and match selected run evidence | Satisfied locally |
| Working solutions for both instances (§4) | Verified makespans 4 h and 8 h, both independently certified optimal by full machine-order enumeration | Satisfied locally |
| Include both schedule JSONs in the submitted public MIT Git repository (§6) | Both verified root files are included in this release’s commit scope; the selected runs and reproducibility evidence are retained | Included in release packaging; repository is currently private, so the public-repository submission condition remains pending |

ODRA5 and VeloxQ are not prerequisites for this baseline. Quantum/hybrid solvers for B are preferred and may improve the quality score; this is not a mandatory condition. VeloxQ integration is relevant to its separate prize. Neither service was used for the selected results, and both remain on user hold.

The quantum optimizer evaluates circuit-state expectations classically, as a simulator-based variational algorithm. The decoded answer comes from the final Aer sample counts, not the independent reference. Choosing the known reference horizon for these fixed instances is disclosed; the specification supplies reference makespans and does not require a generic horizon-search algorithm. No quantum speedup or physical-hardware result is claimed. A 100% sample-validity rate is not a formal acceptance requirement: the requirement is a feasible returned schedule for each instance.

Validation repeated during this audit:

- `solver.verify` accepts both selected runs under `output/stage1-local-ready/`, with zero optimality gap.
- Both root schedule files equal their selected evidence schedules exactly.
- Both root files use the official top-level fields and produce no independent feasibility violations.
- This audit originally found the root schedules untracked. The 2026-10-16 release includes them alongside their selected evidence; see the current Git history for the publishing record. Organizer submission is not established by publication.

The complete competition submission additionally requires the Stage 2 extension, public MIT repository, README/run instructions and AI-use disclosure, dated Development Log, Project Design, demo video, live presentation/Q&A and submission logistics. AI assistance is explicitly permitted (§12); participants must understand and explain their solution. The local code, document and test checks do not establish completion of those human/submission requirements.

Repository visibility rechecked before release: private, default branch `main`. Publishing this website does not satisfy the challenge’s public-source requirement; changing repository visibility is a separate action.

Current selection: `output/stage1-selected.json`. Detailed experiment evidence: `docs/STAGE1_REFINEMENT.md`.
