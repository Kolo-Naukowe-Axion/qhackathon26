# Stage 2 ideation ledger

2026-10-16. Design iterations, not measured solver experiments. User mandate: maximize coherent ambition first; simplify only in response to demonstrated obstacles.

## Iteration 1: how far beyond three machines?

| Candidate | Interesting question | Limitation as the main environment |
| --- | --- | --- |
| Large flexible job shop | Which machine/sequence/mode should each operation use? | Scale alone offers little explanation for why the factory behaves unexpectedly |
| Recovery control room | How does a factory recover from outages with work in progress? | Strong narrative, but weak if all logistics and scarce resources are imaginary |
| Energy-constrained factory | Can production adapt to tariffs, grid limits and batteries? | Can become a standalone energy-dispatch exercise if material flow is too simple |
| Multi-factory supply network | Where should components be made, stocked and transported? | Adds coherent strategic decisions, but risks replacing the shop-floor problem with a generic network model |
| Self-reconfiguring factory | Should we lease a mill, add a robot or retrain a worker? | Counterfactual decisions need a believable operational model underneath |
| Adversarial factory game | Can a policy survive an adversary's limited outages and demand shocks? | Powerful research direction, but an unconstrained adversary can simply destroy feasibility |

Decision: combine recovery, energy and physical manufacturing in one two-hall factory. Put strategic capacity decisions above it. Preserve adversarial stress as a later extension with a declared disruption budget. This retains the organizer's production-scheduling ancestry while making failures propagate through several real mechanisms.

## Iteration 2: introduce joins, not only longer chains

Proposal: manufacture pumps from three different component streams. Housing, rotor and flange share machines but take different routes. Assembly is a BOM join, not another independent job.

Why it matters: minimizing component completion times can still delay every finished pump. The controller may need to prioritize the one missing flange rather than a nearly finished high-priority housing. Heat-treatment batching creates a reason to wait, while due dates create a reason not to.

Retained: flexible machines, certified modes, family setups, batch furnaces, matched BOM joins and final QA. Need: exact unit identity and explicit component consumption; aggregate counts alone could assemble a nonexistent pump.

## Iteration 3: make the factory physically honest

Proposal: four AGVs, finite input buffers, no invisible output storage, a constrained bridge and finite batteries. A completed operation can keep blocking its machine because its part has nowhere to go.

Why it matters: another mill may increase congestion rather than throughput. A battery can be full while the only charger route is blocked. Reserving destination storage is itself a scheduling decision.

Retained: time-expanded physical movement including empty trips, shared opposite-direction edge capacity, junction occupancy, charger occupancy and explicit reservations. Deferred as a separate research refinement: continuous collision geometry. The initial model uses a declared graph discretization rather than pretending to simulate robot kinematics.

## Iteration 4: make shortcuts have consequences

Proposal: turbo modes consume more electricity and tool life and may fail QA more often. Maintenance competes for mechanics and machine time. Workers have skills and shifts. The grid can derate when the factory most needs recovery capacity.

Why it matters: speeding up everything can be worse than protecting one bottleneck. Maintenance before the rush can beat a locally better initial schedule. Overtime can be useless if the real bottleneck is a shared fixture.

Retained: explicit mode tables, portable tools, individual workers, wear/service, grid/solar/battery/cost/carbon. Need: common integer units and finite action tables to prevent rounding-created energy or unbounded time/cost tricks.

## Iteration 5: uncertainty without clairvoyance

Proposal: a causal controller receives only observations already revealed, including QA outcomes. Future orders, hidden failures and random draws remain hidden.

Why it matters: optimizing each future independently can look spectacular and be impossible to execute. A valid robust solution needs one shared prefix and legal recourse. Quality information arrives when inspections finish, which itself depends on the policy.

Retained: exogenous event tree, hidden keyed quality tapes, immutable executed prefix, emergency-triggered replanning and explicit plan-change penalties. Need: distinguish a practical quality approximation from full history-dependent stochastic optimization.

## Iteration 6: give VeloxQ a consequential role

Candidate A: encode the entire joint state space. Conceptually exact, likely enormous. Keep as a semantic reference, not the default implementation plan.

Candidate B: isolated machine-order swaps. Small, but may ignore the interactions that made the environment interesting. Reject as the only Stage 2 story.

Candidate C: closed recovery neighborhoods. Freeze history; jointly select timed production/transport/setup alternatives with power, tool, buffer and boundary-state compatibility. Proposed primary direction. Compare the same candidate pool under exact/classical/VeloxQ selection, then compare the complete resulting policies.

Critical objection: a bundle conflict graph does not automatically capture setups, cumulative capacities or downstream state. Require an explicit closure test, linking variables and independent full-environment replay. Record the restriction gap. If the closure destroys compactness, that is an experimental result, not a reason to hide missing constraints.

## Iteration 7: what would make the result memorable?

Five matched counterfactuals to investigate, without inventing their outcomes:

1. Lease a mill: does the bottleneck migrate to the bridge, power cap, QA or tooling?
2. Add one input-buffer slot: can a tiny physical change unlock a large blocked schedule?
3. Use turbo milling: does rework/power contention erase the deadline benefit?
4. Protect the current plan: how much tardiness does low schedule churn cost during a major outage?
5. Pool component production: can a batch-efficient policy starve final assemblies and lose shipments?

The three-minute demo can follow one pump through one disruption, reveal the causal cascade, then show a genuinely computed recovery and matched counterfactual. The environment can be very complex while the explanation follows one visible chain of cause and effect.

## Current conclusion and next iteration

Primary proposal: **MetalTech under pressure**, specified in `STAGE2_ENVIRONMENT.md`. All its major mechanisms belong to the intended flagship. The executable blueprint is a structural design artifact, not the engine or a solved benchmark.

Next design questions are precise: can the chosen transport/buffer semantics avoid unavoidable gridlock; can a reachable WIP snapshot be generated; which resource/state interfaces a closed QUBO neighborhood needs; and which mode/quality/maintenance tables create meaningful competing decisions instead of a single universally dominant choice? These questions should drive the next experiments, with the full environment retained.

## Iteration 8: challenge the proposal's own shortcuts

- More free optional capacity cannot worsen the true optimum if all old policies remain feasible. Negative value must be attributed to investment costs, forced changes, or the tested policy, not to a mathematical paradox.
- An eight-leaf exogenous tree is not the entire quality-information tree. Policy-dependent inspection outcomes require observation-history recourse or an explicitly declared approximation.
- Counting each component's furnace start independently overcounts nominal decision choices and omits batch-consistency constraints. The reported manufacturing-start count is a sizing audit, not a finished QUBO.
- A small recovery model is not a lossless compression of the full factory unless the candidate domain and boundary-state arguments establish that claim. Keep the unrestricted environment and report restriction gaps.
- A valid 96-hour workload description is not evidence that 24 orders can be fulfilled within 96 hours. Reachability, physical feasibility and fulfillment need actual traces and separate checks.

These objections refine the model without reducing its intended scope.
