# Axion Kitchen: Q&A desk sheet

Use the short answer first. Stop after two sentences unless they ask for more.
The jury has about two minutes for questions. These answers describe the
current evidence, not the result of experiments still running elsewhere.

## Five lines to keep beside the screen

1. “Each meal needs a main and a side. One course alone is waste, not service.”
2. “A bit selects one local batch program. The optimizer chooses a compatible set.”
3. “We distinguish physical feasibility, the offered-pool optimum and the full-grid optimum.”
4. “The live action samples frozen QAOA angles locally. It does not retrain or call a QPU.”
5. “All methods use versioned inputs and the same independent physical checker.”

## Most likely questions: read these first

| Jury question | Short answer |
|---|---|
| What is the optimizer deciding? | Batch quantities, allocations, equipment, crew and timing. It selects compatible local batch programs. |
| What are you minimizing? | Weighted missed complete meals, discarded food, new batches and changes, in that priority order. |
| Why is it quadratic? | Main coverage times side coverage gives complete service. Both coverage expressions are linear in selection bits. |
| How is correctness established? | We prove the encoding and penalty bound, then compare exact references and check raw schedules independently. |
| Why quantum on an easy example? | The complete cell checks the formulation and circuit. Larger cases measure restriction and search losses separately. |
| Did QAOA outperform the controls? | The trained setup increases median per-shot optimum probability about 11x/22x over random-angle search on S2/S3 at 256 evaluations. Both are restricted portfolios; this is no classical or hardware advantage. |
| Why 35 qubits on a laptop? | The complete cell stays in a 1045-state one-hot sector. Larger frozen portfolios reach 279936 states; the dynamic replay uses its own pool. No dense 35-qubit statevector is used. |
| Should the kitchen buy another cooker? | No: in the 12-customer what-if a third cooker serves no extra meals; one flexible worker (prepare, cook, pack) serves 20 more. Classical CP, best found plans, two seeds agree. |
| Where does VeloxQ fit? | It solves larger QUBOs of the same meal model, with the same physical checker. Removing idle bits makes every returned sample valid at all three tested scales, but most are empty plans: only 143/102/62 of 512 select any batch. CP and SA still find better plans. As the engine of a checked large-neighbourhood loop over 40-bit pair sub-QUBOs, VeloxQ took its own plans to 6/7 missed meal lots at 998/2,022 bits, one lot better than 30-second CP; exact enumeration of the same pairs reaches the same U and 240-second CP is better. |

## Three questions to defend precisely

**How is this part of the manufacturing challenge?**

“Cookers are production machines, cleaning is setup-like work, and departures
are due dates. We retain precedence, qualified workers, calendars and resource
conflicts. The extension chooses shared batches and couples two component
streams through completed orders and waste.”

**How difficult is the problem you actually ran?**

“The small cell is easy classically and lets us check every relevant state.
The scheduling choices interact: x1 and x3 are each legal but clash on C2.
The larger fixture generates 18,182 local programs; the largest offered source
QUBO has 636,882 pairs. Those are measured sizes, not a hardness certificate.
We compare actual returned quality with classical references.”

**Can you explain the penalty guarantee without saying 'we tested it'?**

“Let S be the sum of absolute nonconstant objective coefficients. The objective
can change by at most S between any two binary strings. P=S+1. A hard violation
adds at least P, so an invalid string costs at least one more than any feasible
string. A feasible all-idle continuation exists after checking fixed work.
Therefore every ground state is feasible; reaching it is a separate solver question.”

This is the original compiler's sufficient global bound. The VeloxQ study uses
a separate structure-dependent deletion bound; it preserves feasible objectives
and optima while changing invalid-state energies.

If asked about feasibility versus optimization: the checker reconstructs raw
resource/worker intervals and material balance. It checks returned candidates;
it does not prove a heuristic found an optimum. The tiny exact references and
larger incumbent/bound reports provide separate optimality evidence.

## Two-minute team drill

Keep one speaker, one operator and one technical backup. Use the live script
for the three-minute slot; this sheet is for questions afterward.

| Ask without warning | A complete answer must include |
|---|---|
| What does one bit mean? | One local batch program; the solver combines programs, rather than selecting a pre-solved whole schedule. |
| Why does a lone main count as waste? | Service requires both components by departure; production equals served components plus discarded components. |
| Which solver won? | VQE has higher reported per-shot optimum probability; budgets differ. QAOA has the complete archived/live evidence chain. |
| What did VeloxQ actually improve? | Same source, equal step budget, proven equivalent representation; both feasibility and best delivered service improve. |
| Is this really 35 qubits? | Complete cell: 35 data qubits and 1,045 sector states. Larger frozen portfolios reach 279,936 states; dynamic replay pools differ. No generic dense 35-qubit simulation or hardware claim. |
| Does stability help these results? | R=B here. The general stability expression is tested, but these fixtures do not isolate its benefit. |

Give the short answer in 15–20 seconds, then stop. The operator should be able
to open the exact benchmark row/source rather than search during the answer.
If the jury asks about an unmeasured quantity, identify it and show the closest
verified result; do not substitute a rehearsed paragraph on a different topic.

Human rehearsal record (leave blank until actually performed):

| Attempt | Speaker / operator | Spoken duration | Fresh launch or disclosed fallback | One correction |
|---|---|---|---|---|
| 1 | pending | pending | pending | pending |
| 2 | pending | pending | pending | pending |
| 3 | pending | pending | pending | pending |

Target under 2:50 including operator holds. Technical repeat-execution checks
are recorded separately; they do not establish the team's speaking time.

## When the question is unclear

These bridges buy a moment while identifying what the jury wants. Pick one,
then answer the question. Do not recite several or hide a missing measurement.

- “Are you asking about the full kitchen or the restricted QUBO portfolio?”
- “Do you mean the cost of simulating the circuit, or direct classical optimization?”
- “Let me separate feasibility from optimality, because we measure both.”
- “Is your question about the encoding itself, or the solver we used on it?”
- “Could you repeat the last part? I want to answer the comparison you mean.”
- “The result we verified is [one precise result]. The broader claim would need another experiment.”
- “We haven't measured that specific quantity. What we can show is [the closest relevant evidence].”

A useful answer structure is: **claim, evidence, boundary**. Example:
“The cell's optimum is certified. Independent raw CP and exact encoding checks
agree on (0,0,2,2). That certificate applies to this declared small cell.”
Sounding obscure adds follow-up risk; a precise boundary is easier to defend.

## If you freeze: a ten-second reset

“Let me explain it through the kitchen. A bit chooses one batch program. We
select compatible batches, then independently check whether complete meals
reach their departures. Which part would you like us to unpack?”

Use this once to recover, then address their actual question. If you do not
know the answer: “We haven't measured that; our verified result is narrower.”
An unrelated speech will consume the short Q&A slot without answering them.

**What is original here? Is the formula itself new?**

“We are not claiming to have invented binary multiplication or QAOA. Our
extension connects shared batch yields, paired-course service, unpaired waste
and physical scheduling, with explicit correctness checks and representation
loss measurements.”

## The problem and loss

**What are you actually optimizing?**

“First weighted missed complete meals, then discarded component lots, then
new batches and changes to the unstarted plan. The scalar weights preserve
that exact priority order.”

If pressed: U is in priority-weighted meal lots; W is in component lots. A
lot is 10 portions. They are different units, ordered lexicographically.

**Why not just minimize cooking time?**

“Orders have fixed departures and freshness limits. Finishing one course early
doesn't help if its partner is missing, and food can become stale. Complete
service and waste capture that decision directly.”

The required Stage 1 makespan problems remain separate: A=4h, B=8h.

**Isn't catering just renaming factory machines?**

“The extension changes the decisions and objective: batch yields are shared
between customers, and main/side coverage interacts through complete-meal
service and unpaired waste. Those coupling terms are absent from plain makespan.”

**Why is the pairing quadratic?**

“For binary main coverage M and side coverage S, MS is one exactly when both
exist. Missing service is 1−MS, and unpaired food is M+S−2MS.”

On physically feasible schedules, M and S are binary.
Each coverage is linear in program bits. Expanding gives degree at most two,
so the current two-course model needs no product-register qubits.

**Could the objective reward cooking food nobody can use?**

“Every produced component is either part of a completed meal or discarded.
The independent identity is W=produced component lots−2×completed meal lots.
We check that material balance, and waste precedes batch count in the loss.”

**Are you double-counting waste?**

“No. Surplus was never allocated; orphan waste was allocated but lacked its
partner. The per-batch ledger requires those categories plus served components
to equal the batch yield.”

**Is this a financial optimum?**

“No. The implemented policy prioritizes service, then food waste and batch
usage. Monetary prices are outside this profile.”

**What does plan stability add in your examples?**

“The formula counts the symmetric difference from a previous unstarted plan.
In the current published fixtures that plan is empty, so R=B. We test the
general formula, but these examples do not demonstrate a separate stability gain.”

## Encoding and correctness

**Are you selecting among pre-solved kitchen schedules?**

“No. One program describes one locally valid batch with its quantity, timing
and resources. The optimizer must combine those batches without conflicts.”

Local enumeration is classical preprocessing. The exact-sector simulator also
enumerates its sector energies; do not imply that this preprocessing is cheap
at arbitrary scale.

**What is the price of realism in qubits?**

“The complete cell uses 32 batch-program bits plus three idle choices. Our
specified unpruned phase-start comparator uses 1,118 bits for the same cell.
That comparator is analytic, not a measured solver benchmark; pruning it would
reduce the count. Program enumeration is classical work, not free compression.”

Independently restricting the cell to one cooker gives 10 program/idle bits;
yield-one only gives 20; no sharing gives 33. These are separate restrictions,
not additive feature costs. Timing rules and paired service require no extra
registers in the program encoding, but can change the offered programs and
couplers. See the [count derivation](../PROJECT_DESIGN.md#51-the-price-of-realism).

**Why only three qubits for Stage 1 B?**

“They encode the six common job permutations, with earliest-start decoding.
We tabulate their costs classically. That preserves B's eight-hour optimum,
but it does not encode every feasible timed schedule or avoid factorial
preprocessing. The official time-indexed comparison is 72 bits, or 39 pruned.”

**Does anchor grouping discard feasible plans?**

“Two programs sharing an anchor both allocate the same unit demand, so they
cannot coexist. Every compatible offered subset gets exactly one encoding
by selecting idle in unused blocks. Restricting the offered programs can lose plans.”

**Does the XY mixer make every sample feasible?**

“It preserves exactly one choice per block. It does not eliminate cross-block
equipment, worker or duplicate-allocation conflicts. Those remain penalized
and independently checked.”

**How do you choose penalty weights?**

“P is one plus the sum of absolute nonconstant objective coefficients. That
exceeds the objective's whole bit-domain range, so a hard violation cannot
beat a feasible state, even with negative objective terms.”

If pressed: every violated hard term is a positive integer and an all-idle
continuation is feasible. Large conservative penalties can still be difficult
for heuristic or finite-precision solvers; the proof is not a convergence guarantee.

**Why don't different objective units break the weighting?**

“We bound every nonnegative integer component. Each higher-priority weight
exceeds the largest possible combined lower-priority cost. That proves the
scalar ordering equals our declared lexicographic ordering.”

**How do you know the checker isn't simply repeating the QUBO?**

“It reconstructs resource intervals, qualifications, freshness, handovers and
material balance from raw plan records. It doesn't import the compiler or
conflict graph. We also use a raw CP model without program enumeration.”

Shared schemas and basic domain helpers remain shared. Do not claim two fully
independent industrial software systems or a formal proof of every Python line.

**What did your review actually catch?**

“Two information-boundary gaps: future demand could enter an observed snapshot,
and future or malformed outages could pass validation. We now reject those
unsupported inputs. Frozen models and existing result tuples are unchanged.”

## Quantum method and results

**Why use quantum methods if CP solves the small case easily?**

“The small case certifies the formulation and circuit behavior. The larger
experiments study the effect of restricted quantum portfolios and backend
choices. We are not claiming a speedup on this cell.”

**Did quantum beat the classical reference?**

“The small quantum result matches the certified optimum, as do the controls.
The larger pilot still trails the full-grid reference. We measure how much
comes from missing choices versus search within the choices we offered.”

**What does 6/8 mean?**

“Six final retained plans equal the exact optimum of their final offered
portfolio. All eight remain worse than the full-grid optimum. Final-step
controls also tie, so 6/8 does not establish a benefit from trained cost phases.”

**Does 6/6 mean every measurement was optimal?**

“No. Each of the six runs observed an optimal sample among 4096 shots. The ideal
per-shot ground-state probabilities are about 0.30–0.73 percent in those runs.”

Feasibility and best-of-run success are separate metrics. The initializer and
mixer-only controls also find the small-cell optimum.

**What is running live? Are you retraining?**

“Fresh local sampling from the saved p=3 QAOA angles, followed by independent
checks of every returned state. The seed is fixed for reproducibility.
This is a new execution, not another independent training trial.”

The recorded kitchen is a retained schedule. The live receipt reports whether
that exact retained bitstring also appeared in the fresh sample; do not silently
relabel an old replay as the newly selected schedule.

**How many qubits are you actually simulating?**

“The circuit encoding uses 35 data qubits, including idle choices. The small
cell's invariant one-hot sector has only 1045 states, so we simulate that sector
exactly. It is not a generic dense 35-qubit statevector simulation.”

**Did you run on IBM hardware?**

“The current catering results are simulator results. We have logical/native
and synthetic-routing checks, but no catering IBM hardware outcome to report.”

**Which quantum method performs better?**

“VQE's primary held-out median optimum probability is about 12.4%/12.8% on
S2/S3; QAOA's is about 0.87%/1.01% at 256 evaluations. Both use the same offered
portfolios, but their optimizers, parameter counts, training work and final
shots differ. This is higher observed probability, not a matched-budget win.”

QAOA has 10/10 sampled optimum hits on both cases at both budgets. The primary
VQE report has 10/10 and 9/10 at 1024 shots. The five exported VQE cell/S0–S3 plans
were independently checked; the per-seed aggregates remain reported CSV results.
Both are showcased with those evidence boundaries.
Archived VQE circuit counts are a two-shifts-per-parameter heuristic, not a
validated hardware cost for the controlled gates/CVaR objective. E2 three-point
NFT is a limited experimental control; the primary E5 optimizer is L-BFGS-B.

**Where is the train/test split?**

“QAOA settings were chosen on the cell and S0/S1, then frozen for held-out
S2/S3. Angles are still optimized separately on each instance; the test checks
configuration transfer, not a single trained circuit solving unseen kitchens.”

## VeloxQ and scale

**What is VeloxQ doing in the same project?**

“It solves larger offered-program QUBOs of the same paired-meal scheduling
model. The common input version, objective and physical checker connect the
small quantum cases to the larger backend experiment.”

**Is VeloxQ a quantum hardware result?**

“No. It is the integrated optimization backend. The QAOA and VQE simulators are our
quantum-method execution paths on the same type of QUBO.”

**What is the strongest VeloxQ result?**

“We remove redundant idle choices and prove the feasible schedules and optimum
are preserved. At equal 20,000-step budgets on the 512-bit source, valid returns
rise from 17/512 to 512/512, but in that form the empty plan is always valid:
only 143/102/62 of 512 samples select any batch at actual widths 486/998/2022,
and the best plans still miss 9/11/13 of 14 meal lots. CP and same-formulation
SA still find better plans.”

These are exploratory single-job measurements. They demonstrate a checked
representation improvement, not held-out superiority or a runtime advantage.
The old cold jobs remain in the benchmark ledger rather than being discarded.

**Why is the integration nontrivial?**

“Coefficient scale, spin signs and offsets affect what problem the backend
receives. We preserve exact integer packets, recompute literal energies and
check raw returned schedules, without silently repairing them.”

Backend internal arithmetic is not independently established merely because
the uploaded packet is integral.

**Does 2048 mean 2048 physical qubits?**

“No. Those are binary variables in the VeloxQ workload. Our current quantum
circuits use at most 35 data qubits.”

**Are the large problems proven classically hard?**

“No. Finite-time CP incumbents and failed heuristic returns don't prove
hardness. We report the actual quality, bounds and runtime scope at each size.”

**How do you compare runtime fairly?**

“We distinguish preprocessing, training, sampling and checking. For the service
we separately record upload, queue, backend and total time. Backend running
time alone is not end-to-end time, and current budgets are not all matched.”

**How much allowance is left?**

“The service owner has the job ledger and quota receipts. We can show the
recorded usage; I don't want to guess the current account balance.”

The presentation runner uses zero paid service calls. Do not confuse that
with the separate owner's already executed jobs.

## Deliberate scope limits

**What happens if cooking is interrupted halfway?**

“This profile fixes whole started batches and withdraws idle capacity. It
rejects an outage that interrupts committed work. Interrupted cooking would
need a separate phase-aware state model.”

**Do you optimize when to perform the repair clean?**

“No. The current conservative policy fixes the earliest clean compatible with
committed work and qualified staff. Both the QUBO and raw reference use that
same boundary policy.”

**Which real-world features are still missing?**

“Aggregate ingredient, holding and power capacity, monetary costs and interrupted
cooking are disabled. The current model explicitly implements paired service,
shared batches, phase timing, resource/crew conflicts, freshness and cleaning.”

## If the live launch fails

“The fresh launch hasn't completed, so we'll use the retained checked result
to explain the schedule. Its source and bundle hashes are available here.”

Show the saved replay, continue, and keep the failure distinct from a completed
live solver result. One speaker answers. If a specialist detail is needed,
hand over with: “Our method owner can give the implementation detail.”

Evidence: [project design](../PROJECT_DESIGN.md),
[quality audit](CATERING_QUALITY.md), [VeloxQ report](catering-methods/VELOXQ.md).
