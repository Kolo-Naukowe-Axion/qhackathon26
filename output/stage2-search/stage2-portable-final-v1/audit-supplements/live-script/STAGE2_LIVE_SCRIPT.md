# Three-minute explanation and likely questions

Use the final evidence export, not a development replay labeled as final. Rehearse
the spoken portion below at roughly 120 words/minute; spend the remaining time
showing the actual retained execution and a fresh solver launch. This is a script,
not proof of a completed video or presentation.

## Spoken script

We first solved the two required flow shops with actual QAOA simulation, obtaining
four and eight hours. Then we asked a harder question: what happens when a pump
factory has to work physically, rather than just assign operations to machines?

Each pump needs its own housing, rotor and flange to meet at assembly. Our model
has fifteen machines, ten skilled workers with shifts and breaks, and four AGVs.
Parts and tools travel, the bridge has capacity, buffers can block, tools need
service, machines wear, batteries charge, and inspections can trigger repair or
scrap. Outages, supply stress and urgent orders become visible over time.

A classical controller maintains this world. At a decision boundary it offers
legal operations to a local QUBO. Simulated QAOA selects actions that are actually
executed and checked. Integrated circuits use at most five total bits, including
slack. That is a small subproblem inside a large classical system; it is not a
five-qubit encoding of the whole factory.

We froze the policies before testing, then ran twenty-three thousand five hundred
and fifty-two executions on a shared, probability-weighted scenario protocol.
At twelve initial orders in ninety-six hours, the selected cheap controller ships
everything in about ninety-five percent of cases. A thirty-two-order stress case
ships everything in ninety-one percent over two hundred and forty hours. That
extra time causes substantial lateness; the distinction is visible here.

More elaborate methods did not always help. Look-ahead improves sixteen-order
fulfillment, but performs worse than the selected CEM schedule at twenty-four.
QAOA does not demonstrate an advantage over the matched classical controls.
We retained these failures instead of selecting only favorable examples.

The checker reconstructs physical resource use and objectives against a fresh
instance. Separately, in one audited thirty-two-demand case, a final pump must fail both
allowed inspections, and the checked schedule ships thirty-one. Lower and upper
bounds meet: one missing order is primary-optimal on that realization. We do not
claim optimal lateness, cost, or an optimal policy for every future.

Presenter note (not spoken): the 31/32 proof case is a separately labeled posthoc audit illustration, not the
first-leaf 32/32 final replay. Show its audit evidence explicitly if using that
sentence; do not attach the proof to whichever trace happens to be loaded.

## Answers worth rehearsing

| Question | Precise answer |
|---|---|
|Does the quantum component solve the whole factory?|No. It samples small local dispatch QUBOs after classical state maintenance and feasibility filtering. Larger pools use a recorded classical fallback. The master/controller restrictions and unknown full-objective gap are disclosed.|
|Where is the quantum advantage?|None is demonstrated. At 12 orders QAOA's mean missing is worse than SA/uniform; both primary family-adjusted intervals include zero. This does not prove equivalence or rule out untested algorithms.|
|What is learned?|The selected CEM artifact is an eight-segment time schedule, not state-reactive RL. PPO is state-reactive but its 16-order result is matched in fulfillment by a constant control; a rare actual switch worsens secondary metrics. No useful adaptive-RL benefit is established.|
|Why not use all the H 100 s?|The measured simulator and small policy search ran efficiently on CPU. The complete final campaign used 70.42 allocated CPU-hours, with 68.58 measured episode CPU-hours. A saved CEM policy needs only NumPy. We found no justified GPU workload for these experiments; recorded GPU-hours are zero at Slurm's reporting resolution.|
|Can a classical exact solver beat this?|On the separate deterministic two/three-pump fixtures, CP proves optima and beats heuristics. Four pumps currently has an interval [1480,1567] minutes, with a bounded follow-up pending. Those fixtures relax many full-factory mechanisms and do not establish a flagship global gap or classical impossibility.|
|Does a missing order mean infeasible?|A partial execution can obey all physical constraints and miss demand. The objective counts those misses. Only a necessary bound or matching primary certificate justifies a particular impossibility/optimality statement. A tested controller's failure is not an infeasibility proof.|
|Why stop the stress test at 32 initial orders?|There are 34 blanks/type after scheduled delivery and possibly two rush orders. 32 is the largest initial count with no material-only obstruction on every branch. 33/34 initial already have all-success probability at most 50%;35+ at most zero. Quality, timing and scheduling can reduce those ceilings.|
|Why show a posthoc proof example?|It illustrates an existing recorded outcome. The selection rule was declared before one audit-only rerun, which reproduces original metrics. That replay is excluded from all 256-tape estimates and predeclared presentation replays; it establishes one realized primary optimum only.|
|Is this an industrial digital twin?|No. It is an explicit synthetic environment with exported assumptions. Features, exercised mechanisms and binding constraints are distinguished. Industrial calibration and external validation are not claimed.|
|Is the project submitted and public?|That is separate from technical evidence. The requirement audit last verified a private repository; publication remains held, and completed video/form/team receipt are unverified. Check the actual release state before answering on presentation day.|

The result counts, accounting and reference status must be checked again against
[the current decision page](STAGE2_RESULTS.md) before recording; do not recite a
pending reference result as complete. The research literature, novelty limits and
full requirement matrix are in [the judge-facing explanation](STAGE2_JUDGES_EXPLANATION.md).
