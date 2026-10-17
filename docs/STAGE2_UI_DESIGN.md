# Manufacturing workspace — current UI revision

17 October 2026. This revision responds to the user's assessment that the long,
flat manufacturing page was visually weak. It implements the working story in
the actual UI; final recording, deployment and submission packaging remain later
work. Numerical experiment inputs/results are unchanged.

## Design and behavior

Visual thesis: an industrial planning workspace with a dark navigation rail,
a light work surface, readable type and the actual shop floor as the visual
anchor. The existing Axion mark and Manrope type remain; broad gray report panels
are replaced by a clear frame and fewer simultaneous views.

Content plan: the left rail establishes the fictional two-pump recovery scenario;
the main heading shows the active question and measured outcome; the floor and
resource inspector show the selected saved plan. Four steps select actual
retained schedules: outage45/945, complete replacement0/855, original restricted
pool45/945 and enriched pool0/855. Fiction and synthetic measurements are labeled.

Interaction thesis: selecting a step updates the schedule, result and inspector;
playback reveals processing state; tabs expose recipe/timeline, mathematical
explanation, results and answers without stacking them below the floor. Motion
is restrained and respects reduced-motion preferences.

The four view tabs support native focus and arrow/Home/End navigation. Advanced
scenario and schedule selectors remain available in an expandable control area.
The model/results view retains the full tables, cost controls, local QAOA action,
failures and provenance. Selecting a representation opens its actual schedule.
The questions view explains representation loss, quantum contribution and scope.

The mathematical explanation includes a selected assignment example, the
weighted-tardiness/completion objective, one-hot and forbidden-pair quadratic
penalties, completion consistency, and the checked-witness penalty argument.
It distinguishes the assignment optimization encoding, deadline feasibility
query and restricted component-route quantum bridge.

## Verification and limits

The semantic story test checks all four UI choices against the saved original
models and due dates. All114site tests, syntax checks and static build pass after
the redesign. An initially failed build exposed a stale source hash in the older
Start guide after the preceding documentation update; its read-only export was
regenerated from retained evidence, with both frozen evidence exports unchanged.

The loopback Python preview now uses ThreadingHTTPServer, so an idle browser
preconnection cannot monopolize a single-request server. Host/Origin checks,
request bounds, allowed cases and fresh-run behavior retain their prior scope.
No remote solver or credentials are used.

Desktop browser verification passed after the user loaded the HTTP preview.
All four story choices display their expected measured outcomes; keyboard SVG
selection preserves focus, keyboard tab navigation works, and representation
selection returns focus to a visible floor tab. Nominal comparison now lives in
the visible timeline; People comparison uses attendance rather than machine
processing duration. The math panel and answer view were inspected visually.
The fresh action completed a28-qubit local simulation in1.43seconds, returning
a checked0-lateness/855-minute schedule; its result notice remains visible after
switching to the floor. Browser warning/error logs are empty. Source review
independently identified the five interaction issues; all were corrected.

The prior browser policy block was resolved by the user loading the actual HTTP
preview. No alternative browser or policy workaround was used. Desktop screenshots
and current sources are retained in `output/manufacturing-workspace-qa-v1/`.
Responsive CSS is implemented; mobile visual verification is not claimed.
The full [mathematical guide](STAGE2_MANUFACTURING_MATH.md) independently checks
raw-model semantics, polynomial coefficients, penalty proofs and reduction scope.

The earlier acceptance, browser screenshots and test receipts describe their
own prior source snapshots. They are preserved, not silently re-sealed as proof
of this revised layout. Mathematical and numerical evidence remains linked by
[current status](STAGE2_STATUS.md), [the study](STAGE2_MANUFACTURING_STUDY.md),
and [the working story](STAGE2_STORY_AND_ANSWERS.md).
