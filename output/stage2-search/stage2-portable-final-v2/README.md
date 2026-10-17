# Frozen Stage2 evidence package

This is the pre-outcome selected policy/source bundle and measured result summaries.
The complete cohort manifests/evaluations/JSONL remain at the indexed source paths;
this smaller package retains all eight predeclared leaf replays for each of three
presentations. No prettier final tapes were selected. Read the result report for
uncertainty, failures, compute costs and proof scope. No quantum advantage or
physical-QPU execution is claimed.

Use Python3.12+ from this folder. Static and small QAOA execution use the standard
library; saved learned policy loading additionally needs NumPy2.5.4:

    python verify_package.py .
    python -m pip install -r stage2/requirements-inference.txt

Fresh development demo, all physical rules enabled (output must be new):

    python -m stage2.selected_run --selection policies/strong-cheap-selection.json --method static-grid-12 --orders 12 --seed 0 --output demo-static
    python -m stage2.selected_run --selection policies/strong-cheap-selection.json --method cem6-2026-16 --orders 16 --seed 0 --output demo-learned
    python -m stage2.selected_run --selection policies/quantum-stochastic-selection.json --method no-batch-qaoa-12 --orders 12 --seed 0 --output demo-qaoa

These are development replays, not new held-out estimates. The convenience command
rejects final seeds. Actual final comparisons used256 tapes with true leaf
probabilities and actors nested within tapes. Factory clock minutes differ from
execution wall time. QAOA samples only small fixed local dispatch pools; larger
ones use recorded classical fallback. Read retained-replay-index.json for exact
measured final replay hashes and frozen source provenance.

Verify all package files against package-manifest.json. The original global policy
freeze under policies/ remains unchanged. Local sources are copied from the frozen
current-dispatch runtime; legacy comparison summaries retain their separate source
identity. Replaying the legacy policies requires the separately indexed legacy
snapshot, not substituting this runtime. No upload, publication or deployment is
performed by packaging.

If present, audit-supplement-index.json labels separate offline certificates,
accounting and diagnostic evidence. Any posthoc witness or fresh development run
there is excluded from the256-tape estimates and the24 predeclared presentation
replays. Their presence never changes the sealed selection or policy scores.
