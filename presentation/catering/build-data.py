"""Export V3 evidence into the static kitchen. No optimization or service call.

Every displayed plan is rechecked. Quantum selections must match an actual
retained raw sample; a CP witness is never presented as a quantum result.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from catering.check import check_plan
from catering.contracts import load_bundle
from catering.decode import decode
from catering.domain import make_plan


def read(path):
    return json.loads((ROOT / path).read_text())


def source(path):
    return dict(path=str(path), sha256=hashlib.sha256((ROOT / path).read_bytes()).hexdigest())


def score(decoded):
    return tuple(decoded['check']['metrics'][k] for k in ('U', 'W', 'B', 'R'))


def best_sample(bundle, payload):
    if payload.get('bundle_sha256', bundle['bundle_sha256']) != bundle['bundle_sha256']:
        raise ValueError('Different sample bundle')
    candidates = []
    for sample in payload['samples']:
        decoded = decode(bundle, sample['bits'])
        if decoded['energy'] != sample['reported_energy']:
            raise ValueError('Incorrect retained sample energy')
        if decoded['valid']:
            candidates.append((score(decoded), -sample['count'], sample['bits'], sample, decoded))
    if not candidates:
        raise ValueError('No valid sample')
    return min(candidates, key=lambda row: row[:3])[-2:]


def encoded_run(bundle, sample, decoded, path, key, label, **extra):
    if not decoded['valid']:
        raise ValueError('Invalid encoded replay')
    alternatives = []
    # A checked intervention, never a synthetic solver result. Dropping a
    # selected component exposes why packing food is not delivering a meal.
    for i, program in enumerate(bundle['options']):
        if not sample['bits'][i]:
            continue
        bits = sample['bits'].copy()
        bits[i] = 0
        group = next(g for g in bundle['onehot_groups'] if i in g['program_indices'])
        bits[group['idle_index']] = 1
        other = decode(bundle, bits)
        if not other['valid']:
            raise ValueError('Invalid drop-to-idle alternative')
        alternatives.append(dict(index=i, label=f'Skip x{i + 1}', bits=bits,
                                 plan=other['plan'], metrics=other['check']['metrics'],
                                 energy=other['energy'], valid=True))
    return dict(key=key, label=label, bits=sample['bits'], count=sample['count'],
                variable_order=bundle['variable_order'],
                options=[dict(p, operations=make_plan(bundle['instance'], [p])['operations'])
                         for p in bundle['options']],
                onehot_groups=bundle['onehot_groups'], size=bundle['size'],
                registers=bundle['registers'], plan=decoded['plan'],
                metrics=decoded['check']['metrics'], energy=decoded['energy'], valid=True,
                bundle_sha256=bundle['bundle_sha256'], bundle_id=bundle['bundle_id'],
                source=source(path), scope=bundle['scope'],
                representation_kind=bundle.get('representation_kind', 'restricted_portfolio'),
                alternatives=alternatives, **extra)


def raw_run(instance, snapshot, path):
    result = read(path)
    checked = check_plan(instance, snapshot, result['plan'])
    if not checked['valid'] or checked['metrics'] != result['check']['metrics']:
        raise ValueError('Invalid raw reference')
    return dict(key='raw', label='Classical · full declared grid', bits=[], options=[],
                variable_order=[], onehot_groups=[], registers=[], alternatives=[],
                plan=result['plan'], metrics=checked['metrics'], valid=True,
                execution_kind='classical', method_id=result['method_id'],
                reference_status=result['reference_status'], source=source(path),
                timings=result['timings'], scope=result['reference_scope'],
                representation_kind='raw_declared_grid', bundle_sha256=None, bundle_id=None,
                energy=None, size=None)


def export():
    cases = []
    cell_path = 'output/catering-complete-cell-v3'
    bundle = load_bundle(ROOT / cell_path / 'quantum-qubo.json')
    receipt = read('output/catering-complete-cell-demo-v3.json')
    sample_path = receipt['source_samples']
    payload = read(sample_path)
    sample = receipt['sample']
    if source(sample_path)['sha256'] != receipt['source_sha256'] or sample not in payload['samples']:
        raise ValueError('Quantum demo receipt is not a retained sample')
    decoded = decode(bundle, sample['bits'])
    if decoded['plan'] != receipt['plan'] or decoded['check'] != receipt['check']:
        raise ValueError('Demo receipt no longer agrees with the independent decoder')
    runs = [encoded_run(bundle, sample, decoded, sample_path, 'qaoa', 'QAOA · simulator',
                        execution_kind='quantum_simulator', method_id=payload['method_id'],
                        shots=payload['shots'], valid_shots=payload['valid_shots'],
                        reference_status='Observed optimum · controls also attain it')]
    controls_path = f'{cell_path}/p1-seed-2026/controls.json'
    controls = read(controls_path)
    for key in ('initializer', 'mixer-only'):
        control = controls[key]
        sample, decoded = best_sample(bundle, control)
        runs.append(encoded_run(bundle, sample, decoded, controls_path, key,
                                'Initializer control' if key == 'initializer' else 'Mixer-only control',
                                execution_kind='simulator_control', method_id=key,
                                shots=control['shots'], valid_shots=control['valid_shots'],
                                reference_status='Observed optimum · comparison control'))
    runs.append(raw_run(bundle['instance'], bundle['snapshot'], f'{cell_path}/reference-raw.json'))
    cases.append(dict(id='CELL', title='Two courses. One meal.',
                      instance=bundle['instance'], snapshot=bundle['snapshot'], runs=runs,
                      description='Complete small cell · all 32 legal batch programs · 35 data qubits',
                      report=read(f'{cell_path}/report.json')))
    for sid in ('S0', 'S1', 'S2', 'S3'):
        base = f'output/catering-paired-pilot-v1/{sid}-seed-2026'
        report = read(f'{base}/report.json')
        accepted = [r for r in report['steps'] if r['accepted']]
        if not accepted:
            raise ValueError('No accepted quantum plan to replay')
        last = accepted[-1]['step']
        step = f'{base}/step-{last:02d}'
        bundle = load_bundle(ROOT / step / 'qubo.json')
        payload = read(f'{step}/samples.json')
        sample, decoded = best_sample(bundle, payload)
        if decoded['plan'] != read(f'{base}/quantum-plan.json')['plan']:
            raise ValueError('Final plan is not the accepted retained sample')
        runs = [encoded_run(bundle, sample, decoded, f'{step}/samples.json', 'qaoa',
                            'QAOA · simulator', execution_kind='quantum_simulator',
                            method_id=payload['method_id'], shots=payload['shots'],
                            valid_shots=payload['valid_shots'], accepted_step=last,
                            reference_status='Best retained plan · seed 2026 · 8 portfolio updates')]
        # Same offered domain at the final accepted step, not a different pool.
        exact = read(f'{step}/exact-sector-reference.json')
        exact_plan = exact.get('plan')
        if exact_plan is None:
            raise ValueError('Expected a decoded same-domain reference')
        fixed = {p['id'] for p in bundle['snapshot']['fixed_batches']}
        ids = {p['id'] for p in exact_plan['batches']} - fixed
        bits = [int(p['id'] in ids) for p in bundle['options']] + [0] * len(bundle['onehot_groups'])
        for group in bundle['onehot_groups']:
            bits[group['idle_index']] = int(not any(bits[i] for i in group['program_indices']))
        decoded_exact = decode(bundle, bits)
        if decoded_exact['plan'] != exact_plan:
            raise ValueError('Exact-domain bit reconstruction changed the plan')
        runs.append(encoded_run(bundle, dict(bits=bits, count=1), decoded_exact,
                                f'{step}/exact-sector-reference.json', 'encoded',
                                'Exact · same offered portfolio', execution_kind='classical',
                                method_id='exact_sector_enumeration', reference_status='OPTIMAL within this portfolio'))
        runs.append(raw_run(bundle['instance'], bundle['snapshot'], f'{base}/raw-reference.json'))
        cases.append(dict(id=sid, instance=bundle['instance'], snapshot=bundle['snapshot'], runs=runs,
                          description='Larger kitchen · changing portfolios capped at 35 qubits',
                          report=report))
    evidence = dict(cell=read(f'{cell_path}/report.json'),
                    pilot=read('output/catering-paired-pilot-v1/report.json'),
                    scale=read('output/catering-foundation-v3/report.json'))
    target = Path(__file__).with_name('replay-data.json')
    target.write_text(json.dumps(dict(schema='catering-kitchen-replay.v3', cases=cases,
                                     evidence=evidence), indent=2) + '\n')
    print(f'Exported {len(cases)} V3 cases, {sum(len(c["runs"]) for c in cases)} checked runs; no solvers or services called')


if __name__ == '__main__':
    export()
