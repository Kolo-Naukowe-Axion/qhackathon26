"""Exact blockwise coefficient counts without a global quadratic dictionary.

This specialized audit requires continuous worker calendars. Each operation-pair
Boolean block reproduces the declared scalar conflict semantics, including
overlapping reason multiplicities. Support propagation preserves every feasible
schedule. No optimizer, incumbent, heuristic or reference answer is consulted.
"""
from collections import deque
import argparse
import hashlib
import json
from pathlib import Path
import time

import numpy as np

from .window_qubo import assignments, digest, validate


def conflict_block(problem, first, second, rows_a, rows_b):
    if any(worker['available'] != [[0, problem['horizon']]] for worker in problem['workers'].values()):
        raise ValueError('Block audit requires continuous worker calendars')
    machines = list(problem['machines'])
    workers = list(problem['workers'])
    halls = sorted({machine['hall'] for machine in problem['machines'].values()})

    def values(rows, key, categories=None):
        return np.array([categories.index(row[key]) if categories is not None else row[key] for row in rows])

    ma, mb = values(rows_a, 'machine', machines)[:, None], values(rows_b, 'machine', machines)[None, :]
    wa, wb = values(rows_a, 'worker', workers)[:, None], values(rows_b, 'worker', workers)[None, :]
    ha, hb = values(rows_a, 'hall', halls)[:, None], values(rows_b, 'hall', halls)[None, :]
    sa, sb = values(rows_a, 'start')[:, None], values(rows_b, 'start')[None, :]
    ea, eb = values(rows_a, 'end')[:, None], values(rows_b, 'end')[None, :]
    aa, ab = values(rows_a, 'attended_end')[:, None], values(rows_b, 'attended_end')[None, :]
    first_before = (sa < sb) | ((sa == sb) & (first['id'] < second['id']))
    labels = ((ma == mb) & (sa < eb) & (sb < ea)).astype(np.uint8)
    if problem.get('machine_setups'):
        setup = problem['machine_setups']
        gap_ab = setup[first['family']][second['family']]
        gap_ba = setup[second['family']][first['family']]
        labels += ((ma == mb) & np.where(first_before, gap_ab > 0, gap_ba > 0) &
                   np.where(first_before, ea + gap_ab > sb, eb + gap_ba > sa))
    occupation = (wa == wb) & (sa < ab) & (sb < aa)
    labels += occupation
    walk = problem['worker_travel']
    labels += ((wa == wb) & (ha != hb) & ~occupation &
               np.where(first_before, aa + walk > sb, ab + walk > sa))
    if first['id'] in second['predecessors']:
        lags = np.array([[problem['transport_lags'][a][b] for b in machines] for a in machines])
        labels += ea + lags[ma, mb] > sb
    if second['id'] in first['predecessors']:
        lags = np.array([[problem['transport_lags'][b][a] for b in machines] for a in machines])
        labels += eb + lags[ma, mb] > sa
    return labels


def prune(problem, domains):
    """Blockwise construction of the same binary arc-consistency certificate."""
    names = list(domains)
    ops = {op['id']: op for op in problem['operations']}
    support = {}
    pairs, max_block = 0, 0
    for ai, a in enumerate(names):
        for b in names[ai + 1:]:
            compatible = conflict_block(problem, ops[a], ops[b], domains[a], domains[b]) == 0
            pairs += compatible.size
            max_block = max(max_block, compatible.size)
            support[a, b] = [int.from_bytes(row.tobytes(), 'little') for row in np.packbits(compatible, axis=1, bitorder='little')]
            support[b, a] = [int.from_bytes(row.tobytes(), 'little') for row in np.packbits(compatible.T, axis=1, bitorder='little')]
    live = {name: (1 << len(domains[name])) - 1 for name in names}
    queue = deque((a, b) for a in names for b in names if a != b)
    removed = 0
    while queue:
        a, b = queue.popleft()
        before = live[a]
        for index, mask in enumerate(support[a, b]):
            if live[a] & (1 << index) and not mask & live[b]:
                live[a] &= ~(1 << index)
                removed += 1
        if not live[a]:
            raise ValueError('Exact support propagation proved an empty mandatory domain')
        if before != live[a]:
            queue.extend((other, a) for other in names if other != a and other != b)
    result = {name: [row for index, row in enumerate(domains[name]) if live[name] & (1 << index)] for name in names}
    return result, dict(before=sum(map(len, domains.values())), after=sum(map(len, result.values())),
        removed=removed, pair_checks=pairs, max_pair_block_cells=max_block,
        method='Exact binary arc consistency using independently tested vectorized conflict blocks')


def count_model(problem, domains):
    validate(problem)
    start = time.perf_counter()
    operations = {op['id']: op for op in problem['operations']}
    names = list(domains)
    successor_ids = {prior for op in operations.values() for prior in op['predecessors']}
    ends = sorted({row['end'] for rows in domains.values() for row in rows})
    costs, bound = [], 0
    for name, rows in domains.items():
        values = [(problem['horizon'] + 1) * operations[name].get('weight', 1) *
                  max(0, row['end'] - operations[name]['due']) if name not in successor_ids else 0 for row in rows]
        costs.extend(values)
        bound += max(values)
    costs.extend(ends)
    bound += max(ends)
    penalty = bound + 1
    histogram = {}
    pair_checks = 0
    max_block = 0
    for ai, a in enumerate(names):
        for b in names[ai + 1:]:
            labels = conflict_block(problem, operations[a], operations[b], domains[a], domains[b])
            pair_checks += labels.size
            max_block = max(max_block, labels.size)
            for multiplicity, count in enumerate(np.bincount(labels.ravel())):
                if multiplicity:
                    histogram[multiplicity] = histogram.get(multiplicity, 0) + int(count)
    onehot = sum(len(rows) * (len(rows) - 1) // 2 for rows in domains.values()) + len(ends) * (len(ends) - 1) // 2
    makespan_links = sum(int(np.searchsorted(ends, row['end'], side='left')) for rows in domains.values() for row in rows)
    edge_count = onehot + makespan_links + sum(histogram.values())
    linears = [value - penalty for value in costs]
    edge_values = ([2 * penalty] if onehot else []) + ([penalty] if makespan_links else []) + [m * penalty for m, count in histogram.items() if count]
    absolute = [abs(value) for value in [*linears, *edge_values] if value]
    return dict(variables=len(costs), assignment_variables=sum(map(len, domains.values())),
        makespan_variables=len(ends), couplers=edge_count, penalty=penalty,
        coefficient_min=min([*linears, *edge_values]), coefficient_max=max([*linears, *edge_values]),
        min_abs_nonzero_coefficient=min(absolute), max_abs_coefficient=max(absolute),
        coefficient_dynamic_range=max(absolute) / min(absolute),
        onehot_couplers=onehot, makespan_links=makespan_links,
        incompatibility_multiplicity_histogram=histogram, pair_checks=pair_checks,
        max_pair_block_cells=max_block, global_quadratic_dictionary_allocated=False,
        build_seconds=time.perf_counter() - start)


def run(source, output):
    source, output = Path(source), Path(output)
    output.mkdir(parents=True, exist_ok=False)
    root = Path(__file__).resolve().parents[1]
    names = ['realism_streaming.py', 'window_qubo.py']
    hashes = {}
    for name in names:
        path = root / 'stage2' / name
        target = output / 'sources' / 'stage2' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(path.read_bytes())
        hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    problem = json.loads((source / 'problem.json').read_text())
    (output / 'problem.json').write_text(json.dumps(problem, indent=2) + '\n')
    protocol = dict(schema='qfactoria-continuous-calendar-streaming-counts.v1', source=str(source),
        source_hashes=hashes, problem_sha256=digest(problem),
        fixed_horizon=problem['horizon'], fixed_grid=problem['grid'], numpy_version=np.__version__,
        expanded_count_pair_budget=220_000_000, max_block_cells=4_000_000,
        selection='Follow-up to retained dense-build guard, predeclared vectorized count-only audit; no solver performance experiment',
        scope='Exact original full-optimization coefficient counts for continuous-worker-calendar ablation; no global QUBO matrix allocated',
        veloxq_calls=0, physical_qpu_calls=0)
    (output / 'protocol.json').write_text(json.dumps(protocol, indent=2) + '\n')
    started = time.perf_counter()
    domains = {op['id']: assignments(problem, op) for op in problem['operations']}
    counts = [len(rows) for rows in domains.values()]
    checks = sum(counts[i] * counts[j] for i in range(len(counts)) for j in range(i + 1, len(counts)))
    if 2 * checks > protocol['expanded_count_pair_budget'] or max(counts) ** 2 > protocol['max_block_cells']:
        raise ValueError('Predeclared block-count guard exceeded')
    unary = count_model(problem, domains)
    start = time.perf_counter()
    reduced, certificate = prune(problem, domains)
    prune_seconds = time.perf_counter() - start
    support = count_model(problem, reduced)
    support['build_seconds'] += prune_seconds
    support['reduction'] = certificate
    stable = all(hashlib.sha256((root / 'stage2' / name).read_bytes()).hexdigest() == expected for name, expected in hashes.items())
    if not stable:
        raise AssertionError('Streaming audit source changed')
    report = dict(protocol=protocol, unary_complete=unary, support_complete=support,
        source_stable=stable, wall_seconds=time.perf_counter() - started,
        reference_source=str(source / 'report.json'), reference_report_sha256=hashlib.sha256((source / 'report.json').read_bytes()).hexdigest(),
        veloxq_calls=0, physical_qpu_calls=0)
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    (output / 'manifest.json').write_text(json.dumps({str(path.relative_to(output)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in output.rglob('*') if path.is_file()}, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.source, args.output)
