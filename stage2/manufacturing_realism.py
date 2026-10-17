"""Fixed-grid full-recipe feature accounting and guarded scaling, entirely local."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import time

from .column_parents import generate
from .column_reference import solve_column_cp
from .operation_columns import operation_columns
from .operation_qubo import compile_operations
from .window_qubo import assignments, check_plan, compile_qubo, digest, solve_cp, validate


def feature_variants(problem):
    """Remove one modeled feature at a time; never label these exact reductions."""
    variants = {'full': deepcopy(problem)}
    for name in ['no_machine_setups', 'zero_transfer_lags', 'zero_worker_walk',
                 'continuous_worker_calendars', 'no_deadline_cost']:
        variant = deepcopy(problem)
        if name == 'no_machine_setups':
            variant.pop('machine_setups', None)
            variant.pop('machine_initial_family', None)
        elif name == 'zero_transfer_lags':
            variant['transport_lags'] = {a: {b: 0 for b in problem['machines']} for a in problem['machines']}
        elif name == 'zero_worker_walk':
            variant['worker_travel'] = 0
        elif name == 'continuous_worker_calendars':
            for worker in variant['workers'].values():
                worker['available'] = [[0, problem['horizon']]]
        elif name == 'no_deadline_cost':
            for op in variant['operations']:
                op['due'] = problem['horizon']
        variant.setdefault('provenance', {})['experimental_ablation'] = name
        validate(variant)
        variants[name] = variant
    return variants


def domain_counts(problem):
    rows = {op['id']: assignments(problem, op) for op in problem['operations']}
    naive_groups = [len(op['durations']) * len(problem['workers']) *
                    (problem['horizon'] // problem['grid'] + 1) for op in problem['operations']]
    counts = [len(rows[op['id']]) for op in problem['operations']]
    return dict(naive_assignment_product=sum(naive_groups),
                naive_one_hot_couplers_lower_bound=sum(n * (n - 1) // 2 for n in naive_groups),
                naive_scope='Eligible machine x every worker x every grid start before skill, calendar, release and duration checks; assignment family only, no complete naive QUBO claimed',
                unary_assignment_variables=sum(counts),
                cross_operation_pair_checks=sum(counts[i] * counts[j]
                    for i in range(len(counts)) for j in range(i + 1, len(counts))))


def model_summary(model, elapsed):
    values = [*model.linear, *model.quadratic.values()]
    absolute = [abs(value) for value in values if value]
    reduction = getattr(model, 'reduction', {})
    return dict(variables=len(model.linear),
        assignment_variables=sum(len(group) for name, group in model.groups.items() if name != '@makespan'),
        makespan_variables=len(model.groups['@makespan']), couplers=len(model.quadratic),
        build_seconds=elapsed, penalty=model.penalty,
        coefficient_min=min(values), coefficient_max=max(values),
        min_abs_nonzero_coefficient=min(absolute), max_abs_coefficient=max(absolute),
        coefficient_dynamic_range=max(absolute) / min(absolute),
        reduction={key: reduction[key] for key in ['method', 'before', 'after', 'pair_checks'] if key in reduction},
        coefficient_sha256=digest(dict(linear=model.linear, quadratic=[(i, j, value)
            for (i, j), value in sorted(model.quadratic.items())], offset=model.offset)))


def save(path, data):
    path.write_text(json.dumps(data, indent=2) + '\n')


def evaluate(problem, directory, protocol):
    directory.mkdir()
    save(directory / 'problem.json', problem)
    start = time.perf_counter()
    counts = domain_counts(problem)
    counts['count_seconds'] = time.perf_counter() - start
    row = dict(problem_sha256=digest(problem), operations=len(problem['operations']),
               horizon=problem['horizon'], grid=problem['grid'], counts=counts)
    # Heuristic input/initialization is produced before either native reference.
    parents = generate(problem, attempts=48, wanted=4, seed=7001, seconds=8)
    save(directory / 'parents.json', parents)
    row['parent_generation'] = {key: value for key, value in parents.items() if key != 'parents'}
    best = min(parents['parents'], key=lambda plan: check_plan(problem, plan)['objective']) if parents['parents'] else None
    if best is not None:
        row['heuristic_check'] = check_plan(problem, best)
        start = time.perf_counter()
        columns, restriction = operation_columns(problem, parents['parents'], cap=24, radius=240)
        column_seconds = time.perf_counter() - start
        save(directory / 'columns.json', columns)
        start = time.perf_counter()
        model = compile_operations(problem, columns)
        row['restricted'] = model_summary(model, time.perf_counter() - start)
        row['restricted'].update(candidate_generation_seconds=column_seconds, exact=False, restriction=restriction)
        del model
        ref = solve_column_cp(problem, columns, seconds=protocol['pool_cp_seconds'], workers=1, initial_plan=best)
        row['pool_reference'] = ref
        if 'plan' in ref:
            assert check_plan(problem, ref['plan'])['valid']
    else:
        row['restricted'] = dict(status='NO_HEURISTIC_PARENT', exact=False)
    # Guard BEFORE support propagation, which itself compares domain pairs.
    if counts['cross_operation_pair_checks'] <= protocol['max_pair_checks'] and counts['unary_assignment_variables'] <= protocol['max_assignment_variables']:
        for name, support in [('unary_complete', False), ('support_complete', True)]:
            start = time.perf_counter()
            model = compile_qubo(problem, support_pruning=support, max_variables=protocol['max_assignment_variables'] + 1000)
            row[name] = dict(model_summary(model, time.perf_counter() - start), exact=True)
            if best is not None:
                # Only audit the independently generated heuristic; no reference
                # optimum is supplied to either domain construction.
                chosen = {digest([part]) for part in best}
                present = {digest([part]) for part in model.variables if part['operation'] != '@makespan'}
                assert chosen <= present
            del model
    else:
        guard = dict(status='SKIPPED_COMPLEXITY_GUARD', exact_domain_count_available=False,
                     reason='Predeclared raw domain/pair guard; neither infeasibility nor candidate pruning',
                     requested_pair_checks=counts['cross_operation_pair_checks'])
        row['unary_complete'] = guard
        row['support_complete'] = dict(guard)
    row['raw_reference'] = solve_cp(problem, seconds=protocol['raw_cp_seconds'], workers=1, initial_plan=best)
    raw = row['raw_reference']
    candidates = [row['heuristic_check']['objective']] if best is not None else []
    candidates += [reference['objective'] for reference in [raw, row.get('pool_reference', {})] if 'objective' in reference]
    row['raw_objective_interval'] = dict(lower_bound=raw.get('bound'),
        checked_upper_bound=min(candidates) if candidates else None,
        certified=bool(raw.get('optimal')), qualification='Raw CP bound plus independently raw-checked witnesses; restricted optimality is not global')
    if raw.get('optimal') and 'objective' in row.get('pool_reference', {}):
        row['restricted_objective_loss'] = row['pool_reference']['objective'] - raw['objective']
    save(directory / 'report.json', row)
    return row


def run(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    root = Path(__file__).resolve().parents[1]
    names = ['manufacturing_realism.py', 'window_qubo.py', 'window_reduction.py', 'column_parents.py',
             'column_reference.py', 'operation_columns.py', 'operation_qubo.py', 'column_qubo.py', 'trajectory_qubo.py']
    hashes = {}
    for name in names:
        path = root / 'stage2' / name
        target = output / 'sources' / 'stage2' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(path.read_bytes())
        hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    base_path = root / 'output/manufacturing-recovery-v2/heat-lease-32/problem.json'
    scaling_paths = {size: root / f'output/manufacturing-study-v1/nominal-{size}/problem.json' for size in [32, 64, 128]}
    inputs = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in [base_path, *scaling_paths.values()]}
    variants = feature_variants(json.loads(base_path.read_text()))
    protocol = dict(schema='qfactoria-full-recipe-realism-frontier.v1', source_hashes=hashes,
        input_sha256=inputs, ablations=list(variants), scaling_operations=[32, 64, 128],
        raw_cp_seconds=10, raw_cp_workers=1, pool_cp_seconds=5, max_pair_checks=10_000_000,
        max_assignment_variables=6000, parent_seed=7001, parent_attempts=48, parent_wanted=4,
        per_operation_pool_cap=24, pool_radius=240,
        scope='Feature removals change the model; unary/support reductions preserve their own variant; restricted pools are lossy. All ablations share horizon1440/grid30/operations/resources.',
        naive_scope='Exact variable-family count and one-hot coupling lower bound only; naive complete coefficients/couplers intentionally not claimed',
        selection='Development fixtures/settings fixed before outcomes; not a held-out industrial evaluation',
        veloxq_calls=0, physical_qpu_calls=0)
    save(output / 'protocol.json', protocol)
    started = time.perf_counter()
    ablations, scaling = [], []
    for name, problem in variants.items():
        row = evaluate(problem, output / ('ablation-' + name), protocol)
        row['variant'] = name
        ablations.append(row)
        print(json.dumps(dict(variant=name, raw_status=row['raw_reference']['status'],
            raw_objective=row['raw_reference'].get('objective'), support_variables=row['support_complete'].get('variables'))), flush=True)
    for size, path in scaling_paths.items():
        row = evaluate(json.loads(path.read_text()), output / f'scaling-{size}', protocol)
        scaling.append(row)
        print(json.dumps(dict(operations=size, raw_status=row['raw_reference']['status'],
            restricted_variables=row['restricted'].get('variables'), support_status=row['support_complete'].get('status', 'COMPILED'))), flush=True)
    stable = all(hashlib.sha256((root / 'stage2' / name).read_bytes()).hexdigest() == value for name, value in hashes.items())
    if not stable:
        raise AssertionError('Accounting sources changed')
    report = dict(protocol=protocol, feature_ablations=ablations, scaling=scaling, source_stable=stable,
                  wall_seconds=time.perf_counter() - started, veloxq_calls=0, physical_qpu_calls=0)
    save(output / 'report.json', report)
    save(output / 'manifest.json', {str(path.relative_to(output)): hashlib.sha256(path.read_bytes()).hexdigest()
                                  for path in output.rglob('*') if path.is_file()})
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    run(parser.parse_args().output)
