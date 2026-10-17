"""Offline algebra audit for a proposed catering option-QUBO, not a solver benchmark.

Enumerates every bitstring of two small, declared option pools. Requires NumPy.
No service calls, token access, quantum execution, or current factory changes.
"""

import argparse
import hashlib
import itertools
import json
from pathlib import Path

import numpy as np


def options():
    rows = []
    for menu, lots in [('A', ['A1', 'A2']), ('B', ['B1', 'B2'])]:
        for oven in ['O1', 'O2']:
            for start in [0, 3]:
                rows.append(dict(id=f'{menu}-{oven}-{start}', menu=menu,
                                 covers=lots, yield_lots=2,
                                 cooking=[oven, start, start + 2],
                                 packing=['P1', start + 2, start + 4]))
        rows.append(dict(id=f'{menu}-O2-wait', menu=menu, covers=lots,
                         yield_lots=2, cooking=['O2', 0, 2], packing=['P1', 4, 6]))
        for lot, oven, start in [(lots[0], 'O2', 0), (lots[1], 'O1', 3)]:
            rows.append(dict(id=f'{lot}-single', menu=menu, covers=[lot],
                             yield_lots=2, cooking=[oven, start, start + 2],
                             packing=['P1', start + 2, start + 3]))
    return rows


def intervals(row):
    # One synthetic mandatory terminal-cleaning slot is part of oven occupation.
    oven, start, end = row['cooking']
    return [(oven, start, end + 1), tuple(row['packing'])]


def conflict(first, second):
    return any(r == s and a < d and c < b
               for r, a, b in intervals(first) for s, c, d in intervals(second))


def audit(outage):
    lots = ['A1', 'A2', 'B1', 'B2']
    due = {'A': 5, 'B': 7}
    rows = options()
    if outage:
        rows = [r for r in rows if not any(
            resource == 'O1' and start < 3 and 0 < end
            for resource, start, end in intervals(r))]
    assert all(r['packing'][1] >= r['cooking'][2] and
               r['packing'][2] - r['cooking'][2] <= 4 for r in rows)

    # Nonnegative secondary cost: portion-lot lateness, then excess output,
    # then number of selected batches. This scalarization has strict bounds.
    count_bound = len(rows)
    excess_bound = sum(r['yield_lots'] - len(r['covers']) for r in rows)
    excess_weight = count_bound + 1
    late_weight = excess_bound * excess_weight + count_bound + 1
    secondary = [late_weight * len(r['covers']) * max(0, r['packing'][2] - due[r['menu']])
                 + excess_weight * (r['yield_lots'] - len(r['covers'])) + 1
                 for r in rows]
    secondary_bound = sum(secondary)
    missing_weight = secondary_bound + 1
    costs = secondary + [missing_weight] * len(lots)
    objective_bound = sum(costs)
    penalty = objective_bound + 1
    n = len(costs)
    linear = costs.copy()
    quadratic = {}
    offset = 0
    groups = [[i for i, row in enumerate(rows) if lot in row['covers']] + [len(rows) + j]
              for j, lot in enumerate(lots)]
    for group in groups:
        offset += penalty
        for i in group:
            linear[i] -= penalty
        for i, j in itertools.combinations(group, 2):
            quadratic[i, j] = quadratic.get((i, j), 0) + 2 * penalty
    for i, j in itertools.combinations(range(len(rows)), 2):
        if conflict(rows[i], rows[j]):
            quadratic[i, j] = quadratic.get((i, j), 0) + penalty

    masks = np.arange(1 << n, dtype=np.uint32)
    bits = ((masks[:, None] >> np.arange(n)) & 1).astype(np.int64)
    energy = offset + bits @ np.array(linear, dtype=np.int64)
    for (i, j), coefficient in quadratic.items():
        energy += coefficient * bits[:, i] * bits[:, j]

    # Independent physical rule evaluation uses resource occupancy counts rather
    # than the compiler's pair-conflict list or exact-cover group list.
    valid = np.ones(len(masks), dtype=bool)
    direct_penalty = np.zeros(len(masks), dtype=np.int64)
    for j, lot in enumerate(lots):
        coverage = bits[:, len(rows) + j].copy()
        for i, row in enumerate(rows):
            if lot in row['covers']:
                coverage += bits[:, i]
        valid &= coverage == 1
        direct_penalty += (coverage - 1) ** 2
    for resource in ['O1', 'O2', 'P1']:
        for time in range(8):
            occupation = np.zeros(len(masks), dtype=np.int64)
            for i, row in enumerate(rows):
                if any(r == resource and a <= time < b for r, a, b in intervals(row)):
                    occupation += bits[:, i]
            valid &= occupation <= 1
    objective = bits @ np.array(costs, dtype=np.int64)
    ground = energy == energy.min()
    assert valid[ground].all()
    assert int(energy.min()) == int(objective[valid].min())
    assert np.array_equal(energy[valid], objective[valid])
    # The literal energy's zero-penalty set must match the independent checker.
    assert np.array_equal(energy == objective, valid)
    chosen = int(np.flatnonzero(ground)[0])
    selected = [row for i, row in enumerate(rows) if bits[chosen, i]]
    metrics = dict(
        missing_lots=int(bits[chosen, len(rows):].sum()),
        tardiness_lot_slots=sum(len(r['covers']) * max(0, r['packing'][2] - due[r['menu']])
                                for r in selected),
        excess_lots=sum(r['yield_lots'] - len(r['covers']) for r in selected),
        batches=len(selected),
    )
    return dict(
        outage=outage, options=len(rows), binary_variables=n, couplers=len(quadratic),
        bitstrings_checked=len(masks), feasible_bitstrings=int(valid.sum()),
        ground_states=int(ground.sum()), optimum=int(energy.min()), metrics=metrics,
        penalty=penalty, objective_upper_bound=objective_bound,
        selected=selected, candidate_options=rows,
        checks=dict(all_ground_states_physically_valid=True,
                    ground_energy_equals_independent_feasible_minimum=True,
                    every_zero_penalty_state_matches_independent_checker=True),
        scope='Exact only over the declared local batch options. No arbitrary-start '
              'or full catering optimum claim; no VeloxQ/QAOA performance result.',
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Choose a fresh output directory')
    args.output.mkdir(parents=True)
    reports = [audit(False), audit(True)]
    result = dict(schema='catering-design-algebra-audit.v1',
                  source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  numpy_version=np.__version__, physical_qpu_calls=0,
                  veloxq_calls=0, reports=reports)
    (args.output / 'report.json').write_text(json.dumps(result, indent=2) + '\n')
    (args.output / 'source.py').write_text(Path(__file__).read_text())
    print(json.dumps([dict(outage=r['outage'], bits=r['binary_variables'],
                           checked=r['bitstrings_checked'], metrics=r['metrics'],
                           checks=r['checks']) for r in reports], indent=2))


if __name__ == '__main__':
    main()
