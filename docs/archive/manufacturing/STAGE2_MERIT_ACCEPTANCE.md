# Stage 2 merit acceptance matrix

17 October 2026. This matrix audits agreed non-VeloxQ merit work against the official challenge and combined plan. It does not declare the goal complete, certify a prize, or authorize remote use/publication.

The current machine-readable snapshot is [requirements.json](../../../output/merit-workspace-final-audit-v1/requirements.json). Re-run the verifier into a fresh output directory after new evidence arrives. A missing artifact stays pending. Frozen campaign source hashes identify historical code; they need not equal later implementation hashes.

Authority: [official challenge](../../../Quantum_Hackathon_2026_ERP_Challenge.pdf), §§4–5 and11; [combined plan](STAGE2_COMBINED_DIRECTION.md), items1–6; [independent review](STAGE2_REVIEW_PASSES.md), priorities1–5.

| ID | Scope | Status | Requirement and completion evidence |
|---|---|---|---|
| C01 | non_velox_core | **passed** | Correct official baselines and comparable 3×3 encoding count. `output/stage1-compact-ready/formulation-certificates.json`, `docs/STAGE1_COMPACT.md`, `schedule_2x2.json`, `schedule_3x3.json` |
| C02 | non_velox_core | **passed** | Checked full-recipe manufacturing recovery centerpiece. `output/manufacturing-recovery-v2/`, `output/manufacturing-full-recovery-v1/` |
| C03 | non_velox_core | **passed** | Nested representation/quality frontier and stronger pool control. `stage2/capacity_frontier.py`, `output/capacity-frontier-review-v1/`, `docs/STAGE2_CAPACITY_FRONTIER.md` |
| C04 | non_velox_core | **passed** | Exact hard-deadline operational query. `stage2/deadline_qubo.py`, `stage2/deadline_reference.py`, `output/deadline-decision-review-v1/` |
| C05 | non_velox_core | **passed** | Repeated local controls and physical-versus-encoded validity. `output/deadline-anneal-review-v1/`, `output/deadline-anneal-report-audit-v2/` |
| C06 | non_velox_core | **passed** | Manufacturing scaling32/64/128 with honest reference status. `output/manufacturing-study-v1/`, `docs/STAGE2_MANUFACTURING_STUDY.md` |
| C07 | non_velox_core | **passed** | Audited separate assignment-QAOA correctness study. `output/stage2-entry-v2/`, `output/stage2-entry-circuit-audit-v1/`, `docs/STAGE2_ENTRY.md` |
| C08 | non_velox_core | **passed** | Quantum comparison on a recovery-derived full-recipe restriction. `stage2/recipe_bridge.py`, `output/recipe-bridge-review-v2/`, `docs/STAGE2_RECIPE_BRIDGE.md` |
| C09 | non_velox_core | **passed** | Per-feature price-of-realism accounting on the actual model. `stage2/manufacturing_realism.py`, `output/realism-frontier-v1/`, `output/realism-continuous-counts-v2/`, `docs/STAGE2_REALISM_FRONTIER.md` |
| C10 | non_velox_core | **passed** | Current sponsor formulations prepared and audited entirely offline. `stage2/sponsor_merit_packets.py`, `output/sponsor-merit-packets-v1/`, `output/sponsor-enriched-matched-penalty-v1/`, `docs/STAGE2_SPONSOR_PACKETS.md` |
| C11 | non_velox_core | **passed** | Economic sensitivity and capacity break-even answer. `stage2/capacity_economics.py`, `output/capacity-economics-v2/` |
| C12 | non_velox_core | **passed** | One authoritative design/log/README/submission/UI story. `PROJECT_DESIGN.md`, `DEVELOPMENT_LOG.md`, `README.md`, `docs/STAGE2_COMBINED_DIRECTION.md`, `docs/STAGE2_SUBMISSION.md`, `presentation/manufacturing/` |
| C13 | non_velox_core | **passed** | Reproducible final local acceptance tests and build. `scripts/verify-stage2-merit.py`, `tests/stage2/`, `tests/manufacturing-studio.test.mjs`, `package.json` |
| C14 | non_velox_core | **passed** | Preserve failures and distinguish solver loss from representation loss. `docs/STAGE2_REVIEW_PASSES.md`, `output/deadline-boundary-review-v1/`, `output/deadline-boundary-review-v2/`, `output/manufacturing-anneal-pilot-v1/`, `output/recipe-bridge-review-v1/`, `output/realism-continuous-counts-v1/` |
| V01 | held_external | **held** | Actual VeloxQ pilot and bounded sponsor scaling campaign. `docs/STAGE2_VELOXQ_RUNBOOK.md` |
| R01 | release_or_human | **pending** | Recovery-centered final ≤3-minute video. `docs/STAGE2_MANUFACTURING_VIDEO_SCRIPT.json`, `output/manufacturing-video-v3/receipt.json` |
| R02 | release_or_human | **human_required** | Live presentation and Q&A readiness. `docs/STAGE2_LIVE_SCRIPT.md` |
| R03 | release_or_human | **held** | Public MIT repository, exact release and submission receipt. `docs/STAGE2_SUBMISSION.md` |
| S01 | optional_stretch | **optional** | Full calibrated weekly monetary optimization and purchase ROI. Explicit optional scope |
| S02 | optional_stretch | **optional** | Stochastic robust scheduling, external industrial data and QOBLIB trials. Explicit optional scope |

## Completion rules

Each non-VeloxQ core item needs semantic acceptance, not merely a file. Actual backend calls remain held. Final video production/review, live rehearsal and public release/submission are tracked separately; unfinished external duties do not become completed because local numerical work passes.

The weekly calibrated monetary model, stochastic robustness, external data and QOBLIB are explicitly optional. Parameterized economics is core. No feature may be silently dropped by changing this checklist.

## Consistency closure

The final source-hashed document/display receipt resolves the earlier stale scope and artifact references. Historical failure reports remain separate. This closes local consistency; final video review, live rehearsal and public release remain explicitly tracked above.

## Verification

```sh
.venv-stage2/bin/python scripts/verify-stage2-merit.py --output output/NEW-MERIT-AUDIT
```

The command verifies retained manifests, input-domain nesting, whole-plan checks and numerical identities without any optimizer, SDK, network or quantum execution. The overall result remains incomplete while an agreed core acceptance item is pending or failed.
