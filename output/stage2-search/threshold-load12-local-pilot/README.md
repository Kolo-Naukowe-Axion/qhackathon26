# Local threshold pilot at load 12

Development experiment, search seed 2027, frozen threshold source f452bd46b160afcf56ed2870f8c1d9e45c47916ad3f02e7191868a5fe5f1e71c and recorded physical hashes. Search used TRAIN 0–31 and selected on validation 100–115. No final 10000+ holdout was evaluated. All 308 simulated episodes passed independent physical checking.

Validation-selected delayed lease policy reduced mean missing orders 2.5 → 1.6875 against its static teacher on the same 16 validation tapes. Mean tardiness 10203.94 → 10051 minutes; empirical CVaR90 19786.13 → 14268.63; total cost 723.27 → 736.04; complete episodes remained 6/16. Selection on these tapes makes this development evidence, not an unbiased final test.

The selected policy mainly delays the second calibration-kit request to 24 hours (delivery at 32 hours). This exposes a greedy-routing/resource interaction; it does not show that optional extra capacity worsens the globally optimal physical schedule.

Actual local cost: 63.18 seconds wall, 345.01 summed simulation CPU-seconds, 308 actual simulations. The final in-flight generation overran the requested 60 seconds.

Reporting limitation of this frozen first implementation: action_changes counts changes of action/reason labels, including a reason change whose weights stayed equal. Do not interpret it as the number of real control changes. The current learner source separates weight changes and reason changes; the frozen measurements are preserved unchanged.
