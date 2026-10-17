# Bounded learning around the strong recovery scheduler

`stage2/adaptive_recovery.py` tests PPO and a paired CEM time policy on the same
strong physical decoder. This is a separate experiment from the earlier48-action
learner on the weaker baseline. All physical tables, transport, workers, buffers,
quality tape, stock and terminal reserve remain unchanged.

The six actions combine WIP4/6/8 with QA-worker protection thresholds0/4. Every
720minutes the controller reads the existing32 public aggregate features. Between
macro boundaries it repeats its own previous action. Learned actions retain the
context's declared routing, persistent order admission, hard tool homes, kit
reservation and physical recovery. T/F modes staystandard. The action domain is
an explicit restriction, not every legal schedule or factory strategy.

PPO uses a32→64→64 network with six actor logits and one critic value. NumPy
rollout inference is checked against Torch. It first clones actual strong static
trajectories on TRAIN0–7, then uses the existing clipped-PPO update with gamma1
Monte Carlo returns. Potential differences include terminal compensation, so
shaping sums exactly to the terminal reward. That reward prioritizes integer
missing-order count over bounded debt/cost terms; final checkpoint selection
uses the exact lexicographic validity/missing/debt/cost key. It is not a theorem
that scalarized policy-gradient updates optimize the full lexicographic objective.

CEM samples eight-segment schedules on paired TRAIN tapes. A bounded elite pool
is reranked over TRAIN0–7 before its validation challenge. This is a time policy,
not a state-adaptive neural agent. Its exploration and reranking episodes are
charged. Neither method receives hidden scenario/QA draws or the environment
seed as a policy feature. Actor randomness has an independent seed.

Each context begins with an exact static controller reproducing the measured
strong control, and that candidate remains eligible throughout validation
selection. Unlike the earlier neural-clone-only selection, learning cannot
remove the static fallback from the validation candidate set. Different contexts
may retain different policies, including the original static controller. This
protects the measured validation selection, not future generalization.

The underlying static priors are conservatively described as development-selected:
earlier research included TRAIN0–31 and validation100–115. Gradient/CEM fitting
uses TRAIN0–31 only, and repeated checkpoint selection explicitly uses
validation100–115. Reserved final tapes remain untouched until the final policy
freeze. Do not label the overall pipeline TRAIN-only or treat validation-selected
performance as held-out evidence.

Frozenv12 runs two PPO seeds2026/2027 and CEM2026, each requesting1200wallseconds
on32CPUworkers. Small networks are not the dominant cost; full factory simulations
are. No GPU is requested. The time budget is soft at batch boundaries and includes
startup, cloning, reranking and validation; actual wall/allocation costs are
reported. Existing `sequential.summary().simulation_cpu_seconds` is a misleading
legacy label for summed rollout wall time: use actual `episodes.jsonl.cpu_seconds`
for process CPU and label summed rollout wall separately.

Currentv12 logs do not preserve every rejected network/full trajectory. Selected
per-context policy blobs and exact source snapshots are retained and can be
independently replayed. `stage2/adaptive_evidence.py` provides an immutable
post-fit seal, corrected cost accounting, runtime/allocation metadata and full
selected-validation replay. This does not retroactively make every rejected
exploration episode replayable. All training episodes retain seeds, summaries
and checker outcomes; the limitation remains explicit.

Four tests cover static-control exact equivalence, public-only action features,
macro caching/actor seeds, NumPy/Torch action agreement, compensated rewards and
a development-only CEM fit retaining the static candidate. Actual one-update PPO
and CEM smokes also pass. The two PPO/CEM full fits and their selected policies
require their own completed result packages before performance claims.
