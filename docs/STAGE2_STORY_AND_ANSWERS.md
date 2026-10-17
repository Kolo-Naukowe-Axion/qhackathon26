# MetalTech's Monday — working story and answer bank

Draft, 17 October 2026. The user asked for the story, explanations and answers
now, with video production, demo/presentation polish and formal release work
left until after VeloxQ results. This is narrative preparation, not a final
script, recording, award claim or authorization to use VeloxQ.

The people, dialogue and business setting below are invented. The scheduling
numbers come from the retained synthetic manufacturing model. MetalTech is the
challenge setting, not a real industrial customer or a claimed deployment.
Time is stated relative to planning start so the story does not invent clock
alignment for the model's calendars, tariffs or night premiums.

## The story

It is the start of MetalTech's planning day. Marta, the production planner,
has two pumps to finish within the next fifteen hours. Each pump needs its own
housing, rotor and flange. Those components have to meet at assembly, followed
by final inspection: sixteen operations per pump, thirty-two in total.

Maintenance brings bad news before planning begins: one heat-treatment furnace
is unavailable. Marta cannot solve that by moving a single bar on a Gantt chart.
A different machine needs the right worker, that worker has a calendar, and a
component finishing earlier may still wait for its matching parts or inspection.

Maintenance offers extra furnace capacity from six hours into the day. Marta
asks a concrete question: "Will reserving it actually save the deadline?"

Our first compact model says the best schedule still finishes forty-five
minutes late. In the illustrative cost example, it gives almost no operating
saving. Paying a hundred PLN for the extra capacity looks unattractive.

But that is a conclusion about the restricted model. The complete scheduling
reference finds a different answer: both pumps can finish on time, with the
last inspection completed forty-five minutes before the deadline. Under the
declared synthetic prices, that plan improves net cost by374.54PLN after the
hundred-PLN capacity fee.

The extra furnace did not change between those two calculations. The scheduling
choices represented by the models did.

We investigate what was lost. The781-bit pool has retained every mandatory
operation, and it even contains the replacement-furnace assignment rows. What
it misses is a compatible combination of choices across the rest of the recipe.
Deterministic enrichment restores an on-time optimum using2078bits, compared
with2499bits in our complete optimization encoding.

We also ask a narrower question: "Can both due dates be met at all?" An exact
818-bit deadline formulation answers that feasibility question without retaining
the original monetary or tardiness/makespan optimization landscape.

For the quantum experiment, we recombine complete component routes while keeping
all32operations and cross-component rules. QAOA runs on18–36logical qubits,
alongside uniform sampling, annealing and exact references. The classical
constructor already supplies the best plan. We do not give quantum sampling
credit for discovering the furnace's value.

VeloxQ is the next measured backend comparison on the larger scheduling models.
Its result is deliberately left open until it has actually run.

## Opening and takeaway candidates

Opening: "MetalTech has two pumps due today and a furnace out of service.
There is spare heat capacity—but our first compact model says it cannot save
the deadline. Is the capacity useless, or did the model discard the schedule
that makes it useful?"

Takeaway: "Before deciding what capacity is worth, check whether your scheduling
model can represent the plan that uses it."

Technical thesis: "We measure representation loss separately from solver loss,
then test reductions and solvers against the same original manufacturing rules."

A title candidate: **The spare furnace our compact model could not use well.**

These are working lines, not an imposed final brand or presentation sequence.

## Facts the narrative must preserve

| Story element | Actual evidence / boundary |
|---|---|
| Two pumps due in15hours | Both terminal due dates900minutes; all32operations mandatory |
| Furnace unavailable before planning | Known withdrawn capacity; not a stochastic surprise revealed during execution |
| Replacement usable after6hours | Replacement heat resource H3 usable from360minutes |
| Outage's best schedule45minutes late | Complete native reference: weighted tardiness45, makespan945 |
| Complete recovery finishes45minutes early | Complete reference: weighted tardiness0, makespan855, due900 |
| Original compact model stays late | Native restricted-pool optimum45/945;781bits |
| Enrichment restores recovery | Native enriched-pool optimum0/855;2078bits/196228couplers |
| Complete optimization encoding |2499bits/381371couplers after exact support pruning, not a proven minimum encoding |
| Exact deadline formulation |818bits/33817couplers; zero iff the declared deadline query is feasible |
| Hundred-PLN fee decision | Synthetic ledger: complete recovery+374.5417PLN net; original pool−95.5958; enriched+372.0208 |
| QAOA experiment | Same32operations through restricted trajectory pools, not a quantum solve of2499assignment bits |
| Successful quantum returns |18/18valid encoded optima across2known inputs×3caps×3seeds; annealing18/18too |
| VeloxQ | No service result yet; no numerical outcome enters this draft |

The study records final-inspection completion, not actual delivery, physical
shipment, a carrier cutoff or a real customer's financial loss. The fee is a
scenario parameter, not a supplier quote. The purchase threshold is a separate
conditional sensitivity; it is not the main story or evidence of calibrated ROI.

## Short answers to likely questions

### What did you add beyond the baseline?

We replaced the fixed route/machine baseline with complete joined pump recipes,
choice of eligible machines and qualified workers, calendars, transfer and travel
rules, machine-family setups, and terminal due dates. The question is whether
replacement capacity rescues deadlines, and how encoding restrictions change
that answer. Each result has a same-model classical reference.

### What is the main contribution?

A checked manufacturing decision whose apparent value changes with the represented
schedule domain, plus an audited comparison of exact pruning, lossy restriction,
enrichment and a changed feasibility query. The encoding and quantum techniques
are established methods; we are not claiming a new general theorem or a general
quantum speedup.

### Why isn't this just a Gantt chart with extra features?

The schedules are outputs of explicit models. Native references prove what the
complete and restricted domains can achieve. The meaningful result is that the
original compact model misses a recovery plan even when its own optimum is found.
The chart makes that consequence inspectable.

### Isn't the781-bit example simply a weak model?

Yes, it is a failed restriction. We keep it as a measured failure and test a
stronger2078-bit pool that restores the same optimum. The claim is not that every
small model fails or that2499bits are necessary. Candidate selection has to be
validated against operational quality, not size alone.

### Did the compact model forget the replacement machine?

No. The original pool already retains its assignment rows. Recovery needs
coordinated compatible choices elsewhere in the recipes. Keeping a machine in
the model does not guarantee keeping a useful complete schedule that uses it.

### Why not always use818bits instead of2499?

Those models answer different questions. The818-bit model asks whether all hard
deadlines can be met, optionally with a completion cap. It does not rank all
schedules by the original weighted-tardiness/makespan objective. A positive
heuristic energy cannot prove infeasibility; a checked zero-energy witness
establishes feasibility, and native references supply the saved impossibility
certificates.

### What is quantum about it?

We emit and locally simulate QAOA circuits over component-route choices for all
32operations. One-hot-preserving preparation/mixing keeps one choice per group;
resource and precedence interactions remain in the cost. The logical registers
are18–36qubits. All18circuits are parsed/transpiled; only the six18-qubit circuits
receive independent full-Hilbert probability replay. There is no physical-QPU run.

### Does QAOA improve the classical constructor?

Not in this successful recovery study: the constructor already finds the best
incumbent. QAOA and annealing both reach the restricted optimum. The result
establishes correct quantum integration and measured sampling behavior. It does
not establish added practical optimization value or quantum advantage here.

### Is sector simulation hiding the hard part?

It makes this experiment classically tractable by enumerating the invariant
sector and its energies. That already reveals the optimum to an observer and
must be charged as preprocessing. It saves classical memory relative to a full
state vector; it does not reduce logical circuit qubits or demonstrate scalable
quantum computation.

### Why not just use CP-SAT?

For these small synthetic recovery queries, CP-SAT is a strong practical baseline
and is fast. It also gives independent certificates for auditing formulations.
We are testing where each formulation and solver is useful, not asserting that
a QUBO is automatically a better way to schedule every factory.

### Is VeloxQ better?

We do not yet know. The models and exact offline packets are ready. The planned
bounded comparison will measure valid schedule quality, target attainment,
preparation/service/decoding time and cost against strong controls. We will state
the result from returned samples, not infer it from model size or another paper.

### Is this a realistic factory?

It is a synthetic deterministic manufacturing-planning model with explicit
resource interactions. It is not calibrated industrial data. Capacitated AGVs,
blocking buffers, stochastic quality and physical shipment belong to the separate
rich factory replay, not the model behind these recovery certificates.

### Does374.54PLN mean the factory really saves that much?

It is the difference between two checked saved plans under declared synthetic
rates, after a hypothetical100PLN capacity fee. The ledger includes attended
labor, night premiums, machine starts, active/standby/base electricity and
lateness. These schedules optimize deadline priority, not monetary cost. The
number is conditional arithmetic, not an industrial savings forecast.

### Why stop at32operations?

That is the complete recovery example with exact references and an integrated
quantum bridge. We also study64/128operations and report construction size,
bounds and UNKNOWN native status honestly. More operations alone would not
establish quality, scalability or advantage.

### Did the mentor approve this direction?

The supplied [mentor reply](STAGE2_MENTOR_FEEDBACK.md) expresses a preference for
staying in the factory/ERP context, pending consultation with other jury members.
Our direction follows that preference. It is not approval of our implementation
or a statement about how the full jury will score it.

## VeloxQ section to complete after the experiment

Keep an empty results slot for the actual problem/formulation, variables/couplers,
returned feasible objective or query result, reference/bound, per-seed failures,
number of samples, full time/cost accounting and what the backend changed for
the manager's decision. No invented performance number or prewritten win claim.

If the service shows a useful region, describe its measured size, budget and
quality limits. If it is slower or less reliable than the classical controls,
state that and preserve the negative result. Final video and demo wording should
follow the measured outcome.

## Evidence pointers

- [Current scope and acceptance](STAGE2_STATUS.md)
- [Full recovery and independent references](STAGE2_MANUFACTURING_STUDY.md)
- [Nested operation enrichment](STAGE2_CAPACITY_FRONTIER.md)
- [Exact deadline query](STAGE2_DEADLINE_DECISION.md)
- [Whole-recipe quantum study](STAGE2_RECIPE_BRIDGE.md)
- [Synthetic economics and assumptions](STAGE2_CAPACITY_ECONOMICS.md)
- [Backend comparison protocol](STAGE2_VELOXQ_RUNBOOK.md)

Narrative drafting changes no experiment, source model, UI, stored measurement,
external permission or release state.
