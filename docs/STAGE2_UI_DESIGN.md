# Manufacturing demo — game-like factory with checked schedules

17 October 2026. The user explicitly prefers the richer game-like factory
style and authorized combining it with the verified recovery study. This
supersedes the preceding formal workspace design; older source-sealed receipts
remain historical snapshots.

## Design and interaction

Visual thesis: a small cutaway factory world with detailed machines, warm
material cues and readable operational status, framed by the Axion workshop.
Content plan: four recovery decisions, the factory world and selected-pump
progress, followed by mathematical explanation and evidence. Interaction thesis:
interval-driven machine activity, selectable recipe steps and event-based replay.

The four story choices load actual retained schedules: outage45/945, complete
replacement0/855, original restricted pool45/945 and enriched pool0/855.
The guided next-decision action explains what to notice, then opens results.
H3 is available in both replacement pools: missing coordinated choices cause
the original pool's loss, not a missing furnace. Story selection is playback,
not a new optimization. The setting and input data are labeled fictional/synthetic.

The two cutaway halls contain distinct turning, milling, welding, washing,
heat-treatment, inspection and assembly equipment. Workpieces, progress bars
and attending workers derive from the selected schedule. Processing uses
[start,end); worker attendance uses [start,attended_end). Availability comes
from the actual machine domain, release restrictions and calendars. Offline
machines remain selectable and explain why no assignment uses them.

The inspector follows all16mandatory steps of a selected pump: housing, rotor
and flange recipes, assembly and final inspection. The saved plan's predicted
deadline result is separate from playback completion. No shipment is inferred.
A selected operation links to its machine/worker and can seek its actual start.

Replay supports restart, next-event stepping, scrubbing, speed and pause; it
stops at the selected schedule's completion. Every plan/scenario switch pauses
replay. Manual exploration preserves time clamped to the new horizon; guided
story choices reset to minute360. Playback speed changes only the display.
The Focus factory control hides surrounding explanations for presentation;
Exit focus or Escape returns to the complete workspace. Tabs, SVG machines,
recipe buttons and seek actions support keyboard focus through redraws.
Reduced-motion preferences disable ornamental equipment effects and transitions.

## One Stage2 extension, including VeloxQ

The user clarified that VeloxQ should contribute creatively within the project.
The [official challenge](../Quantum_Hackathon_2026_ERP_Challenge.pdf) supports this:
Section5 lists VeloxQ as a Stage2 extension direction; Section11 assesses
integration/quality/scaling/insight/reproducibility; Section15 describes the
end-to-end solution and complementary classical/quantum approaches.

The model/results view explicitly groups classical references, local simulated
QAOA and the prepared larger VeloxQ QUBOs as paths within one factory extension.
Their representation scopes remain different. The same schedule checker and
capacity comparison determine operational value. Actual VeloxQ service quality
is still unmeasured; offline packet preparation is not a successful backend run.
A separate sponsor award does not imply a separate modeled project, and
simultaneous prize eligibility has not been confirmed.

## Mathematical evidence and verification

The mathematical walkthrough, representation comparison, exact cost ledger,
quantum disclosures, failed controls and provenance remain accessible. Read the
[main-model specification](STAGE2_MANUFACTURING_MATH.md) for the actual domains,
coefficients, integer hierarchy, penalty proof and reduction guarantees.
The new UI does not change any numerical campaign or compiler evidence.

The full static build passes120site tests, including six new semantic checks
for actual process/attendance boundaries, future availability, unavailable
machine selection, per-pump progress and on-time-plan versus completion state.
Desktop review checks all four measured outcomes, recipe/machine keyboard
selection, focused mode, event stepping, restart, end-state progress and the
integrated Stage2 explanation. Independent review identified replay-state and
seek-focus edges; these were fixed before the final verification.

A fresh browser action returns a checked28-qubit local QAOA result at0weighted
lateness/855minutes in0.54seconds. Artifact:
`output/recipe-bridge-live/20261017T123902Z-3797789b`.
The constructor already supplies an optimal incumbent; no speedup or quantum
advantage follows from this UI action. Browser warnings/errors are absent in
the reviewed session. Desktop screenshots and verification are saved separately
in `output/manufacturing-game-qa-v1/`. Mobile visual verification is not claimed.

The configured private-repository sync and automatic site deployment are
user-authorized. Actual VeloxQ execution, physical QPU work, public-source release,
final video and submission retain their existing holds/deferred scope.
Markdown/JSON cleanup remains explicitly deferred.
