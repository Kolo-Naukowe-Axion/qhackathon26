# Routing-score coefficient training experiment

All 640 episodes used the byte-frozen v2-threshold physical core, 96-hour minute grid, independent checker, selector=priority, and environment tapes 0–7. All 640 passed. Existing static teacher weights were held constant except the tool-distance and sequence-setup terms of the machine-choice score. These terms alter routing heuristics, not physical travel or setup durations.

| Initial orders | Baseline missing → tuned | Baseline tardiness → tuned, minutes | Tuned tool-distance / setup score |
| --- | ---: | ---: | --- |
| 8 | 0.000 → 0.000 | 1059.5 → 306.9 | 1 / 10 |
| 12 | 1.750 → 1.375 | 8907.4 → 8012.9 | 0 / 10 |
| 16 | 5.625 → 4.875 | 15928.8 → 14453.6 | 1 / 10 |
| 24 | 13.625 → 13.500 | 33609.8 → 32435.9 | 8 / 10 |

These are selected-on-training comparisons, not held-out improvements. Policy coefficients differ by workload; no universal routing weight is supported. The original teacher was itself trained on tapes 0–31. The new two-knob choices above used only 0–7. Final seed 10000+ was untouched.

Local cost: 98.53 seconds wall, six workers. Raw protocol, all measurements and full summaries are retained. The source manifest identifies the unchanged physical model; do not compare this wall time directly against an Axion job.

Machine setup penalties in this probe included 1/3/10/30. The subsequent routing-v3 search domain uses the root-requested 0/3/10/30 and tool-distance 0/1/2/4/8.
