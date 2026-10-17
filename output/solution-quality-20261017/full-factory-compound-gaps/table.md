# Realized primary optimality audit

Posthoc certificates for unchanged frozen outcomes; missing-order objective only. These are empirical weighted values, not population guarantees.

| Initial orders | Calendar hours | Mean missing | Mean excess above realized optimum, certified interval | Primary optimum certified |
|---:|---:|---:|---:|---:|
| 10 | 96 | 0.01031 | [0.00000, 0.00406] | 99.59% |
| 11 | 96 | 0.03172 | [0.00000, 0.02547] | 98.55% |
| 12 | 96 | 0.07500 | [0.06469, 0.06875] | 95.61% |
| 13 | 96 | 0.14922 | [0.09375, 0.14297] | 88.84% |
| 14 | 96 | 0.27813 | [0.12344, 0.27187] | 80.88% |
| 16 | 96 | 2.69062 | [1.14031, 2.68219] | 8.80% |
| 24 | 96 | 10.02094 | [0.57063, 10.01250] | 0.00% |
| 32 | 240 | 0.10234 | [0.00000, 0.04719] | 95.28% |

Every interval concerns realized-tape missing-order optimum only. Deadline debt/cost optimality is unknown.
The upper bound is the best valid retained execution on the identical tape, including different actors/methods; hindsight selection is an offline comparator, not a deployable controller.
Mean excess interval averages per-realization gaps with original probability weights; it is not regret against an optimal nonanticipating stochastic policy.
Attainment rates describe this fixed final sample; no new confidence interval or generalization guarantee is inferred.
23552 executions rely on original anchored physical/identity checks; this audit rebuilds numerical instances/certificates, not all original traces.
