# Root-document consistency proposal — NOT APPLIED

This is a bounded read-only review of saved evidence, prepared on 17 October
2026. Another chat owns Stage1 and root presentation documents. Neither
`PROJECT_DESIGN.md` nor `README.md` was edited. This memo grants no permission to
publish, push, deploy, change repository visibility or run remote backends.

The current Project Design opening says B is planned to use VeloxQ and leads
with the older time-indexed formulation. Its later architecture paragraph and
the selected artifacts already describe the actual compact QAOA results. The
README material index still calls the Project Design a planned solver interface.
The proposed patch changes only that opening status/problem description and
the single README material-index line. Historical experiment sections remain
intact, including earlier time-indexed/domain-wall work and remote preparation.

Saved `output/stage1-selected.json` points to the compact QAOA Aer runs. Both
root schedule JSON objects exactly match their selected run schedule JSONs.
Instance identities, methods, model/instance canonical hashes and saved
verification records agree: A uses one bit, one QAOA layer and makespan 4 h; B
uses three bits, two layers and makespan 8 h. Each saved run records 4,096
feasible measurements out of 4,096. This review did not rerun verification,
tests, scheduling or a solver; it checks literal saved-record consistency.

The selected pairwise-order construction retains all two/six earliest-start
common job orders and pays factorial classical cost tabulation. In B, the
three-bit representation preserves six common orders, not arbitrary independent
machine orders or idle-time schedules. Its scoped information minimum must not
be confused with the separate three-bit H8 deadline-feasibility reduction
retaining five machine-order classes, including a non-permutation order. The
patch links the existing compact formulation and claim register to keep those
claims distinct. It makes no quantum advantage or scalable compiler claim.

The current module docstrings agree with that division: `solver/sequence.py`
explicitly discloses all-permutation tabulation and excluded timing/order
domains; `solver/stage1.py` describes offline time-indexed preparation, not a
VeloxQ execution; `solver/compact.py` describes the compact experiment/bundle
orchestration. Current hashes match 12 of the 13 solver source hashes recorded
in each selected run. The exception is `solver/compact.py`; its exact old and
current hashes are retained in `report.json`. No reason for that drift is
inferred, and this review does not certify replay under the whole current
source tree. The selected model, root schedules and their recorded source
identities remain unchanged; `solver/sequence.py`, `solver/quantum.py` and
`solver/verify.py` match the recorded hashes.

Files in this proposal:

- `proposed-root-documents.patch`: exact **unapplied** unified diff, anchored to
  the current root documents. Review ownership and regenerate if either base
  hash changes; do not apply it blindly to newer work.
- `report.json`: base document hashes, selected artifact identities, canonical
  model hashes, saved evidence file hashes, source-hash agreement/drift and
  current module docstrings.
- `build_proposal.py`: standard-library read-only evidence check and proposal
  generator. It writes only this proposal directory and confirms both original
  root hashes remain unchanged.

The underlying hold and ownership are intentional. The document owner can
review this concrete patch without replacing historical evidence or treating
the proposal as permission for a release.
