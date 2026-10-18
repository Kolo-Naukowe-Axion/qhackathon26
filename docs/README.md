# Documentation index

The active Stage 2 entry is **Axion Kitchen**. Start with the root
[README](../README.md); the older MetalTech factory studies are historical.

## Active documents

| Document | Purpose |
|---|---|
| [CATERING_PROBLEM.md](CATERING_PROBLEM.md) | Self-contained formal problem statement, objective, QUBO and method scopes |
| [PROJECT_DESIGN.md](../PROJECT_DESIGN.md) | Implemented problem, encoding, objective and proofs |
| [CATERING_QUALITY.md](CATERING_QUALITY.md) | Exact references, sampled quality and limitations |
| [CATERING_INVESTMENT.md](CATERING_INVESTMENT.md) | What-if: which resource serves more meals (classical CP) |
| [catering/README.md](../catering/README.md) | Installation, reproduction and frozen inputs |
| [CATERING_SOLVER_CONTRACT.md](CATERING_SOLVER_CONTRACT.md) | Shared input/output conventions |
| [catering-methods/](catering-methods) | Classical, QAOA, VQE and VeloxQ implementation details |
| [Benchmark browser](https://qfactoria.com/catering/benchmarks/) | Filter all retained campaigns, compare budgets and inspect source hashes |
| [CATERING_PRESENTATION.md](CATERING_PRESENTATION.md) | Presentation structure and remaining result gates |
| [CATERING_VOICEOVER.md](CATERING_VOICEOVER.md) | Timed video narration |
| [CATERING_RECORDING.md](CATERING_RECORDING.md) | Source-driven shot list, dry run and final capture/voiceover instructions |
| [CATERING_LIVE.md](CATERING_LIVE.md) | Live speaker and operator cues |
| [CATERING_QA.md](CATERING_QA.md) | Quick answers and technical follow-ups |
| [STAGE2_SUBMISSION.md](STAGE2_SUBMISSION.md) | Official criteria, deliverables and final checks |
| [CATERING_FINAL_HANDOFF.md](CATERING_FINAL_HANDOFF.md) | Final package links, exact form values and remaining external steps |
| [DEVELOPMENT_LOG.md](../DEVELOPMENT_LOG.md) | Dated decisions, experiments and corrections |

The implemented profile is `paired-course-contiguous.v3`.
[PROJECT_DESIGN.md](../PROJECT_DESIGN.md) is the current specification. Earlier
proposals are in [archive/planning/](archive/planning/); they include features
that are not implemented.

## Evidence locations

- `output/catering-complete-cell-v3/`: complete small-cell inputs, references,
  all quantum trials, controls and hashes.
- `output/catering-paired-pilot-v1/`: all larger restricted-portfolio trials.
- `output/catering-foundation-v3/`: frozen shared inputs for method owners.
- `output/catering-velox-scale-v3/`: larger same-model input tiers.
- `output/catering-methods/qaoa/`: 400-run campaign, frozen plan and archives.
- `output/catering-methods/vqe/`: experiment CSVs and checked exported schedules.
- `output/catering-methods/veloxq/`: actual service receipts and raw evaluations.
- `output/catering-velox-conditioned-service-v1/`: no-idle representation study.
- `output/catering-math-audit-v1/`: read-only formulation/quality audit receipts.
- `output/playwright/`: ignored local recordings, screenshots and demo checks.

These JSONs are research evidence and solver inputs. Their paths and hashes
are part of the contract; do not bulk-delete, rename or rewrite them for tidiness.
Earlier v1 catering outage results omitted recovery cleaning; v2 uses a different
component-demand objective. Keep both as historical/regression evidence.

## Historical work and team notes

Earlier factory studies, baseline drafts and broad proposals are grouped under
[archive/](archive/README.md). The older executable model stays in
[stage2/](../stage2/README.md); the current baseline explanation is
[STAGE1_COMPACT.md](STAGE1_COMPACT.md). Team coordination and workspace notes
are under [internal/](internal/).

Frozen inputs, raw results and source snapshots retain their original paths
and hashes. Archived source manifests refer to their recorded commits; the
archive index explains how to recover those exact versions.
