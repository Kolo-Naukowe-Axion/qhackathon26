# Axion Kitchen — speaker pack

Use this beside the live studio. The core route is 2:45; the limit is three
minutes, followed by roughly two minutes of questions. The 4:52 submission
video is a separate deliverable, not the live slot.

## Before the call

- One speaker, one operator; method owners answer specialist follow-ups.
- Open the [live studio](http://127.0.0.1:4193/?mode=live).
- Also open [benchmarks](https://qfactoria.com/catering/benchmarks/),
  [capacity](https://qfactoria.com/catering/benchmarks/#capacity) and
  [video fallback](https://qfactoria.com/video/).
- Use P to hide operator controls, F for full screen, and R at the first spoken word.
  Right/Left changes chapter; Space plays. The rehearsal clock keeps counting during holds.
- Start the local studio if needed:

```sh
.venv-catering/bin/python scripts/serve-catering-showcase.py --port 4193
```

Use the already configured interpreter if its directory is named `.venv-stage2`.
Do one rehearsal with the real speaker and operator before presenting.

## Core live route

| Target time | Operator | Speaker |
|---|---|---|
| 0:00–0:20 | Start R. Play the four-second opening, show both Stage 1 schedules for five seconds, then explain the factory-to-kitchen mapping. | Axion Kitchen. Factory baselines: four and eight hours, both checked optimal. Our extension chooses shared batches, workers and phase times under freshness, calendar and outage constraints. Cookers are machines, cleaning is setup, and departures are due dates. Complete meals come first, then waste, batches and changes. |
| 0:20–0:36 | Point to the actual x1/x3 cooker conflict; the retained plan uses x11 on C1. Play through both departures. | Two customers share a twenty-portion side batch. One Main B option clashes with it on C2. The checked QAOA plan instead chooses Main B on C1, so both orders leave complete. |
| 0:36–0:43 | Show the checked side-batch removal. | Remove the side: zero complete meals and twenty wasted portions. This is a manual intervention. |
| 0:43–0:59 | Explain the actual x3 operation timeline and same-anchor exclusivity. Play past halfway; point to product(...) and penalty=span+1 in the compiler excerpt. | A bit selects a local batch and its schedule. Same-anchor programs share demand, so each block chooses one or idle. Conflicts forbid clashes. The code expands coverage products and sets the penalty to span plus one. This cell uses thirty-five bits. |
| 0:59–1:20 | Explain MS and waste first; after 60% the screen shows the range bound and penalty inequality. State the ground-state guarantee. | Linear main and side coverage multiply into quadratic service and waste terms. Priority weights dominate lower costs. For hard constraints, the objective range is at most S. Set P to S plus one: every invalid state costs more than every feasible state. That proves the ground-state guarantee. |
| 1:20–1:37 | Click Run trained QAOA. Only after completion, read actual meals and waste aloud: expected 20 meals/0 waste. If launch fails or values differ, describe the actual receipt and use the labeled retained fallback. | Return to the original choices. We run the saved depth-three circuit, draw four thousand ninety-six fresh samples, and independently check the outcomes. |
| 1:37–1:57 | Compare trained and random probabilities, then point to the restriction gap. | On both held-out disruption cases, QAOA finds the offered-pool optimum in all ten seeds. Random-angle search also hits all ten on S2. With two hundred fifty-six evaluations, optimum probability per shot is about eleven and twenty-two times random-angle search. The full kitchen still has better schedules than these restricted portfolios. |
| 1:57–2:09 | Show the same-circuit CVaR baseline and latest Gibbs concentration result. State exact-gradient scope. | Our latest VQE uses CVaR then Gibbs loss: ninety-nine point five percent offered-optimum probability in both disruption cases. Exact gradients; this staged gain did not survive shot-noise emulation. |
| 2:09–2:28 | Follow the loop, then read the three starting and final missed-lot counts. Distinguish total adapter time from backend time; retain the exact-control and longer-CP comparison. | VeloxQ starts from its own plan and repeatedly changes two blocks. Missed meal lots fall from nine to seven, eleven to six, and thirteen to seven. All improvements pass the checker. Exact neighborhood controls do as well or better; longer classical runs still win. |
| 2:28–2:38 | Distinguish the 1,045-state correctness cell from the 18,182-program generated domain and the offered QUBO tiers. | Small cells test correctness. Larger inputs generate eighteen thousand programs with shared-resource conflicts. More variables alone do not establish hardness; benchmarks show quality and runtime. |
| 2:38–2:45 | Show final handovers and the three development-log decisions; stop. | Twenty meals, zero waste. We fixed cleaning, paired main and side, and proved idle elimination. |


After the fresh receipt completes, read the actual values. For the checked setup:
“The receipt shows twenty complete meals and zero waste.” Do not read this
sentence if the receipt differs or the launch has not completed.

## Optional business close

Use this instead of the last sentence, only if rehearsal leaves time. Finish
before 3:00; otherwise keep the capacity tab for questions.

“The same model also supports capacity decisions. In the best plans found,
a prep or packing helper adds twenty meals; a third cooker adds none.
That comparison is classical, under equal budgets.”

Show [Capacity](https://qfactoria.com/catering/benchmarks/#capacity).
This is an observed comparison, not a proof equipment can never help or an
ROI calculation. Prices were not supplied.

## Ten-second answers

| Question | Answer |
|---|---|
| What does one bit represent? | One locally legal batch program: quantity, allocation, equipment, worker choices and timings. The solver must combine programs into a compatible full plan. |
| Why is this manufacturing? | Cookers are machines, cleaning is setup work and departures are due dates. Shared batch yields and paired main/side fulfillment add decisions and couplings beyond makespan. |
| What is the loss? | First weighted missed complete meals, then discarded food, new batches and plan changes. Higher-priority weights dominate every possible lower-priority contribution. |
| Why quadratic? | Main and side coverage are linear in program bits. Their product MS counts complete service; M+S−2MS counts unpaired components on feasible plans. No product ancillas are needed for two courses. |
| How do you guarantee feasibility? | With S the sum of absolute nonconstant objective coefficients, objective variation is at most S. P=S+1 makes any hard violation worse than every feasible state. This guarantees feasible ground states, not that a heuristic reaches one. |
| Why can a laptop simulate 35 qubits? | The circuit preserves a one-hot sector: the complete cell has 5×11×19=1,045 states, rather than a dense 2^35 statevector. Only 59 of those sector states are physically feasible. |
| Is this quantum advantage? | No. We demonstrate a checked formulation and quantum-method experiments. Classical references expose both restricted choices and search quality. |
| Why the new VQE loss? | CVaR at alpha 0.1 stops rewarding concentration once the best 10% is optimal. Gibbs keeps rewarding more probability at low energy. In exact simulation, median offered-optimum probability rises from 12.37/12.79% to 99.54/99.55% on S2/S3. |
| Is VQE better than QAOA? | Latest VQE has higher measured per-shot optimum probability on these same portfolios. Budgets, parameters and final shots differ, so it is not a matched-budget overall ranking. The live execution uses QAOA. |
| Is 99.5% a hard limit? | No. It reflects the declared stopping threshold. Ten-seed aggregates come from retained CSVs; all five exported seed 0 parameter vectors were independently replayed. |
| Would this VQE work on hardware? | We report exact-gradient simulation. The staged improvement did not survive shot-noise emulation, and these gradient circuits are costly. No physical-QPU result is claimed. |
| What did VeloxQ actually do? | It drove a checked two-block replanning loop, starting from its own plans. Missed meal lots fell 9→7,11→6,13→7 at 486/998/2,022 bits; 71 submissions, 565 s total adapter time, 127 s backend time, excluding starting-plan generation. |
| Did VeloxQ beat the controls? | It improves its own starting plans. Exact neighborhood controls match or improve quality, and longer CP runs remain better. We retain failures and distinguish backend from total time. |
| Which resource should be added? | A prep or packing helper improved the best found plans from 90 to 110 meals; a third cooker remained at 90, with less waste. W1 handles both prep and packing for 300 of 320 minutes. These are equal-budget classical incumbents, not certified investment optima. |
| Are you solving it classically before quantum? | Local batch programs are classical preprocessing; they are not whole kitchen schedules. Combining them creates the global conflicts and service couplings. Our sector simulator also enumerates sector energies, so we do not claim scalable quantum advantage. |
| What about Stage 1's tiny encoding? | It represents the common job permutations and tabulates their costs classically. It correctly yields 4 h / 8 h, but factorial preprocessing is not a scalable quantum scheduling method. The comparable time-indexed B encoding has 30 bits. |
| Is the live button training? | No. It reuses saved depth 3 QAOA angles, samples 4,096 shots with a fixed seed and independently checks returned states. The animation is a separately labeled retained schedule. |

## If you need a moment

Use one line, then answer the actual question:

- “Do you mean the full kitchen, or the restricted portfolio we ran?”
- “Let me separate feasibility, solution quality and runtime.”
- “Are you asking about the encoding, or the solver?”
- “We have not measured that. The closest verified result is …”
- “Our method owner can give the implementation detail.”

If completely stuck:

“A bit selects one batch program. We choose compatible batches and independently
check whether complete meals reach departure. Which part would you like us to unpack?”

## Stall-and-pivot card

Use one sentence to collect your thoughts. Then answer, show evidence, or hand
the question to the method owner. These are broad bridges, not extra claims.

**General question:**
“The important distinction here is between the quality of the representation
and the quality of the search. Our evaluation keeps those two effects separate.”

Pivot: offered-pool optimum versus full-grid reference.

**Unexpected quantum question:**
“The circuit preserves the structure of the encoded choices; physical
feasibility and useful service are evaluated separately after measurement.”

Pivot: one-hot sector, conflict penalties, independent checker.

**Performance question:**
“The relevant comparison is the checked decision under a stated compute budget.
A backend time or an energy value alone does not describe that whole process.”

Pivot: runtime table and input identity; ask which two methods they mean.

**Scaling question:**
“What matters is how the decisions interact through shared resources and
service requirements, as well as how many choices the representation retains.”

Pivot: worker/cooker conflicts, paired service, restricted portfolios.

**Why your approach?**
“We wanted the model, optimization method and operational interpretation to
agree, so every reported result can be traced back to a checked production plan.”

Pivot: show one selected bit's batch timeline.

**Genuine unknown:**
“We have not isolated that effect in this experiment. The result we can support
is the narrower comparison shown here.”

Then state that comparison or ask the appropriate method owner to take over.
Do not stack several bridges: the Q&A slot is only about two minutes.

## If the demo fails

“The fresh launch has not completed, so we will use the retained checked schedule.”

Move to the saved kitchen or video. Do not wait for a remote job, relabel an old
result as a fresh one, or spend the remaining slot debugging.

## Numbers worth memorizing

- Stage 1: A 4 h; B 8 h.
- Cell: 35 data qubits; 1,045 sector states; 59 physically feasible states.
- Fresh QAOA setup: 4,096 shots; 2,173 valid shots; 20 complete meals; 0 waste.
- Trained QAOA at 256 evaluations:10.7×/21.6× median per-shot optimum probability
  versus random-angle search on S2/S3. Both hit 10/10 on S2; random hits 6/10 on S3.
- Latest VQE: 99.54%/99.55%; 10/10 seeds per case; 1,024 final shots; exact gradients.
- VeloxQ loop: 486/998/2,022 bits; U 9→7,11→6,13→7; 71 submissions.
- Capacity: 90→110 meals with a prep or packing helper, out of 140 requested.

## Do not blur these distinctions

- Offered-pool optimum is not the full-grid optimum.
- A feasible sample is not necessarily optimal.
- Simulator result is not hardware execution.
- Ten seeds finding an optimum is not every shot being optimal.
- More bits alone does not establish classical hardness.
- R=B in these fixtures; there is no separately demonstrated stability gain.
- QAOA settings transferred to S2/S3, but angles are optimized per instance.
  E6 reused cases previously examined in E5; do not call those wholly unseen.

Full references: [live runbook](CATERING_LIVE.md), [Q&A](CATERING_QA.md),
[formal problem](CATERING_PROBLEM.md), [benchmarks](https://qfactoria.com/catering/benchmarks/).
