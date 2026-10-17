"""Cold local controls for retained deadline and original manufacturing QUBOs.

No reference schedules, witness files, SDK or remote services are read. The two
annealing methods use explicitly different work budgets; timings are empirical.
"""
import argparse
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import random
import time

from .deadline_qubo import DeadlineQUBO
from .window_qubo import WindowQUBO, check_plan, digest


def fields_and_neighbors(model, bits):
    neighbors = [dict() for _ in model.linear]
    fields = list(model.linear)
    for (i, j), weight in model.quadratic.items():
        neighbors[i][j] = weight
        neighbors[j][i] = weight
        fields[i] += weight * bits[j]
        fields[j] += weight * bits[i]
    return fields, neighbors


def swap_delta(fields, neighbors, old, new):
    return fields[new] - fields[old] - neighbors[old].get(new, 0)


def apply_swap(bits, fields, neighbors, old, new):
    if old == new or bits[old] != 1 or bits[new] != 0:
        raise ValueError('A swap must turn one selected bit off and one unselected bit on')
    for index, weight in neighbors[old].items():
        fields[index] -= weight
    for index, weight in neighbors[new].items():
        fields[index] += weight
    bits[old], bits[new] = 0, 1


def onehot_anneal(model, seed, reads=16, proposals=4096):
    """Metropolis swaps within groups, retaining each read's best encountered state."""
    if reads < 1 or proposals < 1:
        raise ValueError('Positive reads and proposals required')
    rng = random.Random(seed)
    groups = [list(group) for group in model.groups.values()]
    movable = [i for i, group in enumerate(groups) if len(group) > 1]
    samples = []
    for _ in range(reads):
        selected = [rng.choice(group) for group in groups]
        bits = [0] * len(model.linear)
        for index in selected:
            bits[index] = 1
        fields, neighbors = fields_and_neighbors(model, bits)
        energy = model.energy(bits)
        initial_energy = energy
        best_energy, best_bits = energy, bits[:]
        accepted = 0
        for step in range(proposals if movable else 0):
            group_index = rng.choice(movable)
            group = groups[group_index]
            old = selected[group_index]
            # Uniform over all alternatives, so the proposal is symmetric.
            choice = rng.randrange(len(group) - 1)
            position = group.index(old)
            new = group[choice + (choice >= position)]
            change = swap_delta(fields, neighbors, old, new)
            temperature = model.penalty * 4 * (0.005 ** (step / max(1, proposals - 1)))
            if change <= 0 or rng.random() < math.exp(-change / temperature):
                apply_swap(bits, fields, neighbors, old, new)
                selected[group_index] = new
                energy += change
                accepted += 1
                if energy < best_energy:
                    best_energy, best_bits = energy, bits[:]
        if energy != model.energy(bits) or best_energy != model.energy(best_bits):
            raise AssertionError('Incremental swap energy disagrees with literal QUBO')
        samples.append(dict(bits=best_bits, energy=best_energy, count=1,
                            initial_energy=initial_energy, final_energy=energy,
                            accepted_swaps=accepted, proposals=proposals if movable else 0))
    return samples


def load_model(directory, kind):
    """Read only problem/qubo files; deliberately avoid witness-aware loaders."""
    directory = Path(directory)
    problem = json.loads((directory / 'problem.json').read_text())
    raw = json.loads((directory / 'qubo.json').read_text())
    meta = raw['metadata']
    quadratic = {(i, j): value for i, j, value in raw['quadratic']}
    if kind == 'deadline':
        model = DeadlineQUBO(problem, meta['query'], raw['variables'], raw['groups'],
                             raw['linear'], quadratic, raw['offset'], meta['reduction'],
                             meta['incompatible_pairs'])
    elif kind == 'original':
        model = WindowQUBO(problem, raw['variables'], raw['groups'], raw['linear'],
                           quadratic, raw['offset'], meta['penalty'],
                           meta['feasible_objective_upper_bound'], {})
    else:
        raise ValueError('Unknown model kind')
    return model


def checked_samples(model, samples, cap):
    records = []
    for sample in samples:
        if sample['energy'] != model.energy(sample['bits']):
            raise AssertionError('Returned sample energy disagrees with model')
        decoded = model.decode(sample['bits'])
        # Derive every selected physical row, even if the completion register or
        # its one-hot group is invalid. Do not repair missing/duplicate operations.
        plan = [row for row, bit in zip(model.variables, sample['bits'])
                if bit and row['operation'] != '@makespan']
        raw_check = check_plan(model.problem, plan)
        target = (raw_check['valid'] and raw_check['weighted_terminal_tardiness'] == 0
                  and raw_check['makespan'] <= cap)
        records.append(dict(sample, decoded=decoded, encoded_valid=decoded['valid'],
                            raw_valid=raw_check['valid'], raw_check=raw_check,
                            target_satisfied=bool(target)))
    return records


def audit_retained(source, output):
    """Reclassify frozen returned bitstrings; never call either sampler."""
    source, output = Path(source), Path(output)
    manifest = json.loads((source / 'manifest.json').read_text())
    for name, expected in manifest.items():
        if hashlib.sha256((source / name).read_bytes()).hexdigest() != expected:
            raise AssertionError('Frozen retained-study manifest changed')
    prior = json.loads((source / 'report.json').read_text())
    for name, expected in prior['protocol']['input_sha256'].items():
        if hashlib.sha256(Path(name).read_bytes()).hexdigest() != expected:
            raise AssertionError('Frozen model input changed')
    output.mkdir(parents=True, exist_ok=False)
    root = Path(__file__).resolve().parents[1]
    hashes = {}
    for name in ['stage2/deadline_anneal.py', 'stage2/deadline_qubo.py', 'stage2/window_qubo.py']:
        path = root / name
        target = output / 'sources' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(path.read_bytes())
        hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    protocol = dict(schema='qfactoria-anneal-reporting-audit.v2',
                    retained_source=str(source), retained_manifest_sha256=hashlib.sha256(
                        (source / 'manifest.json').read_bytes()).hexdigest(),
                    source_hashes=hashes, resampling=False, solver_calls=0,
                    correction='Independently check all selected physical rows, ignoring only makespan-register bits; report encoded and raw validity separately',
                    veloxq_calls=0, physical_qpu_calls=0)
    (output / 'protocol.json').write_text(json.dumps(protocol, indent=2) + '\n')
    models, rows = {}, []
    began = time.perf_counter()
    for old in prior['rows']:
        case, kind = old['case'], old['kind']
        if (case, kind) not in models:
            relative = f'output/deadline-decision-review-v1/{case}-cap-900' if kind == 'deadline' else f'output/manufacturing-full-recovery-v1/{case}'
            models[case, kind] = load_model(relative, kind)
        model = models[case, kind]
        filename = f"{case}-{kind}-{old['method']}-{old['seed']}.json"
        previous = json.loads((source / filename).read_text())
        records = checked_samples(model, previous['records'], 900)
        row = dict(case=case, kind=kind, method=old['method'], seed=old['seed'],
            returned_samples=sum(r['count'] for r in records),
            encoded_feasible_samples=sum(r['count'] for r in records if r['encoded_valid']),
            raw_feasible_samples=sum(r['count'] for r in records if r['raw_valid']),
            target_satisfied_samples=sum(r['count'] for r in records if r['target_satisfied']),
            old_target_satisfied_samples=old['target_satisfied_samples'],
            best_raw_objective=min((r['raw_check']['objective'] for r in records if r['raw_valid']), default=None),
            retained_sample_sha256=hashlib.sha256((source / filename).read_bytes()).hexdigest(),
            records=records)
        (output / filename).write_text(json.dumps(row, indent=2) + '\n')
        rows.append({key: value for key, value in row.items() if key != 'records'})
    stable = all(hashlib.sha256((root / name).read_bytes()).hexdigest() == expected
                 for name, expected in hashes.items())
    if not stable:
        raise AssertionError('Audit source changed')
    report = dict(protocol=protocol, rows=rows, source_stable=stable,
                  original_manifest_verified=True, model_inputs_verified=True,
                  wall_seconds=time.perf_counter() - began)
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    (output / 'manifest.json').write_text(json.dumps({str(path.relative_to(output)):
        hashlib.sha256(path.read_bytes()).hexdigest() for path in output.rglob('*') if path.is_file()}, indent=2) + '\n')
    return report


def run(output, deadline_source=Path('output/deadline-decision-review-v1'),
        original_source=Path('output/manufacturing-full-recovery-v1')):
    import dimod
    from dwave.samplers import SimulatedAnnealingSampler

    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    root = Path(__file__).resolve().parents[1]
    files = ['stage2/deadline_anneal.py', 'stage2/deadline_qubo.py', 'stage2/window_qubo.py']
    hashes = {}
    for name in files:
        source = root / name
        target = output / 'sources' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
        hashes[name] = hashlib.sha256(source.read_bytes()).hexdigest()
    tasks = [(case, kind) for case in ['heat-outage-32', 'heat-lease-32']
             for kind in ['deadline', 'original']]
    protocol = dict(seeds=[101, 103, 107, 109, 113], reads=16,
        binary_sweeps=1024, onehot_proposals_per_read=4096,
        onehot_temperature='Geometric4*penalty to0.02*penalty; symmetric one-operation swaps',
        tasks=[dict(case=case, kind=kind, cap=900) for case, kind in tasks],
        initialization='Cold binary random for dwave SA; cold uniform independent one-hot choices for grouped SA',
        budgets='Different update counts and kernels; no equal-budget or hardware superiority claim',
        selection='Known development fixtures; frozen settings before these outcomes, not held-out evaluation',
        reference_usage='No witness files or exact solutions read; native reference status loaded only after all samples saved',
        source_hashes=hashes, dimod=importlib.metadata.version('dimod'),
        dwave_samplers=importlib.metadata.version('dwave-samplers'),
        veloxq_calls=0, physical_qpu_calls=0)
    input_hashes = {}
    for case, kind in tasks:
        directory = deadline_source / f'{case}-cap-900' if kind == 'deadline' else original_source / case
        for name in ['problem.json', 'qubo.json']:
            path = directory / name
            input_hashes[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    protocol['input_sha256'] = input_hashes
    (output / 'protocol.json').write_text(json.dumps(protocol, indent=2) + '\n')
    began = time.perf_counter()
    rows = []
    for case, kind in tasks:
        directory = deadline_source / f'{case}-cap-900' if kind == 'deadline' else original_source / case
        model = load_model(directory, kind)
        if kind == 'original':
            deadline_problem = json.loads((deadline_source / f'{case}-cap-900' / 'problem.json').read_text())
            if digest(model.problem) != digest(deadline_problem):
                raise AssertionError('Original and deadline models use different raw inputs')
        bqm = dimod.BinaryQuadraticModel(dict(enumerate(model.linear)), model.quadratic,
                                        model.offset, dimod.BINARY)
        for seed in protocol['seeds']:
            for method in ['binary_sa', 'onehot_sa']:
                start = time.perf_counter()
                if method == 'binary_sa':
                    samples = SimulatedAnnealingSampler().sample(bqm, seed=seed,
                        num_reads=protocol['reads'], num_sweeps=protocol['binary_sweeps'])
                    raw = [dict(bits=[int(sample.sample[i]) for i in range(len(model.linear))],
                                energy=int(round(sample.energy)), count=int(sample.num_occurrences))
                           for sample in samples.data(sorted_by=None)]
                else:
                    raw = onehot_anneal(model, seed, protocol['reads'], protocol['onehot_proposals_per_read'])
                solver_seconds = time.perf_counter() - start
                records = checked_samples(model, raw, 900)
                feasible = [r for r in records if r['raw_valid']]
                target = [r for r in records if r['target_satisfied']]
                row = dict(case=case, kind=kind, method=method, seed=seed,
                    variables=len(model.linear), couplers=len(model.quadratic),
                    returned_samples=sum(r['count'] for r in records),
                    feasible_samples=sum(r['count'] for r in feasible),
                    raw_feasible_samples=sum(r['count'] for r in feasible),
                    encoded_feasible_samples=sum(r['count'] for r in records if r['encoded_valid']),
                    target_satisfied_samples=sum(r['count'] for r in target),
                    best_checked_objective=min((r['raw_check']['objective'] for r in feasible), default=None),
                    best_encoded_energy=min(r['energy'] for r in records),
                    solver_seconds=solver_seconds, wall_seconds=time.perf_counter() - start,
                    records=records, target_failure_means='Not found; never a heuristic infeasibility proof')
                path = output / f'{case}-{kind}-{method}-{seed}.json'
                path.write_text(json.dumps(row, indent=2) + '\n')
                rows.append({key: value for key, value in row.items() if key != 'records'})
                print(json.dumps(rows[-1]), flush=True)
    references = {}
    for case in ['heat-outage-32', 'heat-lease-32']:
        # Reporting only: opened after every stochastic run is complete.
        ref = json.loads((deadline_source / f'{case}-cap-900' / 'reference.json').read_text())
        references[case] = {k: ref[k] for k in ['status', 'target_feasible', 'query_sha256']}
    stable = all(hashlib.sha256((root / name).read_bytes()).hexdigest() == value
                 for name, value in hashes.items())
    if not stable:
        raise AssertionError('Source changed while controls were running')
    report = dict(protocol=protocol, rows=rows, references=references, source_stable=stable,
                  wall_seconds=time.perf_counter() - began, veloxq_calls=0, physical_qpu_calls=0)
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    (output / 'manifest.json').write_text(json.dumps({str(path.relative_to(output)):
        hashlib.sha256(path.read_bytes()).hexdigest() for path in output.rglob('*') if path.is_file()}, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--audit-source', type=Path)
    args = parser.parse_args()
    if args.audit_source:
        audit_retained(args.audit_source, args.output)
    else:
        run(args.output)
