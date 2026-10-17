# Documentation index

The active Stage 2 entry is **Axion Kitchen**. Start with the root
[README](../README.md); the older MetalTech factory studies are historical.

## Active documents

| Document | Purpose |
|---|---|
| [PROJECT_DESIGN.md](../PROJECT_DESIGN.md) | Implemented problem, encoding, objective and proofs |
| [CATERING_QUALITY.md](CATERING_QUALITY.md) | Exact references, sampled quality and limitations |
| [catering/README.md](../catering/README.md) | Installation, reproduction and frozen inputs |
| [CATERING_SOLVER_CONTRACT.md](CATERING_SOLVER_CONTRACT.md) | Shared input/output conventions |
| [CATERING_METHOD_WORKSPLIT.md](CATERING_METHOD_WORKSPLIT.md) | Method ownership and handoffs |
| [catering-methods/](catering-methods/) | Classical, QAOA, VQE and VeloxQ implementation details |
| [Benchmark browser](http://127.0.0.1:4192/catering/benchmarks/) | Filter all retained campaigns, compare budgets and inspect source hashes |
| [CATERING_PRESENTATION.md](CATERING_PRESENTATION.md) | Presentation structure and remaining result gates |
| [CATERING_VOICEOVER.md](CATERING_VOICEOVER.md) | Timed video narration |
| [CATERING_LIVE.md](CATERING_LIVE.md) | Live speaker and operator cues |
| [CATERING_QA.md](CATERING_QA.md) | Quick answers and technical follow-ups |
| [STAGE2_SUBMISSION.md](STAGE2_SUBMISSION.md) | Official criteria, deliverables and final checks |
| [DEVELOPMENT_LOG.md](../DEVELOPMENT_LOG.md) | Dated decisions, experiments and corrections |

The paired-course profile is `paired-course-contiguous.v3`.
[CATERING_QUANTUM_FIRST.md](CATERING_QUANTUM_FIRST.md) explains the design choices.
[CATERING_AMBITIOUS_SPEC.md](CATERING_AMBITIOUS_SPEC.md) is a broader proposal;
it is not a list of delivered features.

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

## Historical factory work

The `STAGE2_*` family mostly describes earlier manufacturing studies. The active
exception is [STAGE2_SUBMISSION.md](STAGE2_SUBMISSION.md), which identifies its
archived factory section explicitly. Read [stage2/README.md](../stage2/README.md)
for the older executable model; use [STAGE1_COMPACT.md](STAGE1_COMPACT.md) for
baseline methods. Historical transcripts and plans are retained under
[archive/2026-10-17/](archive/2026-10-17/).

Those older source paths remain in place because research scripts, verifiers
and retained source manifests reference them. Presentation-facing duplicates
are consolidated first; moving bulk evidence needs a separate dependency audit.
