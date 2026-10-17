# An idealized quality and material probability ceiling

Under the explicitly idealized assumption that every canonical unit/attempt has an independent uniform QA draw, a necessary-event relaxation gives an all-orders-success probability upper bound of **97.5180636447%** for the 32-order, H14400 numerical model, averaged over its eight declared exogenous leaves. This is an analytic model statement, not a theorem that SHA-derived draws are independent, an achievable success rate, or an additional experiment.

For a recipe, let `a` be a conservative policy-independent lower bound on initial manufacturing defect risk and `b` the lower bound on residual repair risk. The event that its first potential QA draw is below `a` and its repair draw is below `b` forces that canonical unit to scrap under every policy. Its idealized probability is `q = a*b`. Wear, deliberate mode choices and adaptive decisions cannot remove this event because the thresholds are lower bounds across legal choices. These events use fixed identities, including `original~r1` for replacements; they do not permit policy-selected random-stream names.

For `D` demanded originals and `B` available blanks, success requires no more than `B-D` forced original scraps, and each forced original scrap requires a replacement that is not itself forced to scrap. Therefore a component's necessary-event probability is

```text
sum k=0..min(D,B-D) binom(D,k) [q(1-q)]^k (1-q)^(D-k),
or zero when B<D.
```

The two allowed states of each original are: not forced to scrap, probability `1-q` and one blank; or forced to scrap with an unforced replacement, probability `q(1-q)` and two blanks. A doubly forced lineage cannot succeed. Multiplying the component expressions and `(1-q_pump)^D` for final pumps gives a necessary-event probability conditional on an exogenous leaf. The leaf probabilities then give the stated ceiling. The independence assumption applies jointly across these fixed potential QA keys and conditionally independently of the exogenous leaf. No final pump replacement is legal.

The held bound module supplies conservative initial floors approximately 0.02 for housing/rotor, 0.015 for flange and 0.01 for pump, with repair floor approximately 0.02. These conservative floors intentionally discard some mandatory accumulated risk. The computation uses exact rational polynomial evaluation and leaf averaging, then rounds the displayed binary64 upper bound upward. It checks the identities `B<D => 0`, `B=D => (1-q)^D`, `B>=2D => (1-q²)^D`, and `q=0 => 1`.

Evidence is `output/stage2-search/final-independent-audit/analytic_quality_ceiling.py` and `ideal-quality-ceiling-report.json`. Analysis source SHA-256: `e94b0f90288e43224381f7f9733878afb0a9dc281cd171c01d8aa95ae6d0174c`; held numerical bound source SHA-256: `c16698d81a2803df30c4b8d331904a14f45a375040ac9a3ca750b151e2e80236`. This analysis performs no factory simulations and inspects no realized endogenous QA draws. All frozen policy and physical sources remain unchanged.

The relaxation ignores timing, resource constraints and failures outside its conservative forced-event rectangles. Its difference from an observed policy success rate **does not establish achievable headroom or attribute losses to scheduling**. Such claims would require tighter bounds or additional checked schedules on the same instances. It is also distinct from the deterministic realized-tape certificates: those use actual keyed draws and can prove a nonzero primary optimum on an individual tape.
