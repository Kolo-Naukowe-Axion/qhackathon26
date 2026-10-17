"""Nested recovery pools generated without reading reference answers.

The baseline pool is immutable. Additional unary rows alternate anchor proximity
and temporal coverage, round-robin across machine/worker modes. References are
used only after every pool has been saved.
"""
import argparse
from collections import defaultdict
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import time

from .window_qubo import assignments, check_plan, digest


def nested_pools(problem, baseline, caps=(24, 32, 48, 64, None)):
    """Return nested caps; None appends every raw unary assignment.

    No solver, objective value, reference plan or downstream result is an input.
    All original options survive, including options lacking global support.
    """
    operations = {op['id']: op for op in problem['operations']}
    if set(baseline) != set(operations):
        raise ValueError('Baseline must contain every operation')
    finite = [cap for cap in caps if cap is not None]
    if finite != sorted(set(finite)) or (None in caps and caps[-1] is not None):
        raise ValueError('Caps must increase, with full last')
    pools = deepcopy(baseline)
    queues = {}
    anchors = {}
    for oid, op in operations.items():
        raw = assignments(problem, op)
        legal = {digest(row) for row in raw}
        if not pools[oid] or any(len(c) != 1 or digest(c[0]) not in legal for c in pools[oid]):
            raise ValueError('Every original column must be unary legal')
        if len({digest(c[0]) for c in pools[oid]}) != len(pools[oid]):
            raise ValueError('Duplicate original column')
        if finite and len(pools[oid]) > finite[0]:
            raise ValueError('First cap must retain baseline')
        anchors[oid] = [c[0]['start'] for c in pools[oid]]
        kept = {digest(c[0]) for c in pools[oid]}
        modes = defaultdict(list)
        for row in raw:
            if digest(row) not in kept:
                modes[row['machine'], row['worker']].append(row)
        queues[oid] = modes
    result = []
    # A complete deterministic ordering is built once; caps take its prefixes.
    ordering = {}
    for oid, modes in queues.items():
        ordered = []
        retained = [c[0] for c in pools[oid]]
        round_number = 0
        while any(modes.values()):
            for mode in sorted(modes):
                options = modes[mode]
                if not options:
                    continue
                current = [r['start'] for r in retained if (r['machine'], r['worker']) == mode]
                if round_number % 2 == 0 or not current:
                    key = lambda r: (min(abs(r['start'] - s) for s in anchors[oid]), r['start'])
                else:
                    key = lambda r: (-min(abs(r['start'] - s) for s in current), r['start'])
                row = min(options, key=key)
                options.remove(row)
                retained.append(row)
                ordered.append([row])
            round_number += 1
        ordering[oid] = ordered
    for cap in caps:
        columns = {oid: deepcopy(baseline[oid] + ordering[oid][:None if cap is None else cap - len(baseline[oid])])
                   for oid in operations}
        result.append((cap, columns))
    return result


def save(path, data):
    path.write_text(json.dumps(data, indent=2) + '\n')


def run(source, output, seconds=5):
    # All literal source/input bytes are copied before generator or reference work.
    output.mkdir(parents=True, exist_ok=False)
    root = Path(__file__).resolve().parents[1]
    sources = ['capacity_frontier.py', 'window_qubo.py', 'column_reference.py',
               'column_qubo.py', 'trajectory_qubo.py', 'operation_qubo.py']
    hashes = {}
    for name in sources:
        path = root / 'stage2' / name
        target = output / 'sources' / 'stage2' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(path.read_bytes())
        hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    caps = [24, 32, 48, 64, None]
    cases = ['heat-outage-32', 'heat-lease-32']
    protocol = dict(cases=cases, caps=caps, seconds_per_solve=seconds, workers=1,
                    generation='Immutable baseline; alternating anchor-near and temporal-gap rows in round-robin machine/worker mode order',
                    cp_teacher_used=False, references_read_after_all_pools_saved=True,
                    full_means='All raw unary rows; no support pruning, no radius restriction',
                    source_hashes=hashes, remote_calls=0)
    save(output / 'protocol.json', protocol)
    began = time.perf_counter()
    prepared = []
    for case in cases:
        directory = output / case
        directory.mkdir()
        p = json.loads((source / case / 'problem.json').read_text())
        baseline = json.loads((source / case / 'columns.json').read_text())
        parents = json.loads((source / case / 'parents.json').read_text())['parents']
        witness = min(parents, key=lambda plan: check_plan(p, plan)['objective'])
        save(directory / 'problem.json', p)
        save(directory / 'baseline.json', baseline)
        generation_started = time.perf_counter()
        pools = nested_pools(p, baseline, caps)
        save(directory / 'generation.json', dict(wall_seconds=time.perf_counter() - generation_started,
             problem_sha256=digest(p), baseline_sha256=digest(baseline), witness=check_plan(p, witness)))
        for cap, columns in pools:
            target = directory / ('full' if cap is None else f'cap-{cap}')
            target.mkdir()
            save(target / 'columns.json', columns)
            prepared.append((case, cap, p, columns, witness, target))
    # Candidate generation is complete before references are imported or read.
    from .column_reference import solve_column_cp
    from .operation_qubo import compile_operations
    rows = []
    for case, cap, p, columns, witness, target in prepared:
        reference = solve_column_cp(p, columns, seconds=seconds, workers=1, initial_plan=witness)
        t = time.perf_counter()
        q = compile_operations(p, columns)
        metadata = q.metadata()
        metadata['build_seconds'] = time.perf_counter() - t
        if 'plan' in reference:
            assert check_plan(p, reference['plan'])['valid']
            assert q.energy(q.encode(reference['plan'])) == reference['objective']
        row = dict(case=case, cap=cap, pool_sha256=digest(columns), model=metadata, reference=reference)
        save(target / 'report.json', row)
        rows.append(row)
        print(json.dumps(dict(case=case, cap=cap, bits=metadata['variables'],
                             status=reference['status'], objective=reference.get('objective'), bound=reference['bound'])), flush=True)
    # Saved complete-model references are audit comparators, never generator input.
    comparators = {case: json.loads((source / case / 'report.json').read_text())['raw_reference'] for case in cases}
    report = dict(protocol=protocol, rows=rows, complete_reference=comparators,
                  wall_seconds=time.perf_counter() - began,
                  source_stable=all(hashlib.sha256((root / 'stage2' / n).read_bytes()).hexdigest() == h for n, h in hashes.items()))
    save(output / 'report.json', report)
    save(output / 'manifest.json', {str(p.relative_to(output)): hashlib.sha256(p.read_bytes()).hexdigest()
                                   for p in output.rglob('*') if p.is_file()})
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path('output/manufacturing-recovery-v2'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--seconds', type=float, default=5)
    args = parser.parse_args()
    run(args.source, args.output, args.seconds)
