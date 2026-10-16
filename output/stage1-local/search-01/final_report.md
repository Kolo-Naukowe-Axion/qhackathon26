# First offline screening

Twelve configurations tested with seeds 0, 1, 2. Three-layer QAOA with independent X mixer angles reached 100% measured validity; shared p5 reached 99.72%. Classical geometric annealing at 8000 sweeps reached 98.37%, prompting the separate six-trial cooling-schedule follow-up. All actual selected schedules were optimal. Both remote backends stayed unused.

Validation subsequently completed on seeds 100–109: selected quantum 40,960/40,960 valid shots; selected classical 5,110/5,120 valid samples. All 20 validation runs returned exact optima. See docs/STAGE1_REFINEMENT.md for the selected exports and limits.
