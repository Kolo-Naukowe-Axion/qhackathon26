# Axion Kitchen: presentation and demo plan

Planning draft, 17 October 2026. Active catering entry. The factory scripts are
historical fallback material. This document plans the talk, recording and next
implementation work; it is not a completed recording or submission.

## The story

**Title: Axion Kitchen: two courses, one scheduling decision.**

Opening: “Twenty people are waiting for lunch. The mains can finish on time. Without
one shared side batch, we deliver zero complete meals.” This is a synthetic
kitchen, illustrated with an actual checked simulator sample.

The technical contribution is joint batch scheduling and course pairing:
choose local batch programs, share their yields across orders, and reward
complete meals while charging for unpaired food. Pairing expands directly into
quadratic terms without extra product-register qubits. Scheduling conflicts,
freshness and mandatory cleaning make those choices interact.

Keep the pixel kitchen. Use it to explain the decision and its consequences.
Use a small amount of large, readable math and one results comparison outside
the animated scene. Avoid spending the talk explaining every control.

The current strongest evidence supports correctness and an integrated method
study. The VeloxQ prize track needs a stronger checked quality result before
we can lead with a performance claim. The next section defines that work.

## VeloxQ prize preparation

The criteria explicitly include integration correctness, solution quality,
scaling, experimental insight and reproducibility. Large variable counts alone
do not satisfy them. The current implementation already contributes exact
integer packets, offset/sign checks and independent schedule validation.

The first cold scale runs diagnose a feasibility problem under the tested
settings. They do not establish VeloxQ's best performance. Prioritize making
the integration effective on this production decision:

1. **Offline first:** quantify one-hot versus physical-conflict violations and
   objective/penalty coefficient ranges for each retained return. Confirm which
   settings the installed SDK actually supports. Prepare a short, capped
   experiment proposal for the method owner; this plan authorizes no calls.
2. **Feasibility experiment:** select one fixed tier before testing. Compare the
   existing formulation with a mathematically justified penalty alternative or
   a supported feasible initialization. Prove any new penalty bound, create a
   new bundle identity, and validate its feasible objective ordering. Arbitrary
   penalty weakening can change the problem and is not an acceptable shortcut.
3. **Budgeted service experiment:** the VeloxQ owner obtains authorization for
   the concrete submission cap. Keep the original cold run. Record every new
   job, returned sample and quota change. Do not automatically escalate width.
4. **Quality comparison:** compare validated (U,W,B,R), valid-return rate and
   runtime. Separate upload, queue, backend and total time. The current service
   returns only final samples, so time to first feasible plan is not observable.
   Use identical bundle hashes for solver comparisons and comparable declared
   budgets/initialization. A CP FEASIBLE incumbent is not a proven optimum.
5. **Presentation gate:** feature the best reproducible supported result, with
   its domain and budget visible. A service speed claim needs the corresponding
   measured quality and end-to-end time. A useful feasibility improvement can
   be the finding even if CP still returns the better schedule.

Possible final headline, **only if measured**: “A feasibility-aware formulation
makes larger meal-planning QUBOs useful for VeloxQ.” The current title and
script work without assuming this result. The owner may propose a different
backend-supported change after inspecting the failure evidence.

## Three-minute live presentation

Aim for 2:45–2:50 in rehearsal, leaving transition time. One speaker and one
demo operator. Keep the kitchen tab and a prepared terminal open. Use at most
three support frames: objective, evidence, conclusion. Never wait for a queue
or a remote job during the slot.

| Time | Visual/action | Point |
|---|---|---|
| 0:00–0:20 | Cell, tickets, shared C token | Main plus side makes a meal. One batch supplies both orders. |
| 0:20–0:45 | Launch local program; show checked result | Real executable code, retained quantum output clearly labeled. |
| 0:45–1:10 | Seek 11:40, then 12:10; show packing queue | Concurrent resources, exact allocations, 20 complete handovers. |
| 1:10–1:45 | One objective frame; one program/one-hot illustration | Local programs, quadratic pairing, hard-conflict penalties. |
| 1:45–2:20 | One measured-results frame | Complete cell, controls and larger representations have distinct scopes. |
| 2:20–2:45 | VeloxQ finding, then kitchen end state | Same model scales; explain the measured backend lesson. |
| 2:45–3:00 | Buffer / final sentence | State the contribution and stop. |

Draft spoken script, approximately 350 words. Replace the VeloxQ paragraph
after the result freeze; use the current wording if no later evidence exists.

> Twenty people need lunch. Each meal needs a main and a side, packed before
> departure. Our kitchen already has one main cooking. This one shared side
> batch completes both orders. Remove it and we deliver zero complete meals,
> even though the mains still exist.
>
> We extended the factory scheduling problem into batch production with paired
> outputs. We choose quantities, allocations, equipment, workers and phase
> times. Freshness and cleaning constrain the schedule. Repairing a cooker
> also requires a staffed clean before reuse.
>
> Here we launch our local program to check an actual saved quantum sample.
> The animation replays that result. This small kitchen serves all twenty
> meals with zero discarded portions and two new batches. The timeline shows
> the side cooking while the first main is still on its cooker. Packing then
> splits the side across the two departures.
>
> Each bit selects a local batch program, including its resources and times.
> Each block also has an idle choice. For an order, main coverage times side
> coverage tells us whether the meal is complete. The same product identifies
> food left without its partner. Both expand directly into quadratic terms,
> with no extra product qubits.
>
> We prioritize missed meals, then wasted food, then new batches and plan
> changes. One-hot penalties and pairwise conflict penalties enforce the
> represented scheduling rules. Our XY mixer preserves one choice per block.
> A separate checker validates the actual schedule and material balance.
>
> The complete cell contains all thirty-two legal programs and three idle
> choices. All six QAOA simulator trials recover its optimum. Our controls
> also recover it. On the larger kitchen, every pilot still trails the full
> classical reference, so we measure representation loss separately from
> search loss.
>
> VeloxQ uses the same meal model at up to two thousand forty-eight variables.
> The first cold runs exposed low feasibility under our penalty settings.
> We retain exact integer packets and every returned sample, so that finding
> directly guides the next integration experiment.
>
> Our contribution is a checked quadratic model of complete meals and wasted
> components, with an executable path from sampled bits to kitchen operations.

If a fresh optimizer run is ready by rehearsal, replace “check an actual saved
quantum sample” with the precise method and execution description. Keep fresh
classical output, saved quantum output and animation labels distinct.

## Demo runbook

Preparation: from the repository root, run `PORT=4192 npm run dev` only if the
server is not already running. Open <http://127.0.0.1:4192/catering/>. Rehearse
at the actual screen-share size. Use the normal browser zoom and verify that
the tickets and timeline fit. Pause autoplay and disable looping for the talk.

1. Select **Complete small cell** and **QAOA · simulator**. Restore the saved
   plan if a manual intervention is active. Keep the batch timeline visible.
2. Point to Order A and Order B: ten meals each, both require C. Point to
   selected C twenty portions and B ten portions. A is committed outside the
   decision register. Explain that these are actual saved program choices.
3. Run the local checker below. Show a concise summary, not a wall of JSON.
   Say explicitly that it validates a retained sample and performs no training.
4. Seek to **11:40 (minute 70)**. Show concurrent B cooking, C2 cleaning and
   C packing for A. The packing queue links the shared batch to each order.
5. Seek to **12:10 (minute 100)** and pause: 20/20 served, tuple (0,0,2,2).
6. In the video, or if rehearsal leaves time, open C's selected token and
   **Skip x3 and replay**, then seek to the end. This checked manual change
   yields zero complete meals and twenty discarded component portions.
   Restore saved solution immediately. It is not a new optimizer result.
7. Open **Model & results**, then **The QUBO**. Use the prepared objective
   frame if the modal is too small on the shared screen. Show only meal pairing
   and one-hot/conflict terms; keep the full proof available for Q&A.

### Local launch already available

Both rules §9 and §10 require showing program launch and result. This existing
command runs the real hash-aware sample decoder and physical checker locally:

```sh
demo_dir=$(mktemp -d /tmp/axion-presentation.XXXXXX)
.venv-stage2/bin/python -m catering.run evaluate \
  --bundle output/catering-complete-cell-v3/quantum-qubo.json \
  --samples output/catering-complete-cell-v3/p1-seed-2026/samples.json \
  --output "$demo_dir/evaluation.json"
.venv-stage2/bin/python - "$demo_dir/evaluation.json" <<'PY'
import json, sys
payload = json.load(open(sys.argv[1]))
valid = [r for r in payload['results'] if r['valid']]
if not valid:
    raise SystemExit('No physically valid retained sample')
best = min(valid, key=lambda r: tuple(r['check']['metrics'][k] for k in ('U','W','B','R')))
print('RETAINED QAOA SAMPLE / FRESH LOCAL VALIDATION / NO REPAIR')
print('Best checked (U,W,B,R):', tuple(best['check']['metrics'][k] for k in ('U','W','B','R')))
print('Bundle:', payload['bundle_sha256'])
PY
```

This launches validation, **not fresh optimization**. Before recording, prepare
a short launch of the selected optimizer with its owner and time it. A bounded
local classical solve on the same cell is a useful launch demonstration;
the strongest quantum demonstration is a fresh sample from frozen parameters,
clearly distinguished from training. No such sampling/training is launched by
this planning task. Rehearsal must settle the final command and its duration.
Do not describe a replay or checker as a fresh solver run. If launch fails,
show the retained result, state the fallback, and continue.

## Five-minute video storyboard

Target 4:35, leaving 25 seconds of margin. Record the terminal and browser at
readable size. Capture actual launches; trimming waiting time must be visible.
Do not fake terminal output or replace a failed run with an animation.

| Time | Content | Concrete evidence |
|---|---|---|
| 0:00–0:15 | Stage 1 prerequisite | Actual A=4h and B=8h schedule outputs, selected simulator methods. |
| 0:15–0:50 | Kitchen decision and shared side | Two orders, committed A, new B, shared C; explain complete meals. |
| 0:50–1:20 | Launch and result | Final rehearsed optimizer command plus independent check; saved/fresh labels. |
| 1:20–2:10 | Data model and encoding | A concrete program; main/side coverage product; waste; one-hot and conflict terms. |
| 2:10–2:45 | Optimization method | Actual selected QAOA or VQE circuit/objective/update; only a method whose code and result exist. |
| 2:45–3:15 | Operations and counterfactual | Shared-side intervention, 20 versus 0 complete meals; S3 repair and mandatory clean. |
| 3:15–3:55 | VeloxQ integration and scale | Actual packets, validation, frozen tiers, final measured quality/runtime and finding. |
| 3:55–4:20 | Results versus references | Small complete domain, controls, larger offered/raw domains and their gaps. |
| 4:20–4:35 | Development decisions and close | Repair-clean correction, pairing without product bits, restricting portfolios has a cost. |

Code locations for the walkthrough: `catering/meal_blocks.py` (compiler and XY
mixer), `paired_meals.py` (meal accounting), `options.py` (legal local programs),
`decode.py` and `check.py` (independent validation), `meal_search.py` (retained
QAOA pilot), `methods/veloxq.py` (service boundary). Open only the relevant few
lines. The complete development history remains in the log.

## Claim sheet for the speaker

| Statement | Source / current limit |
|---|---|
| Complete cell: 32 legal programs, 3 idle bits, 35 data qubits, 520 couplers | `output/catering-complete-cell-v3/report.json`; all programs of this declared narrow grid. |
| 1,045 sector states, 59 physically feasible | Same report. It is deliberately classically tractable. |
| QAOA 6/6 best tuples (0,0,2,2) | Same report and all six trial directories. Both controls also attain this tuple. Best observed result is not a 100% shot success rate. |
| One shared C batch completes two orders | `output/catering-complete-cell-demo-v3.json`; selected B and C, fixed A, ten people per order. |
| S3 recovery clean occupies C2 and W2 at 70–80 | Frozen V3 snapshots and raw check. Repair ends at 60; immediate reuse is forbidden. |
| Larger QAOA pilot: eight runs improve empty initializer but trail raw CP | `output/catering-paired-pilot-v1/`; restricted/changing portfolios differ from raw domain. |
| Scale: 512 / 1,024 / 2,048 variables | `output/catering-velox-scale-v3/`; 12 customers, nested restrictions of 18,182 local programs, approximately 28–30% coupling density. |
| First VeloxQ cold runs: valid rows 5/512,1/512,0/512 respectively | `docs/catering-methods/VELOXQ.md`, Phase D and raw evaluations. Best tuples(13,6,4,4), (14,8,4,4), none. One setting per width. |
| Stronger offered CP incumbents: (6,1,10,10),(7,2,11,11),(8,3,8,8) | `output/catering-classical-scale-v3/`; 30-second FEASIBLE references, not certificates. |

Compare raw energy only on an identical bundle/coefficient convention. Across
versions use checked tuples and scope. R=B in current fixtures because the
previous unstarted plan is empty. No independent stability improvement is
measured here. Money, ingredients, holding and interrupted cooking are disabled.

## Likely jury questions

- **Why is this more than a factory reskin?** Batch yields and shared allocations
  interact with main/side completion and unpaired disposal. This changes the
  objective and feasible production decisions, beyond renaming machines.
- **Why quadratic?** Each meal requires two binary coverage expressions. Their
  product encodes paired service and unmatched waste directly.
- **Are these pre-solved schedules?** A program is one legal local batch. The
  optimizer must choose a compatible set and allocations. It is not choosing
  between globally optimized whole-kitchen answers.
- **Does the mixer ensure feasibility?** It preserves one choice per block.
  Cross-block clashes remain penalties, and the physical checker rejects them.
- **Could a bad hard-constraint state beat a feasible one?** With our proven
  bound P exceeds the whole objective span and a feasible idle witness exists,
  so a ground state has zero hard penalty. Heuristics can still return violations.
- **Is the quantum part useful or just easy classically?** The cell validates
  correctness and execution. Larger pilots measure performance and representation
  loss. Current evidence supports no quantum speedup.
- **What did VeloxQ add?** Actual execution of larger instances of this same
  model, exact packet integration, returned-sample validation and measured scale
  behavior. Give the final observed improvement only after its receipt exists.
- **Why not claim 2,048 qubits?** Those are VeloxQ binary variables. The current
  quantum circuits use at most 35 data qubits, simulated in a one-hot sector.
- **What about hardware?** These catering quantum results are simulator runs.
  Synthetic routing audits do not establish performance on a calibrated IBM chip.

## Work to finish, in order

1. **Us:** rehearse this story against the existing UI; prepare objective,
   evidence and conclusion frames in the same pixel/wood visual family, with
   large readable text. Keep full equations and audit detail in backup material.
2. **VeloxQ owner:** produce the capped improvement proposal and, after its
   authorization, the checked finding and comparable quality/runtime table.
3. **QAOA / VQE owners:** supply one source-hashed selected result, precise
   execution label, circuit/optimizer settings, all trial outcomes and a short
   reproducible launch. Feature the strongest measured method; do not wait
   indefinitely for every method to appear on the main stage.
4. **Us:** finalize and time the live launch, synchronize the viewer's results
   text and support frames, record the ≤5-minute video, and rehearse the live
   talk three times below 2:50. Keep a local recording and screenshots as fallback.
5. **Team release owner:** verify Stage1 files, MIT/public-repository requirement,
   run instructions, current project design/log, video URL and submission receipt.
   Official deadline is 18 October 15:00 UTC+2; live presentations start 18:00 UTC+2.

No new domain, extra constraint backlog or arbitrary variable-count target is
needed for this preparation. Freeze the result set before recording so the
spoken numbers, demo, code and docs refer to the same version.

Rules source: repository PDF `Quantum_Hackathon_2026_ERP_Challenge.pdf`, §§6–11.
Scoring is 30 points: formulation 5, solution quality 5, extension 5, then3 each for
development log, project design, video, live presentation/Q&A and consistency.
