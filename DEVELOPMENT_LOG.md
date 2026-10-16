# Development log

## 2026-10-16 — requirements and access

- Captured the organizer's opening slides and checked the transcription. The user emphasized that both baseline solutions must be demonstrated for eligibility.
- Connected/verified the existing GitHub remote and pushed the initial shared context snapshot as `1123ff4`, following the user's explicit instruction. Subsequent work is local until published.
- Verified WCSS SSH authentication and Axion quantum Unix group membership. Slurm did not list a corresponding allocation; a test-only request using the group name as an account was rejected. No compute job was submitted and no account default was changed.
- Read both supplied PDFs in full, visually checked the instance tables and extension requirements, and reconciled the context. Important clarification: Instance A requires a QUBO solved using a quantum algorithm; baseline output times are integer hours.

## 2026-10-16 — presentation environment

- User requested visually engaging results and specified a clear Factorio/Stardew Valley-inspired scene. Chose original SVG pixel art with machine mechanisms, a conveyor, parts, and a small landscape; kept analysis and controls readable outside the scene.
- Built a local-only, buildless browser application with Node's standard library server. This avoids a framework/dependency setup for a presentation shell and keeps it easy to run and record offline.
- Added 3×3/2×2 illustrations, time replay, selection, linked Gantt chart, evidence view, playback speed, presentation layout, and JSON import/export. The 9-hour alternative was manually authored for comparison, not obtained through a solver experiment.
- Kept illustrations separate from actual result claims. No completed baseline JSON outputs or solver-run evidence have been fabricated.
- Implemented independent checks against operation requirements: coverage, duration, machine capacity, and precedence. The official-output adapter also checks the declared makespan and requires integer hours.
- Added the exact official input JSON files. Tests compare fixture operation data to these inputs.
- Caught and corrected a visual bug during browser review: an SVG tile path had an implicit black fill, obscuring the factory floor. Explicitly removed the fill.
- Verified timeline selection seeks to the operation's start and updates the selected part route and completion count. Checked the evidence view's feasibility/source labels.
- Browser checks also confirmed 2×2/3×3 switching, 2×2 replay completion at 4 hours, and import of a temporary official-format illustration with unverified method provenance. The test fixture remained in ignored `tmp/`, not among final baseline outputs.
- Ten automated tests passed, as did JavaScript syntax checks. These verify the presentation/checker, not quantum execution.
- Tests and syntax checks are recorded in the task's final report after the final changes; they establish display/checker behavior, not quantum solver success.

## Decisions and rejected directions

- Rejected presenting an SDK call alone as satisfying both instances: the 2×2 needs a genuine quantum algorithm run.
- Rejected replacing failed solver output with a classical answer while calling it a solver success. Classical reference results and solver-produced schedules will have separate provenance.
- Kept transport cosmetic because the official baseline has no travel-time constraint.
- Chose a shared display contract plus an official-JSON adapter instead of coupling the frontend to VeloxQ credentials or SDK objects. API tokens must stay outside the browser and repository.
- Deferred extended-model UI claims until the chosen constraints are actually modeled and solved. Rich visuals cannot substitute for Stage 2 substance.

## Current status

Visual cleanup passes on 2026-10-16: removed the introductory slogans, stage eyebrow, repeated instructions, redundant passing-check descriptions, and footer tagline. Replaced the temporary asterisk with the unchanged Axion logo from the user's `axion2.0` site, bundled its typefaces/licenses locally, and revised the Gantt to neutral bars with semantic job markers and a legible dark selection. Factory, selected-chart, and Validation states were inspected in the browser. No scheduling algorithm or data was changed by these passes.

The first presentation environment and offline QUBO preparation are implemented and checked. Neither quantum nor VeloxQ baseline execution is complete. VeloxQ access and the correct Axion allocation mapping remain unconfirmed. No Stage 2 model has been selected.

## 2026-10-16 — offline Stage 1 preparation without VeloxQ access

- User asked whether implementation could start without the API. Built a standard-library Python preparation pipeline; it performs no service calls and needs no new packages.
- Implemented integer start windows, exactly-one/capacity/precedence QUBO penalties, coefficient export, sample decoding, and an independent interval checker. All weights are one for fixed-horizon feasibility; zero energy means feasibility. Minimizing makespan remains an outer search.
- Reproduced 39 variables at H=8 for B, using ordinary window pruning. A has 8 at H=4. These are not novel/minimal encoding claims.
- Independently enumerated all machine orders (including non-permutation combinations): optima are 4 h and 8 h. Both references round-trip through their QUBOs with zero energy. Wrote clearly labeled reference artifacts rather than final required-method submission files.
- Verified every bitstring of the 2×2 QUBO at H=3 and H=4 against independent schedule feasibility. Added 1,000 deterministic 3×3 one-start-per-operation samples comparing QUBO energy with direct constraint-violation counts, reference checks, and corrupt-schedule rejection.
- Prepared a lazy optional dimod BINARY BQM conversion for the SDK boundary. Conversion and remote integration remain untested here. The official SDK README confirms token-based remote sampling; backend behavior still needs real service verification.
- AI assistance included the offline formulation implementation, reference enumerator, tests and explanatory notes. Team review and understanding remain required. No QAOA/VeloxQ result is claimed.

## 2026-10-16 — baseline/methods literature review and tutorial

- Ran a targeted literature sweep (OpenAlex keyword/title queries plus one backward/forward citation step from seven seed papers) focused on the Stage 1 formulation and the methods we might use. Result: `literature/BASELINE_METHODS_REVIEW.md` (52 DOI-resolved references) and `literature/reading_list.csv`, complementing the existing Stage 2 guide.
- Main conclusions recorded there: our time-indexed QUBO with window pruning and an outer horizon search is the standard Venturelli et al. (2015) formulation, ported to QAOA by Kurowski et al. (2023); differentiation must come from encoding size, constraint-aware QAOA, and a hybrid (LNS-style) extension where VeloxQ solves residual QUBOs. VeloxQ is a classical, quantum-inspired solver and must be described that way.
- Extended `literature/sources.json` with a `baseline-methods` collection and generalised the README generator in `fetch_papers.py`; 19 new open PDFs (arXiv versions) were added. Publisher-hosted PDFs outside arXiv could not be fetched from that environment and remain link-only; Stage 2 manifest records keep their original retrieval data.
- Added `docs/METHODS_TUTORIAL.html`. Its numbers come from `solver/stage1.py` models and a small exact statevector QAOA simulation (COBYLA, 20 restarts): at H=4 exactly 1 of 256 one-hot bitstrings has zero energy; at p=3 the domain-wall model reaches P(optimal)=0.886, matching the committed QAOA run's 0.888 feasible-shot rate; one-hot with an X mixer reaches only 0.113, while an XY mixer recovers the domain-wall result. Also documented a lower-bound proof that 8 h is optimal for Instance B (T load 5 h + min(F+S) 3 h).
- AI assistance: the literature search, synthesis, simulations and tutorial were prepared with an AI research assistant. Claims summarise abstracts; team members should read the key PDFs before the defense.
