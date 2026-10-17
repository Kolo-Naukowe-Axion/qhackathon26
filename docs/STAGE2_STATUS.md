# Stage 2 current status — 17 October 2026

**The agreed non-VeloxQ technical merit scope is complete: all 14 core
requirements passed.** Actual VeloxQ measurements, the synchronized final video,
human rehearsal and public release/submission remain open. Completion does not
establish prize eligibility, a winning score or quantum advantage.

**UI and math refinement after technical closeout:** the
[workspace design record](STAGE2_UI_DESIGN.md) documents the new four-step
recovery rail, separate views and114passing site tests. Desktop browser checks
pass, including a fresh local28-qubit0-lateness/855-minute result and corrected
keyboard/comparison interactions. Mobile visual verification is not claimed.
The [main-model mathematics](STAGE2_MANUFACTURING_MATH.md) specifies the actual
variables, constraints, QUBO coefficients, penalty proof and reduction boundaries.
Older receipts certify their own source snapshots; numerical campaign results
remain unchanged.

Start with the [manufacturing studio](http://127.0.0.1:4192/manufacturing/#merit),
[combined design](STAGE2_COMBINED_DIRECTION.md) and
[acceptance matrix](STAGE2_MERIT_ACCEPTANCE.md). This page supersedes the earlier
pause/proposal status in historical factory and planning notes.

## The completed technical story

The same two-pump model retains all 32 mandatory operations, qualified workers,
calendars, assembly joins, family changeovers and transfer lags. Native complete
references prove 45 weighted late minutes unavoidable after a furnace outage;
replacement heat capacity available from minute 360 restores zero lateness and
855-minute completion. Both pumps are due at minute 900. Inputs are synthetic.

| Replacement-case representation | Bits / couplers | Checked result and scope |
|---|---:|---|
| Original operation pool | 781 / 26,307 | Exact pool optimum stays 45 late / 945 minutes; excludes valuable coordinated choices |
| Deterministically enriched pool | 2,078 / 196,228 | Exact pool optimum restores 0 late / 855 minutes; still a restriction |
| Support-pruned complete optimization encoding | 2,499 / 381,371 | Retains the declared complete grid model; native optimum 0 / 855 |
| Exact hard-deadline query | 818 / 33,817 | Zero energy iff the original-model deadline query is feasible; changes the optimization question |

The [whole-recipe QAOA bridge](STAGE2_RECIPE_BRIDGE.md) retains every operation
through eight component groups in restricted trajectory pools. Caps 2/3/4 use
18/28/36 logical qubits. Across two known inputs and three seeds per cap, QAOA
and one-hot annealing each return 18/18 valid encoded optima; uniform sampling
returns 6/18. Uniform also contains two raw-valid operation plans with invalid
completion registers; they do not count as encoded optima. The constructor
already finds the optimal incumbent, sector energies are enumerated classically,
and method budgets differ. Six 18-qubit circuits receive independent
full-Hilbert replay; larger circuits receive logical resource audits.

[Six feature ablations and scaling](STAGE2_REALISM_FRONTIER.md) measure domains,
couplers, coefficients and quality. Larger 64/128-operation native references
remain UNKNOWN with checked bounds. [Economics](STAGE2_CAPACITY_ECONOMICS.md)
values four checked plans with an exact ledger and 135 sensitivities. At the
declared synthetic prices, the complete recovery plan permits an event fee of
474.54 PLN. The illustrative purchase-price threshold is 19,923.63 PLN under
explicit exposure, probability and discount assumptions. This values saved
priority-optimal schedules; it is not weekly monetary optimization or calibrated
industrial ROI.

[Four cold SDK files](STAGE2_SPONSOR_PACKETS.md) cover deadline, enriched and
complete models, including a matched-penalty enriched control. Their 815,121
coefficient/constant checks pass offline. Service behavior is unmeasured. Cold
operation-level annealing produces 0/640 raw-valid samples at its stated budgets;
fast native CP queries prevent treating that as evidence of intrinsic hardness.
Failed boundary, trajectory-selection and counting attempts remain preserved.

## Validation and how to run

The final implementation receipt records **52 targeted Python tests, 113 site
tests, syntax checks and a successful static build**. The browser action produced
a fresh, checked 28-qubit local simulation with all 32 operations, zero weighted
lateness and 855-minute completion. No VeloxQ or physical QPU was used.

- [Technical acceptance](../output/merit-audit-final-v1/requirements.json): 14/14 core requirements passed at closeout.
- [Test/build receipt](../output/merit-final-checks-v1/report.json): commands, logs and 269 source hashes.
- [Independent closeout consistency](../output/merit-document-consistency-v2/report.json): 20 checks, 34 files and 116 local links at that snapshot.
- [Browser receipt](../output/manufacturing-merit-qa-v1/report.json): checked fresh run, screenshots and UI source hashes.

The linked receipts are immutable dated snapshots. The acceptance matrix points
to the newest documentation verification after subsequent documentation edits.

```sh
.venv-stage2/bin/python -m stage2.entry_demo --port 4192
```

Open `/manufacturing/`. The static build displays retained evidence; fresh QAOA
requires the loopback Python server. The older `/entry/` page is a separate
smaller validation study; `/stage2/` is the richer physical-factory replay.

## Remaining work and boundaries

| Work | Status / next action |
|---|---|
| Actual VeloxQ pilot and sponsor comparison | Held pending explicit authorization for service/credit use; follow the [runbook](STAGE2_VELOXQ_RUNBOOK.md) |
| Final synchronized video | Pending; the existing manufacturing-v3 cut predates the latest results and stays a review draft |
| Live presentation and Q&A | Human rehearsal required; use the [current script](STAGE2_LIVE_SCRIPT.md) |
| Public MIT release, hosting and submission | Held; review the exact release and complete the [submission duties](STAGE2_SUBMISSION.md) |
| Calibrated weekly monetary optimization, stochastic robustness, QOBLIB trials | Optional further work, outside the accepted core |

The subsequent repository sync was explicitly authorized, including the existing
automatic site deployment. It preserves the private repository and all evidence;
Markdown/JSON cleanup is deferred. It does not authorize service credits,
physical QPU execution, a public-source release or final submission.
