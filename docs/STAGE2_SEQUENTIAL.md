# Sequential learned factory control

`stage2/sequential.py` implements an actual causal PPO actor-critic controller for
the executable minute-grid factory. The engine calls it every 60 minutes. A
decision changes CONWIP admission, certified machining mode, dispatch priorities
and whether to request the physically delivered extra calibration kit. It has
no authority to bypass the engine's physical constraints or independent checker.

The complete initial implementation was smoke-tested on the current full profile:
real simulator rollouts, genuine gradient updates, source guards, portable JSON
policy checkpoint and process-parallel inference execute successfully. These
smoke checks establish execution and protocol correctness; they do not establish
an improvement over tuned scheduling baselines.

## Public state and decisions

The network sees 32 normalized features: elapsed/remaining horizon; sine/cosine
shift time; revealed order, shipment and completed-step counts; active and waiting
work; accepted components; available AGVs/workers/tools; AGV and stationary-battery
SOC; current revealed grid capacity/outages; incurred energy cost and overdue
orders; changes since the last observation; seven process queues; and memory of
its own previous WIP/lease action. It never receives the instance seed, future
events, hidden defect tape or unrevealed orders. Missing optional queue entries
default to zero; malformed/nonfinite public observations are rejected.

The 48 actions contain the full 36-choice static grid of WIP limits 1/2/3/4/6/8 ×
eco/standard/turbo × lease yes/no at the ordinary baseline dispatch priorities.
Twelve additional actions apply long-tail or family-grouping priorities at each
WIP level, with standard machining and the lease request enabled. Thus the action
domain includes the strong ordinary static grid rather than excluding its best
policies through a mode/priority confound. It remains a restricted controller
domain; it does not enumerate every physically possible schedule.

The lease is irreversible once requested. A later no-lease action cannot cancel
it or recover its cost. Admission reductions do not erase already admitted work.
Mode changes affect future operation starts; they do not magically change a
running operation. The engine retains all released orders and their objective
penalties even when a CONWIP policy postpones admission.

## Objective, shaping and PPO

The terminal training score is negative unfulfilled-order count, followed by
bounded normalized tardiness and total cost. Total cost includes both energy
and the calibration-kit investment. A physically invalid trace or unsatisfied
terminal battery condition receives a much larger penalty. At a fixed workload,
one extra fulfilled order dominates all possible tardiness/cost differences in
this score. The full original metrics are always retained; this is a learning
surrogate, not a proof of globally optimal scheduling or a CVaR optimizer.

A small progress potential uses observed shipped/completed counts. Intermediate
rewards are potential differences, and the final reward subtracts the final
potential and restores the initial potential. With gamma exactly one, episode
reward sum is **exactly the terminal score**. There is no undisclosed incentive
to accumulate unfinished intermediate components. Monte Carlo undiscounted
returns train the critic and form advantages; no lambda-discounted GAE changes
the return. This is tested directly, including nonmonotone potentials.

The actor and critic share two 64-unit tanh layers. PPO uses a .2 clipping range,
entropy regularization, a smooth-L1 value loss, clipped gradients, four update
epochs and shuffled minibatches. Rollouts within a batch share frozen policy
weights. Weights update only after all that batch's episodes finish. Each worker
uses NumPy inference and its own actor-sampling RNG. The scheduling solver's
`policy_seed` remains separately fixed in base weights, and neither is derived
from the environment seed. NumPy and PyTorch inference agreement is tested.

These aggregate features do not make the physical factory fully observable or
Markov. The learned controller is a reactive policy with limited explicit memory
for a partially observed process. PPO is an empirical optimization method here;
we claim neither convergence nor the existence of an optimal policy within this
feature/action class. A valid trace certifies physical execution, not policy
optimality.

## Honest comparators

Every method runs the same physical factory, checker, action domain and allowed
training seed pool:

- `ppo`: state-dependent decisions throughout the episode.
- `bandit`: the same network chooses one action from the initial observation and
  holds it for the full episode. It stores one actual decision, not 96 fictitious
  repeated decisions. It uses the same PPO update machinery for that one-step
  problem.
- `static`: budgeted finite-grid empirical policy selection, separately for each
  training workload. Broad action coverage precedes repeated training tapes; no
  duplicate configuration/action/tape is evaluated. If the grid finishes early,
  it stops rather than wasting the remaining compute.
- `random`: causal random dynamic actions, with a fixed independent evaluation
  RNG. This is an exploration control, not the sole comparator supporting a claim.
- `cem`: classical search for an eight-segment time-dependent action schedule,
  separately for each workload. Candidate schedules in a batch share the same
  environment tape and workload, making their fitness comparisons paired.
  Elite updates retain an exploration floor. In v2 a bounded candidate pool is
  reranked on paired training tapes 0–3 before choosing an incumbent. Results are
  cached only within the same source snapshot. This corrects v1's optimistic
  single-best-tape selection; the frozen v1 run remains separately identified.

The existing root static tournament can additionally supply stronger independently
tuned controls. Its better result must not be replaced by a weak default merely
to make a learned policy look favorable. Differences in policy domains should be
reported explicitly. All results retain global optimality gap as unknown.

Each method receives a requested wall-time fit budget. Initialization, rollouts,
checking and updates count toward that budget. The last batch can overrun; actual
time, episode count, transitions and summed simulation CPU-seconds are saved.
Process startup and policy inference are included. Compare the same worker count
and CPU allocation. An episode cap is useful for smoke tests, but that is not an
equal-wall-time experiment. Validation/test time is reported separately.

V2 additionally charges checkpoint-selection validation, CEM reranking, and
behavioral-cloning preparation against that fit budget. Final post-fit validation
and final held-out evaluation remain separately reported. The last completed
policy is saved as `last-checkpoint.json`; `checkpoint.json` retains the best
validation-selected policy, with its original selection episode clearly recorded.
Validation selection orders candidates by physical invalidity, unfulfilled orders,
tardiness and total cost. The initial cloned policy is eligible, so subsequent
RL deterioration does not silently discard the strong starting solution.

## Training-only warm start

`--warm-start-static checkpoint.json` initializes PPO or the contextual bandit
from an actual static-grid training artifact. Physical model hashes must match;
changing the learner source is allowed. Every teacher action must map exactly
to a current action, every workload must have a measured teacher, and the teacher
may use only declared training seeds. The program collects training-only teacher
trajectories, then fits actor labels and critic returns. Label smoothing preserves
some exploration. It resets Adam's momentum before starting policy-gradient
updates. This is supervised behavioral cloning followed by genuine RL fine-tuning.

V2.1 records an explicit checkpoint-selection role. TRAIN-only cloning rejects
a validation-selected teacher; use the static experiment's training-only
`last-checkpoint.json`. Legacy v1 static checkpoints are accepted because v1 did
not select policies using validation. The safeguard prevents silently claiming
training-only teacher selection after validation has chosen that teacher.

The artifact reports teacher checkpoint/hash, its external fit time and episodes,
teacher rollout seeds and costs, cloning states/epochs/accuracy and subsequent
RL work separately. Reused precomputation is not free: report its amortized or
end-to-end cost and give classical comparators access to the same tuned teachers.
Imitating a static teacher alone is not evidence of an improvement from RL.

Training episode logs retain the applied static action or schedule, or the neural
policy digest, plus an action histogram. CEM reranking and validation have their
own measurement logs and explicit seed roles. Raw neural weights stay in the
checkpoint rather than being repeated in each episode record.

## Splits, reproducibility and execution

Training seeds are 0–31, validation 100–115, and development test 1000–1031. The
engine/checker has already been repaired using some development seeds, so final
research claims should use a fresh root-designated holdout, such as 10000 onward,
once the model and policies are frozen. `--test-seed-start` and
`--test-seed-count` support that final evaluation without retraining.

Every checkpoint records model/blueprint/learner hashes, full action definitions,
feature names, seed roles, learning curves and resource settings. Source changes
abort an experiment before mixing results. It exports JSON tensors, permitting
safe inspection and CPU inference without deserializing a Python pickle. Evaluation
defaults to argmax for learned policies. Per-episode records keep failures as failures;
they are never dropped from averages. A valid but unfinished trace remains
distinguishable from a complete feasible solution.

V2.1 also supports `--stochastic-evaluation --actor-seeds 900000,900001,900002`.
This samples the learned policy at each decision and pairs the same actor RNG
seeds across methods, independently of environment tapes and the fixed scheduling
solver seed. Report both argmax and stochastic performance: PPO optimizes a
stochastic policy, whose argmax projection can behave differently. Multiple actor
replicas on one environment tape are correlated; uncertainty calculations should
average or cluster them by environment tape rather than claiming independent
factory scenarios. The report records unique tape count and actor seeds.

Use `--validation-actor-seeds 900000,900001,900002` to select checkpoints by
stochastic validation rather than the default argmax validation. This extra
evaluation is charged against fit wall time. The final evaluation rule and the
selection rule should both be disclosed.

An explicit `--adapt-learner-version` flag permits evaluating older frozen policy
weights with this evaluator only when every physical-source hash and the complete
feature/action definitions match. It preserves original hashes and records the
adapter. It never permits an engine/model change. Parameter values are unchanged;
the caller must inspect any feature-implementation changes before opting in.

Run from a frozen source snapshot with NumPy and PyTorch installed. CPU rollouts
dominate the workload; this small network does not justify reserving an H100.
Set BLAS/OpenMP thread limits to one when launching many worker processes.

```
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  python -m stage2.sequential --method ppo --orders 8 --seconds 600 \
    --workers 32 --batch-episodes 64 --selector priority \
    --output output/stage2-search/sequential-ppo-8

python -m stage2.sequential --method static --orders 8 --seconds 600 \
    --workers 32 --batch-episodes 64 \
    --output output/stage2-search/sequential-static-8

python -m stage2.sequential --method ppo --orders 8 --seconds 600 \
    --workers 32 --batch-episodes 64 --validation-every 5 \
    --warm-start-static path/to/static/checkpoint.json --warm-start-episodes 8 \
    --output output/stage2-search/sequential-warm-ppo-8

python -m stage2.sequential --checkpoint path/to/checkpoint.json --orders 8 \
    --workers 32 --test-seed-start 10000 --test-seed-count 64 \
    --output output/stage2-search/final-heldout-ppo-8

python -m unittest discover -s tests/stage2 -p test_sequential.py
```

Use comma-separated workloads, such as `--orders 3,8,12`, to share a contextual
network. The static/CEM comparators require those contexts to have been explicitly
measured; the current comparison does not claim unseen-workload generalization.
Use `--skip-evaluation` for training-only Slurm jobs. A fresh output directory is
required to protect previous episode logs. Checkpoints update after each batch,
so interruption preserves the last completed training stage.

This implementation is genuine sequential RL in a classically simulated factory.
It neither uses a quantum processor nor claims a quantum advantage. A fixed QUBO
selector can be passed through `--selector` to couple learned high-level control
with the already validated local action QUBOs; the resulting complete workflow
must still be compared end to end against equally tuned classical alternatives.

The primary algorithm reference is [Schulman et al., Proximal Policy Optimization
Algorithms (2017)](https://arxiv.org/abs/1707.06347). The potential-difference
principle is grounded in [Ng, Harada and Russell, Policy invariance under reward
transformations (1999)](https://people.eecs.berkeley.edu/~russell/papers/icml99-shaping.pdf).
Our finite-horizon compensated shaping is additionally checked by direct equality
of every episode's total shaped reward and its terminal score. These references
justify method choices; they do not establish that this factory policy outperforms
its measured classical controls.
