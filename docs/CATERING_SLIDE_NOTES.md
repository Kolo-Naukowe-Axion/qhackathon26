# Live speaker notes — by visible slide

These notes match the current visual slide, including the separate opening, Stage 1, code and proof views. They do not change on a clock within the same view. Keep this file on a phone or second device when sharing the demo; P hides the studio notes as well as its controls. Use the rehearsal timer to stay under three minutes.

## Opening · Axion Kitchen

> Axion Kitchen. Quantum optimization for catering production.

## Stage 1 · factory baselines

> Factory baselines: four and eight hours, both checked optimal.

## The catering production problem

> Same formulation across five cases: a complete small cell, then normal service, urgent order, outage, and both. Cookers are machines, cleaning is setup, and departures are due dates. We enforce freshness and resource constraints throughout. Complete meals come first, then waste, batches and changes.

## Two orders sharing a side batch

> Two customers share a twenty-portion side batch. One Main B option clashes with it on C2. The checked QAOA plan instead chooses Main B on C1, so both orders leave complete.

## What happens without the side batch

> Remove the side: zero complete meals and twenty wasted portions. This is a manual intervention.

## Encoding · one bit selects a batch program

> A bit selects one batch and its schedule. Each anchor block chooses one program or idle. Conflicts forbid clashes. This cell uses thirty-five bits.

## Encoding · compiler excerpt

> The compiler expands coverage products into pair terms and sets the hard penalty above the full objective range.

## Objective · complete meals and waste

> Main and side coverage multiply into quadratic service and waste terms. Priority weights put missed meals first, then waste, batches and changes.

## Correctness · the penalty guarantee

> The objective varies by at most S over all bitstrings. Set P to S plus one: every invalid state costs more than every feasible state. This ground-state guarantee does not guarantee solver convergence.

## Run QAOA

> Return to the original choices. We run the saved depth-three circuit, draw four thousand ninety-six fresh samples, and independently check the outcomes.

## QAOA results

> On both held-out disruption cases, QAOA finds the offered-pool optimum in all ten seeds. Random-angle search also hits all ten on S2. With two hundred fifty-six evaluations, optimum probability per shot is about eleven and twenty-two times random-angle search. The full kitchen still has better schedules than these restricted portfolios.

## VQE: concentrate the solution

> Our latest VQE uses CVaR then Gibbs loss: ninety-nine point five percent offered-optimum probability in both disruption cases. Exact gradients; this staged gain did not survive shot-noise emulation.

## VeloxQ inside the replanning loop

> VeloxQ starts from its own plan and repeatedly changes two blocks. Missed meal lots fall from nine to seven, eleven to six, and thirteen to seven. All improvements pass the checker. Exact neighborhood controls do as well or better; longer classical runs still win.

## What makes the choices difficult?

> Small cells test correctness. Larger inputs generate eighteen thousand programs with shared-resource conflicts. More variables alone do not establish hardness; benchmarks show quality and runtime.

## Checked results and benchmarks

> Twenty meals, zero waste. We fixed cleaning, paired main and side, and proved idle elimination.

