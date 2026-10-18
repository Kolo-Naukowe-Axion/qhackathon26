# What should the kitchen invest in?

The challenge asks whether the model can justify buying a machine. We changed
one resource of the 12-customer lunch at a time and reran the raw-input CP
reference with the same physical checker. The case is S3: cooker C2 is out
from 20 to 60 minutes and an urgent order arrives. Code: `catering/investment.py`;
results: [`output/catering-investment-v1/`](../output/catering-investment-v1/).
No quantum training and no service calls; this is a classical decision study
on the same model.

| Option | Missed meal lots U | Waste W | Program register (QUBO bits before any cut) |
|---|---:|---:|---:|
| Current kitchen | 5 | 1 | 18,182 |
| Repair C2 (no outage) | 5 | 0 | 18,416 |
| Third cooker C3 | 5 | 0 | 27,418 |
| Second prep station P2 | 5 | 1 | 36,364 |
| Extra worker who can only cook | 5 | 1 | 36,364 |
| **Extra flexible worker: prepare, cook, pack** | **3** | 1 | 150,080 |
| Extra worker: prepare and cook | 3 | 1 | 75,040 |
| Extra worker: prepare and pack | 3 | 1 | 75,040 |
| Extra worker: cook and pack | 3 | 1 | 72,728 |
| **Extra worker: prepare only** | **3** | 1 | 37,520 |
| **Extra worker: pack only** | **3** | 1 | 36,364 |
| Second packing line | not modelled | — | — |

U counts missed complete meal lots of ten meals (14 lots in total); lower is
better. Each CP run had 240 s and two workers; seeds 2026 and 2027 return the
same tuples. No run proved optimality, so these are best found plans, not
certified optima. The core profile requires exactly one packing line, so that
option is reported as unsupported rather than approximated.

**Decision supported by these runs.** The best found third-cooker and repaired-C2
plans serve the same number of meals as the current-kitchen plan, while wasting
one fewer component lot (ten portions). W1 both prepares and packs; adding a
worker qualified for either task produces plans serving two more lots, or 20
more meals per lunch service. A cook-only worker gives no observed service gain.
A single-task packing or prep helper attains the same U=3 as the fully flexible
worker in these runs. This identifies a sufficient skill set, not the cheapest
hire: wages were not supplied. The observed 20-meal gain breaks even when its
contribution margin covers the extra shift cost. Because no run proved
optimality, the experiment does not certify that additional equipment can never
help or that 20 meals is the maximum possible gain.

**Price of realism.** The same decision shows the qubit cost of flexibility:
the flexible worker multiplies the complete program register by 8.3 (18,182 to
150,080), a single-task helper by 2.0 (36,364), while a cooker adds 9,236
programs. A single-task helper requires a smaller program register than a fully
flexible worker. The quantum methods therefore
work on cut portfolios of this register (31–35 qubits for QAOA/VQE, 486–2,022
bits for VeloxQ), and these what-if answers come from the classical reference.

Worker-skill variants are in `skills-seed-*`; the first seven rows in `seed-*`.
Reproduce: `.venv/bin/python -m catering.investment --output NEW_DIR --seconds 240 --workers 2 --seed 2026`
(add `--only NAME,...` to run selected variants).
