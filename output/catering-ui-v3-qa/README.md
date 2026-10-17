# V3 catering viewer verification

Local preview: http://127.0.0.1:4192/catering/ . Verified on 17 October 2026.
This is local browser verification, not a production/deployment receipt.

- Desktop: complete-cell actual QAOA sample, multiple selected batch tokens,
  method selector, larger S3 replay and independent raw reference.
- S3 at minute75: C2 recovery clean visible, W2 attending, and the inspector
  explains repair ending60, clean70–80 and no cooking before80.
- Raw S3 at horizon200: 50/80 complete meals served, 10 component portions
  discarded, tuple (3,1,6,6), explicitly classical full-grid OPTIMAL.
- Small-cell skip-side intervention: actual handovers drop from20 to0 complete
  meals, discarded component portions rise from0 to20; tuple (2,2,1,1).
  This is explicitly manual, not another solver sample.
- Model/results dialog: objective, penalty, XY scope, actual all-eight-run table,
  source provenance and pending service results inspected in the browser.
- Portrait390×844: working kitchen composition and readable formula dialog
  inspected; temporary viewport override reset afterward.

Screenshots: desktop-kitchen.png, desktop-results.png, mobile-qubo.png.
backend-check.json independently rechecks16source views,48manual interventions,
source hashes, three larger bundle manifests, raw-plan validity and exact gzip
round trips. These checks run no solver, QPU or remote service.

The initial viewer build passed134tests; the production-order pass below adds coverage. Catering Python tests pass45cases (one optional
SDK test skipped in the lightweight environment); that Qiskit circuit-equivalence
test passes separately in .venv. The live UI performs no optimization.

## Production-order pass

The new sequence view was checked against the retained plans, without running
any optimizer or training circuit:

- Small cell: visible cooking A→C→B and packing A-main→A-side→B-side→B-main.
- Next event at minute30: B is prepared and waits for its cook at minute70.
- Packing C for A seeks minute70: C2 cleaning, K1 packing C and C1 cooking B
  appear together; A's main is packed while B's side waits for its packing slot.
- S3 Equipment view: repair20–60, waiting-for-clean60–70 and recovery clean70–80
  are distinct. Clicking recovery clean seeks its actual start and highlights C2.
- Mobile390 CSS-pixel width: no horizontal overflow; the Sequence control opens
  the clipboard and both queues are accessible. Temporary viewport overrides reset.
- Four added projection tests check actual queues/status boundaries, all16source
  views, manual missing-course behavior, event stepping and unchanged horizon.

Screenshots: sequence-desktop.png, sequence-packing.png, sequence-recovery.png.
The current site build passes138tests. Existing backend evidence remains unchanged.
