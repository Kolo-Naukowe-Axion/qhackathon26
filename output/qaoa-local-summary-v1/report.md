# Local QAOA training — 17 October 2026

All results use this Mac, classical statevector simulation and the same restricted 32-operation models.

| Case | Historical p2 seed7 | CVaR alpha.25 | CVaR alpha.5 | CVaR alpha.75 | Expectation | Final depth |
|---|---:|---:|---:|---:|---:|---:|
| heat-outage-32 | 0.6257% | 24.8571% | 20.7908% | 19.4865% | 18.3032% | 12 |
| heat-lease-32 | 1.3603% | 26.0592% | 27.5076% | 26.8473% | 25.7584% | 4 |

32 depth/multistart fits and 12 tail-lifting fits. Retained fit CPU: at least 1797.6 seconds.

The CVaR and expectation variants are selected by their respective training losses. The final export uses the expectation selection, even if another variant has a higher measured optimum probability.

See report.json for fresh-pool transfer probabilities and all measured returns. The classical constructor and exact/SA controls remain essential; no quantum advantage is established.
