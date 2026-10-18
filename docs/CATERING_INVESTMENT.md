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
| Second packing line | not modelled | — | — |

U counts missed complete meal lots of ten meals (14 lots in total); lower is
better. Each CP run had 240 s and two workers; seeds 2026 and 2027 return the
same tuples. No run proved optimality, so these are best found plans, not
certified optima. The core profile requires exactly one packing line, so that
option is reported as unsupported rather than approximated.

**Decision.** More equipment does not serve more meals here: a third cooker or
a repaired C2 only removes one discarded portion. The bottleneck is people:
W1 both prepares and packs. A flexible extra worker serves two more lots, i.e.
20 more meals per lunch service. It pays off when 20 meals' margin exceeds the
cost of one extra shift; we do not invent prices.

**Price of realism.** The same decision shows the qubit cost of flexibility:
the flexible worker multiplies the complete program register by 8.3 (18,182 to
150,080), while a cooker adds 9,236 programs. The quantum methods therefore
work on cut portfolios of this register (31–35 qubits for QAOA/VQE, 486–2,022
bits for VeloxQ), and these what-if answers come from the classical reference.

Reproduce: `.venv/bin/python -m catering.investment --output NEW_DIR --seconds 240 --workers 2 --seed 2026`.
