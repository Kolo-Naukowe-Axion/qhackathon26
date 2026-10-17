"""Read-only acceptance audit of retained non-VeloxQ merit evidence.

Historical factory audit: run at the commit recorded by its source receipts.
The active catering release uses check-catering-release.py.

No optimizer, SDK, network, quantum simulation or external publication is run.
Outputs are written only to a new, explicitly selected directory. A missing
agreed core artifact produces PENDING, never an inferred success.
"""
import argparse
from collections import Counter
import hashlib
import json
from fractions import Fraction
from pathlib import Path
import sys
import subprocess

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from stage2.window_qubo import assignments, check_plan, digest


def read(path):
    return json.loads((ROOT / path).read_text())


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def sealed(folder):
    """Check literal retained bytes, without requiring frozen sources be current."""
    manifest = read(Path(folder) / 'manifest.json')
    for name, expected in manifest.items():
        require(sha(Path(folder) / name) == expected, f'Manifest mismatch: {folder}/{name}')
    return len(manifest)


def baseline():
    from solver.stage1 import validate as validate_baseline
    cert = read('output/stage1-compact-ready/formulation-certificates.json')
    for case, makespan, bits, orders in [('2x2', 4, 1, 2), ('3x3', 8, 3, 6)]:
        c = cert[case]
        require(c['logical_bits'] == bits and c['represented_orders'] == orders, case)
        require(c['gap_to_full_machine_order_optimum'] == 0, case)
        require(c['independent_reference']['makespan'] == makespan, case)
        valid = [r for r in c['states'] if r['makespan'] is not None]
        require(len(valid) == orders and all(r['energy'] == r['makespan'] for r in valid), case)
        require(min(r['energy'] for r in c['states']) == makespan, case)
        schedule = read(f'schedule_{case}.json')
        require(schedule['makespan'] == makespan, case)
        require(not validate_baseline(read(f'instances/instance_{case}.json'), schedule['schedule'], schedule['makespan']), 'Official raw schedule invalid: ' + case)
    disclosure = (ROOT / 'docs/STAGE1_COMPACT.md').read_text()
    require(all(s in disclosure for s in ['72', '39', 'factorial classical', 'six']), 'Baseline preprocessing disclosure')
    return dict(official_optima_hours=[4, 8], baseline_3x3_bits=dict(naive=72, pruned=39, selected=3),
                selected_scope='Six earliest-start common orders; factorial classical preprocessing already reveals this tiny optimum')


def recovery():
    count = sealed('output/manufacturing-recovery-v2') + sealed('output/manufacturing-full-recovery-v1')
    rows = read('output/manufacturing-recovery-v2/report.json')['rows']
    answer = {}
    for row in rows:
        case = row['case']
        p = read(f'output/manufacturing-recovery-v2/{case}/problem.json')
        for key in ['initial', 'raw_reference', 'pool_reference']:
            ref = row.get(key, {})
            if ref.get('plan'):
                checked = check_plan(p, ref['plan'])
                require(checked['valid'] and checked['objective'] == ref['objective'], (case, key))
        raw, pool = row['raw_reference'], row['pool_reference']
        require(raw['optimal'] and pool['optimal'], f'Unproved recovery reference: {case}')
        answer[case] = {k: dict(tardiness=row[k]['check']['weighted_terminal_tardiness'],
                               makespan=row[k]['check']['makespan']) for k in ['raw_reference', 'pool_reference']}
    require(answer['heat-outage-32']['raw_reference'] == dict(tardiness=45, makespan=945), 'Outage result')
    require(answer['heat-lease-32']['raw_reference'] == dict(tardiness=0, makespan=855), 'Replacement result')
    require(answer['heat-lease-32']['pool_reference'] == dict(tardiness=45, makespan=945), 'Pool loss')
    return dict(manifest_files=count, result=answer, parameters='Synthetic; 30-minute start grid; due900; replacement360')


def frontier():
    folder = 'output/capacity-frontier-review-v1'
    files = sealed(folder)
    report = read(folder + '/report.json')
    for case in report['protocol']['cases']:
        p = read(f'{folder}/{case}/problem.json')
        previous = None
        for cap in report['protocol']['caps']:
            name = 'full' if cap is None else f'cap-{cap}'
            columns = read(f'{folder}/{case}/{name}/columns.json')
            kept = {k: {digest(c[0]) for c in options} for k, options in columns.items()}
            require(previous is None or all(previous[k] <= kept[k] for k in kept), 'Nonnested pool')
            if cap is None:
                require(all(kept[o['id']] == {digest(a) for a in assignments(p, o)} for o in p['operations']), 'Incomplete full domain')
            previous = kept
            row = read(f'{folder}/{case}/{name}/report.json')
            ref = row['reference']
            require(ref['optimal'] and ref['objective'] == ref['bound'], 'Unproved frontier row')
            require(check_plan(p, ref['plan']) == ref['check'], 'Frontier schedule mismatch')
    winner = next(r for r in report['rows'] if r['case'] == 'heat-lease-32' and r['cap'] == 64)
    require(winner['model']['variables'] == 2078 and winner['model']['couplers'] == 196228, 'Enriched count')
    require(winner['reference']['objective'] == 855, 'Enriched capacity benefit')
    return dict(manifest_files=files, recovered_optimum_bits=2078, recovered_optimum_couplers=196228,
                caveat='Known-fixture development frontier; no minimum sufficient encoding or held-out result')


def deadline():
    folder = 'output/deadline-decision-review-v1'
    files = sealed(folder)
    report = read(folder + '/report.json')
    expected = {('heat-outage-32', 900): (796, 32760, False),
                ('heat-lease-32', 900): (818, 33817, True),
                ('heat-lease-32', 855): (818, 33817, True),
                ('heat-lease-32', 854): (632, 21152, False)}
    actual = []
    for row in report['rows']:
        bits, edges, feasible = expected[row['case'], row['cap']]
        require(row['model']['variables'] == bits and row['model']['couplers'] == edges, 'Query count')
        ref = row['reference']
        # Native satisfaction records expose tri-state feasibility explicitly.
        require(ref['target_feasible'] is feasible, 'Query feasibility reference')
        require(row['query_sha256'] == row['model']['query_sha256'] == ref['query_sha256'], 'Query identity')
        actual.append(dict(case=row['case'], cap=row['cap'], bits=bits, couplers=edges, feasible=feasible))
    return dict(manifest_files=files, rows=actual,
                claim='Exact hard-deadline question, not lossless compression of original soft optimization')


def controls():
    files = sealed('output/deadline-anneal-review-v1') + sealed('output/deadline-anneal-report-audit-v2')
    r = read('output/deadline-anneal-report-audit-v2/report.json')
    require(r['original_manifest_verified'] and r['model_inputs_verified'], 'Reporting audit provenance')
    require(not r['protocol']['resampling'] and r['protocol']['solver_calls'] == 0, 'Reporting-only scope')
    require(len(r['rows']) == 40 and sum(x['returned_samples'] for x in r['rows']) == 640, 'Control sample count')
    require(all(x[k] == 0 for x in r['rows'] for k in ['encoded_feasible_samples', 'raw_feasible_samples', 'target_satisfied_samples']), 'Control count')
    return dict(manifest_files=files, runs=40, retained_samples=640, encoded_valid=0, raw_valid=0, target=0,
                caveat='Failure at declared local budgets is UNKNOWN; no classical hardness or sponsor advantage')


def scaling():
    r = read('output/manufacturing-study-v1/report.json')
    rows = [x for x in r['rows'] if x['case'] in ['nominal-32', 'nominal-64', 'nominal-128']]
    require({x['operations'] for x in rows} == {32, 64, 128}, 'Missing manufacturing scaling size')
    answer = []
    for row in rows:
        ref = row['raw_reference']
        require('status' in ref and 'bound' in ref and 'wall_seconds' in ref, 'Missing scaling accounting')
        answer.append(dict(operations=row['operations'], status=ref['status'], bound=ref['bound'], objective=ref.get('objective')))
    return dict(rows=answer, caveat='UNKNOWN is unresolved, not infeasible; restricted optimum is not a global optimum')


def microscope():
    from stage2.window_qubo import compile_qubo
    folder = 'output/stage2-entry-v2'
    files = sealed(folder)
    r = read(folder + '/report.json')
    totals = {}
    for method in ['qaoa_xy', 'uniform_onehot', 'sa_onehot']:
        rows = [x for x in r['rows'] if x['method'] == method]
        totals[method] = dict(runs=len(rows), valid=sum(x['valid'] for x in rows),
                              optimal_schedules=sum(x['decoded_objective_gap'] == 0 for x in rows),
                              encoded_minima=sum(x['encoded_energy_gap'] == 0 for x in rows))
    require(totals['qaoa_xy'] == dict(runs=60, valid=60, optimal_schedules=60, encoded_minima=57), 'Small QAOA totals')
    require(totals['sa_onehot']['encoded_minima'] == 60 and totals['uniform_onehot']['optimal_schedules'] == 59, 'Small classical totals')
    require(r['veloxq_calls'] == r['physical_qpu_calls'] == 0, 'Small-study backend scope')
    models = {}
    for row in r['rows']:
        case = row['case']
        if case not in models:
            models[case] = compile_qubo(read(f'{folder}/{case}/problem.json'), support_pruning=True)
        sample = read(f'{folder}/{case}/test-{row["method"]}-{row["seed"]}.json')
        q = models[case]
        require(q.energy(sample['bits']) == sample['energy'] == row['energy'], 'Small-study literal sample energy')
        require(q.decode(sample['bits']) == sample['decoded'], 'Small-study retained decoder')
        checked = check_plan(q.problem, sample['decoded']['plan'])
        require(checked['valid'] == row['valid'] and checked['objective'] == row['decoded_objective'], 'Small-study raw schedule')
    return dict(manifest_files=files, totals=totals, claim='Separate synthetic 18–34 logical-qubit cell; unequal work budgets; no quantum advantage')


def bridge():
    from stage2.column_qubo import compile_columns
    folder = 'output/recipe-bridge-review-v2'
    files = sealed(folder)
    report = read(folder + '/report.json')
    require(report['protocol']['cp_teacher_used'] is False, 'Bridge reference leakage declaration')
    require(report['protocol']['anchor_policy'] == 'first_and_incumbent', 'Bridge incumbent disclosure')
    require(len(report['rows']) == 6, 'Bridge cases/caps')
    totals = Counter()
    earlier = {}
    for row in report['rows']:
        case, cap = row['case'], row['cap']
        prefix = f'{folder}/{case}/cap-{cap}'
        p = read(f'{folder}/{case}/problem.json')
        columns = read(prefix + '/columns.json')
        covered = [r['operation'] for choices in columns.values() for r in choices[0]]
        require(len(covered) == len(set(covered)) == len(p['operations']) == 32, 'Bridge operation boundary')
        require(set(covered) == {o['id'] for o in p['operations']}, 'Bridge missing raw operations')
        current = {k: {digest(c) for c in options} for k, options in columns.items()}
        require(case not in earlier or all(earlier[case][k] <= current[k] for k in current), 'Bridge nonnested cap')
        earlier[case] = current
        q = compile_columns(p, columns)
        require(q.metadata() == row['model'], 'Bridge literal compilation mismatch')
        require(row['reference']['optimal'] and row['reference']['objective'] == row['exact_sector_energy'], 'Bridge exact/native mismatch')
        require(check_plan(p, row['reference']['plan']) == row['reference']['check'], 'Bridge native whole plan')
        require(len(row['runs']) == 9, 'Bridge repeated methods')
        for summary in row['runs']:
            method, seed = summary['method'], summary['seed']
            sample = read(prefix + f'/{method}-{seed}.json')
            require(sum(sample['observed_counts'].values()) == sample['samples'], 'Bridge shot reconciliation')
            require(sample['samples'] == (32 if method == 'sa_onehot' else 512), 'Bridge disclosed unequal sampling work')
            require(q.energy(sample['bits']) == sample['energy'], 'Bridge sample energy')
            decoded = q.decode(sample['bits'])
            require(decoded == sample['decoded'], 'Bridge literal decoder')
            require(sample['logical_qubits'] == len(q.linear), 'Bridge physical register claim')
            require(sample['sector_amplitudes'] == row['sector_states'], 'Bridge sector accounting')
            sampled_optima = sampled_feasible = 0
            for encoded_index, count in sample['observed_counts'].items():
                index = int(encoded_index)
                chosen = []
                for group in reversed(list(q.groups.values())):
                    index, choice = divmod(index, len(group))
                    chosen.append(group[choice])
                require(index == 0 and count > 0, 'Bridge observed sector index')
                bits = [0] * len(q.linear)
                for selected in chosen:
                    bits[selected] = 1
                energy = q.energy(bits)
                sampled_optima += count * (energy == row['exact_sector_energy'])
                sampled_feasible += count * (energy < q.penalty)
            require(sampled_optima == sample['optimal_samples'] and sampled_feasible == sample['feasible_samples'], 'Bridge retained probability/count claim')
            if decoded.get('valid'):
                checked = check_plan(p, decoded['plan'])
                require(checked['valid'] and checked == sample['whole_plan_check'], 'Bridge merged whole plan')
                require(checked['objective'] == decoded['objective'], 'Bridge raw objective')
                totals[case + ':' + method + ':valid'] += 1
                if checked['weighted_terminal_tardiness'] == 0:
                    totals[case + ':' + method + ':ontime'] += 1
            if method == 'qaoa_xy':
                require(bool(sample.get('qasm')) and sample['optimization'], 'Bridge actual quantum circuit/training')
        require(any(check_plan(p, plan)['objective'] == row['best_constructive']['objective']
                    for plan in read(f'{folder}/{case}/constructive-parents.json')['parents']), 'Bridge constructive baseline')
    circuit = read('output/recipe-bridge-circuit-audit-v1/report.json')
    sealed('output/recipe-bridge-circuit-audit-v1')
    require(circuit['valid'] and len(circuit['rows']) == 18 and circuit['full_hilbert_replayed'] == 6, 'Bridge independent circuit audit')
    for row in circuit['rows']:
        require(sha(row['source']) == row['source_sha256'], 'Bridge audited circuit source')
        if row['full_hilbert_replayed']:
            require(row['qubits'] == 18 and row['valid'] and row['probability_error'] < 1e-12 and row['outside_sector_probability'] < 1e-12, 'Bridge full replay error')
    return dict(manifest_files=files, rows=6, retained_runs=54,
                logical_qubits=[18, 28, 36], sector_amplitudes=[512, 26244, 262144],
                totals=dict(totals),
                caveat='All32operations retained through restricted constructive component trajectories. Best constructive parent already supplies optimum; exact sector preparation reveals restricted optimum; no quantum advantage.')


def packets():
    folder = 'output/sponsor-merit-packets-v1'
    files = sealed(folder)
    report = read(folder + '/report.json')
    require(report['veloxq_calls'] == report['physical_qpu_calls'] == 0, 'Packet backend scope')
    require(report['protocol']['cold_only'] and not report['protocol']['service_acceptance'], 'Packet service/initialization claim')
    for path, expected in report['protocol']['input_sha256'].items():
        require(sha(path) == expected, 'Packet input changed')
    require([r['variables'] for r in report['rows']] == [818, 2078, 2499], 'Packet formulation identity')
    # HDF5 is installed in the pinned SDK environment. This child imports only
    # the local loader and h5py, never SDK code or a remote adapter.
    program = r'''
import json
from pathlib import Path
import h5py
from stage2.sponsor_merit_packets import load_models
folder=Path('output/sponsor-merit-packets-v1')
report=json.loads((folder/'report.json').read_text())
models=dict(load_models()); count=0
tasks=[(folder/row['file'],models[row['case']])for row in report['rows']]
matched_folder=Path('output/sponsor-enriched-matched-penalty-v1')
matched=json.loads((matched_folder/'report.json').read_text())
from copy import deepcopy
q=deepcopy(models['enriched-2078']);old=q.penalty;new=matched['penalty']
assert new==matched['penalty_certificate']['witness_objective']+1==65791
q.linear=[v+old-new for v in q.linear]
assert all(v%old==0 for v in q.quadratic.values())
q.quadratic={ij:(v//old)*new for ij,v in q.quadratic.items()};q.offset=q.offset//old*new
tasks.append((matched_folder/matched['file'],q))
for path,q in tasks:
 with h5py.File(path,'r') as file:
  assert set(file)=={'Ising'}
  g=file['Ising']; assert [int(x) for x in g['labels'][:]]==list(range(len(q.linear)))
  fields=[int(x) for x in g['biases'][:]]; coupling=g['couplings']
  if isinstance(coupling,h5py.Group):
   directed={(int(i)-1,int(j)-1):int(v) for i,j,v in zip(coupling['I'][:],coupling['J'][:],coupling['V'][:])}
  else:
   dense=coupling[:];directed={(int(i),int(j)):int(dense[i,j])for i,j in zip(*dense.nonzero())}
  assert all(i!=j and directed.get((j,i))==v for (i,j),v in directed.items())
  edges={pair:v for pair,v in directed.items()if pair[0]<pair[1]}
  linear=[2*v for v in fields]
  for(i,j),v in edges.items():linear[i]-=2*v;linear[j]-=2*v
  assert linear==[4*v for v in q.linear]
  assert {ij:4*v for ij,v in edges.items()}=={ij:4*v for ij,v in q.quadratic.items()}
  assert g.attrs['offset']-sum(fields)+sum(edges.values())==4*q.offset
  count+=len(fields)+len(edges)+1
print(json.dumps(dict(exact_inverse_coefficients=count, sdk_imported=False)))
'''
    process = subprocess.run([str(ROOT / '.venv/bin/python'), '-c', program], cwd=ROOT,
                             capture_output=True, text=True, timeout=60)
    require(process.returncode == 0, 'Independent HDF5 inverse audit: ' + process.stderr[-1000:])
    matched_folder = 'output/sponsor-enriched-matched-penalty-v1'
    files += sealed(matched_folder)
    matched = read(matched_folder + '/report.json')
    require(sha(matched['protocol']['heuristic_parents']) == matched['protocol']['heuristic_parents_sha256'], 'Penalty witness provenance')
    return dict(manifest_files=files, **json.loads(process.stdout), cold_packets=4,
                caveat='Exact offline serialization only; no platform acceptance, internal arithmetic or solver-performance inference')


def realism():
    folder = 'output/realism-frontier-v1'
    files = sealed(folder)
    report = read(folder + '/report.json')
    require(len(report['feature_ablations']) == 6 and len(report['scaling']) == 3, 'Realism declared cases')
    guarded = []
    for family in ['feature_ablations', 'scaling']:
        for row in report[family]:
            name = ('ablation-' + row['variant']) if family == 'feature_ablations' else f'scaling-{row["operations"]}'
            p = read(f'{folder}/{name}/problem.json')
            require(digest(p) == row['problem_sha256'], 'Realism input identity')
            require(p['horizon'] == row['horizon'] and p['grid'] == row['grid'] == 30, 'Realism input-grid accounting')
            require(family != 'feature_ablations' or row['horizon'] == 1440, 'Realism ablation fixed horizon')
            raw_counts = [len(assignments(p, op)) for op in p['operations']]
            naive = [len(op['durations']) * len(p['workers']) * (p['horizon'] // p['grid'] + 1) for op in p['operations']]
            counts = row['counts']
            require(sum(naive) == counts['naive_assignment_product'], 'Naive variable-family count')
            require(sum(n * (n - 1) // 2 for n in naive) == counts['naive_one_hot_couplers_lower_bound'], 'Naive lower-bound count')
            require(sum(raw_counts) == counts['unary_assignment_variables'], 'Unary variable count')
            require(sum(raw_counts[i] * raw_counts[j] for i in range(len(raw_counts)) for j in range(i + 1, len(raw_counts))) == counts['cross_operation_pair_checks'], 'Pair guard count')
            for label in ['raw_reference', 'pool_reference']:
                ref = row.get(label, {})
                if 'plan' in ref:
                    checked = check_plan(p, ref['plan'])
                    require(checked['valid'] and checked['objective'] == ref['objective'], 'Feature reference raw plan')
                    require(checked == ref['check'], 'Feature reference checker details')
            for label in ['unary_complete', 'support_complete']:
                model = row[label]
                if model.get('status') == 'SKIPPED_COMPLEXITY_GUARD':
                    require(counts['cross_operation_pair_checks'] > report['protocol']['max_pair_checks'] or sum(raw_counts) > report['protocol']['max_assignment_variables'], 'Unjustified complexity guard')
                    guarded.append(name + ':' + label)
                    require('variables' not in model and not model['exact_domain_count_available'], 'Invented guarded count')
                else:
                    require(model['variables'] == model['assignment_variables'] + model['makespan_variables'], 'Feature variable family sum')
                    require(model['exact'] and model['build_seconds'] >= 0 and model['coefficient_dynamic_range'] >= 1, 'Feature complete metrics')
            require(row['restricted']['exact'] is False, 'Restriction mislabeled lossless')
            interval = row['raw_objective_interval']
            if interval['checked_upper_bound'] is not None:
                require(interval['lower_bound'] <= interval['checked_upper_bound'], 'Invalid reference interval')
    supplement_folder = 'output/realism-continuous-counts-v2'
    files += sealed(supplement_folder)
    supplement = read(supplement_folder + '/report.json')
    require(sha(supplement['reference_source']) == supplement['reference_report_sha256'], 'Supplement reference identity')
    require(supplement['source_stable'] and supplement['veloxq_calls'] == 0, 'Supplement source/backend scope')
    for label, bits, couplers in [('unary_complete', 14871, 9467283), ('support_complete', 9322, 3785787)]:
        model = supplement[label]
        require(model['variables'] == bits and model['couplers'] == couplers, 'Calendar supplement counts')
        require(model['assignment_variables'] + model['makespan_variables'] == bits, 'Calendar variable partition')
        require(model['onehot_couplers'] + model['makespan_links'] + sum(model['incompatibility_multiplicity_histogram'].values()) == couplers, 'Calendar edge partition')
        require(not model['global_quadratic_dictionary_allocated'], 'Calendar streaming scope')
    return dict(manifest_files=files, independently_counted_variants=9,
                guarded_complete_compilations=guarded,
                authoritative_calendar_supplement='output/realism-continuous-counts-v2',
                caveat='Naive counts are assignment-family counts and coupling lower bounds; no naive complete coefficient claim. Feature removal changes model. Calendar exact counts come from separately tested streaming v2, not failed v1;64/128 complete compilations remain guarded.')


def money_value(value):
    exact = Fraction(value['numerator'], value['denominator'])
    require(abs(float(exact) - value['value']) <= 1e-9, 'Rational display mismatch')
    return exact


def economics():
    folder = 'output/capacity-economics-v2'
    files = sealed(folder)
    report = read(folder + '/report.json')
    profile = report['protocol']['profile']
    require(profile['calibrated'] is False, 'Economic calibration claim')
    require(len(report['records']) == 4 and len(report['sensitivities']) == 135, 'Economic scope')
    def rates(t):
        clock = t % profile['tariff_period']
        return next(Fraction(b['pln_per_kwh']) for b in profile['tariffs'] if b['start'] <= clock < b['end'])
    def integral(start, end):
        return sum((rates(t) for t in range(start, end)), Fraction())
    for name, record in report['records'].items():
        case = 'heat-outage-32' if name == 'outage_complete' else 'heat-lease-32'
        p = read(f'output/manufacturing-recovery-v2/{case}/problem.json')
        plan = record['plan']
        require(check_plan(p, plan) == record['check'], 'Economic raw schedule')
        require(digest(p) == record['problem_sha256'] and digest(plan) == record['plan_sha256'], 'Economic identities')
        require(digest(profile) == record['profile_sha256'], 'Economic profile identity')
        machines = {}
        active = Fraction()
        attendance = night = 0
        for row in plan:
            active += Fraction(profile['active_kw'][row['machine'].rstrip('0123456789')]) * integral(row['start'], row['end']) / 60
            attendance += row['attended_end'] - row['start']
            night += sum(any(a <= t % profile['tariff_period'] < b for a, b in profile['night_intervals']) for t in range(row['start'], row['attended_end']))
            machines.setdefault(row['machine'], []).append(row)
        idle = Fraction()
        for rows in machines.values():
            occupied = {t for r in rows for t in range(r['start'], r['end'])}
            idle += sum((rates(t) for t in range(min(r['start'] for r in rows), max(r['end'] for r in rows)) if t not in occupied), Fraction())
        expected = dict(active_electricity=active,
                        standby_electricity=Fraction(profile['standby_kw']) * idle / 60,
                        base_electricity=Fraction(profile['base_load_kw']) * integral(0, record['check']['makespan']) / 60,
                        labor=Fraction(profile['labor_pln_per_attended_hour']) * attendance / 60,
                        night_premium=Fraction(profile['night_premium_pln_per_attended_hour']) * night / 60,
                        machine_start=Fraction(profile['machine_start_pln']) * len(machines),
                        late_penalty=Fraction(profile['late_pln_per_weighted_minute']) * record['check']['weighted_terminal_tardiness'])
        expected['operating'] = sum((v for k, v in expected.items() if k != 'late_penalty'), Fraction())
        expected['total_before_capacity_fee'] = expected['operating'] + expected['late_penalty']
        require(all(money_value(record['money'][k]) == v for k, v in expected.items()), 'Independent minute-wise cost ledger')
        require(record['attended_minutes'] == attendance and record['night_attended_minutes'] == night, 'Economic staffing minutes')
    for row in [*report['sensitivities'], report['illustrative_repeated_exposure']]:
        variant = row.get('variant', 'replacement_complete')
        base, replacement = report['records']['outage_complete'], report['records'][variant]
        saved = base['check']['weighted_terminal_tardiness'] - replacement['check']['weighted_terminal_tardiness']
        operating = money_value(base['money']['operating']) - money_value(replacement['money']['operating'])
        gross = operating + money_value(row['late_rate']) * saved
        net = gross - money_value(row['event_fee'])
        annual = row['exposures_per_year'] * money_value(row['probability']) * net - money_value(row['annual_maintenance'])
        present = sum((annual / (1 + money_value(row['discount_rate'])) ** year for year in range(1, row['years'] + 1)), Fraction()) - money_value(row['installation'])
        require(row['saved_weighted_late_minutes'] == saved, 'Economic saved lateness')
        require(money_value(row['maximum_event_fee']) == gross and money_value(row['event_net_benefit']) == net, 'Economic event threshold')
        require(money_value(row['expected_annual_net']) == annual and money_value(row['present_value_of_net']) == present, 'Economic discounted sensitivity')
    return dict(manifest_files=files, independently_minute_valued_plans=4, sensitivity_rows=135,
                maximum_event_fee_at_rate10=str(money_value(report['records']['outage_complete']['money']['total_before_capacity_fee']) - money_value(report['records']['replacement_complete']['money']['total_before_capacity_fee'])),
                caveat='Exact declared-plan valuation and conditional break-even; original plans optimize priority objective, not monetary cost; synthetic rates and event probabilities')


def failures():
    files = sum(sealed('output/' + p) for p in ['deadline-boundary-review-v1', 'deadline-boundary-review-v2',
                                               'recipe-bridge-review-v1', 'realism-continuous-counts-v1'])
    pilot = read('output/manufacturing-anneal-pilot-v1/report.json')
    require(len(pilot['rows']) == 60, 'Retained pilot runs')
    counts = Counter()
    for row in pilot['rows']:
        counts[row['penalty']] += row['feasible_samples']
    require(counts == dict(original_bound=21, checked_incumbent_bound=1), 'Retained failed penalty study')
    return dict(manifest_files=files, historical_penalty_runs=60, feasible_by_penalty=dict(counts),
                caveat='Original pilot has no standalone manifest; its retained raw samples are covered by the independent manufacturing audit, rather than inventing a seal')


def final_checks(receipt_path):
    receipt = read(receipt_path)
    commands = receipt['commands']
    require(commands and all(r['exit_code'] == 0 for r in commands), 'Final command failure')
    texts = [' '.join(r['command']) if isinstance(r['command'], list) else r['command'] for r in commands]
    require(any('unittest' in s or 'pytest' in s for s in texts), 'Missing final Python model tests')
    require(any('node' in s or 'npm test' in s for s in texts), 'Missing final JS/presentation tests')
    require(any('npm run build' in s for s in texts), 'Missing final static build')
    hashes = receipt['source_hashes']
    require(hashes, 'Missing final source scope')
    for path, expected in hashes.items():
        require(sha(path) == expected, 'Final tested source changed: ' + path)
    return dict(receipt=str(receipt_path), receipt_sha256=sha(receipt_path), commands=len(commands), tested_source_files=len(hashes))


def document_consistency(receipt_path):
    receipt = read(receipt_path)
    require(receipt['status'] == 'passed' and receipt['checks'], 'Document consistency incomplete')
    require(all(x['passed'] for x in receipt['checks']), 'Document consistency discrepancy')
    hashes = receipt['source_hashes']
    expected = {'README.md', 'PROJECT_DESIGN.md', 'DEVELOPMENT_LOG.md',
                'docs/STAGE2_COMBINED_DIRECTION.md', 'docs/STAGE2_SUBMISSION.md'}
    require(expected <= set(hashes), 'Incomplete authoritative document scope')
    require(any(s.startswith('presentation/manufacturing/') for s in hashes), 'No checked studio artifact')
    for path, value in hashes.items():
        require(sha(path) == value, 'Document/display changed after audit: ' + path)
    return dict(receipt=str(receipt_path), receipt_sha256=sha(receipt_path), checks=len(receipt['checks']), files=len(hashes))


def audit(validation_receipt='output/merit-final-checks-v1/report.json',
          consistency_receipt='output/merit-document-consistency-v1/report.json'):
    requirements = []
    def add(key, title, category, authority, evidence, acceptance, checker=None, status=None):
        item = dict(id=key, requirement=title, category=category, authority=authority,
                    evidence=evidence, acceptance=acceptance)
        if checker:
            try:
                item['checked_result'] = checker()
                item['status'] = 'passed'
            except FileNotFoundError as e:
                item.update(status='pending', remaining=f'Missing agreed artifact: {e}')
            except (AssertionError, KeyError, ValueError) as e:
                item.update(status='failed', remaining=str(e))
        else:
            item['status'] = status or 'pending'
        requirements.append(item)

    add('C01', 'Correct official baselines and comparable 3×3 encoding count', 'non_velox_core',
        ['Challenge §4 gate', 'Challenge §5 comparable number', 'Combined plan preamble'],
        ['output/stage1-compact-ready/formulation-certificates.json', 'docs/STAGE1_COMPACT.md', 'schedule_2x2.json', 'schedule_3x3.json'],
        '4/8-hour optima; 72 naive/39 pruned/3 selected bits; six-order classical tabulation and representation limits disclosed.', baseline)
    add('C02', 'Checked full-recipe manufacturing recovery centerpiece', 'non_velox_core',
        ['Combined plan item1', 'Review priority1', 'Challenge §5 depth'],
        ['output/manufacturing-recovery-v2/', 'output/manufacturing-full-recovery-v1/'],
        'Identical32-operation problems, complete references, 45→0 weighted late minutes and945→855 makespan; raw plans checked.', recovery)
    add('C03', 'Nested representation/quality frontier and stronger pool control', 'non_velox_core',
        ['Combined plan item2', 'Review priority1', 'Review pass3'],
        ['stage2/capacity_frontier.py', 'output/capacity-frontier-review-v1/', 'docs/STAGE2_CAPACITY_FRONTIER.md'],
        'All pools nested and legal; full spans unary domain; independent native bounds;2,078-bit pool preserves0/855 optimum.', frontier)
    add('C04', 'Exact hard-deadline operational query', 'non_velox_core',
        ['Review priority1', 'Challenge §5 compact/correct formulation'],
        ['stage2/deadline_qubo.py', 'stage2/deadline_reference.py', 'output/deadline-decision-review-v1/'],
        'Zero iff all original operations legally meet dues and cap; independent tri-state reference;818/33,817 positive query; no false infeasibility from sampling.', deadline)
    add('C05', 'Repeated local controls and physical-versus-encoded validity', 'non_velox_core',
        ['Combined plan item4 local controls', 'Review priority2', 'Challenge §5 verified quality'],
        ['output/deadline-anneal-review-v1/', 'output/deadline-anneal-report-audit-v2/'],
        'Forty frozen cold runs/640 retained samples; reporting audit confirms0encoded-valid/0raw-valid/0target; all work/budgets disclosed.', controls)
    add('C06', 'Manufacturing scaling32/64/128 with honest reference status', 'non_velox_core',
        ['Combined plan item1', 'Review priority1', 'Challenge §5 scaling'],
        ['output/manufacturing-study-v1/', 'docs/STAGE2_MANUFACTURING_STUDY.md'],
        'Per-size construction/solver metadata, incumbents/bounds/statuses; UNKNOWN and pool restrictions explicit.', scaling)
    add('C07', 'Audited separate assignment-QAOA correctness study', 'non_velox_core',
        ['Combined plan item3 retained study', 'Challenge §11 correct quantum implementation'],
        ['output/stage2-entry-v2/', 'output/stage2-entry-circuit-audit-v1/', 'docs/STAGE2_ENTRY.md'],
        '60/60 optimal schedules,57/60 encoded minima; SA60/60; uniform59/60;18–34logicalqubits; independent circuit audit and unequal budgets disclosed.', microscope)
    add('C08', 'Quantum comparison on a recovery-derived full-recipe restriction', 'non_velox_core',
        ['Combined plan item3', 'Review priority3', 'Challenge §5 one integrated result'],
        ['stage2/recipe_bridge.py', 'output/recipe-bridge-review-v2/', 'docs/STAGE2_RECIPE_BRIDGE.md'],
        'All32operations and cross-component joins retained; independent conditional headroom/reference; repeated actual QAOA/SA/uniform/exact on identical restrictions; whole-plan checks, source snapshots and all preprocessing costs.',
        bridge)
    add('C09', 'Per-feature price-of-realism accounting on the actual model', 'non_velox_core',
        ['Combined plan item2', 'Review priority4', 'Challenge §5 price of realism'],
        ['stage2/manufacturing_realism.py', 'output/realism-frontier-v1/', 'output/realism-continuous-counts-v2/', 'docs/STAGE2_REALISM_FRONTIER.md'],
        'Fixed horizon/grid; features mapped to naive/unary counts and bounded safely-pruned/restricted metrics, coefficients, timing and native/pool quality; explicitly skipped complete compilations and grid loss distinguished.',
        realism)
    add('C10', 'Current sponsor formulations prepared and audited entirely offline', 'non_velox_core',
        ['Combined plan item1 offline packets', 'Review priority2 integration preparation'],
        ['stage2/sponsor_merit_packets.py', 'output/sponsor-merit-packets-v1/', 'output/sponsor-enriched-matched-penalty-v1/', 'docs/STAGE2_SPONSOR_PACKETS.md'],
        'Cold818query/2,078enriched/2,499complete plus matched-penalty2,078packet; independent literal-coefficient inverse Ising audit, labels/offsets/scale, no hidden reference initialization or network calls.',
        packets)
    add('C11', 'Economic sensitivity and capacity break-even answer', 'non_velox_core',
        ['Combined plan item5', 'Review priority4', 'Challenge §5 functional scaling'],
        ['stage2/capacity_economics.py', 'output/capacity-economics-v2/'],
        'Explicit rates/scenario assumptions; independently checked cost ledger and break-even;45weighted minutes translate to45c only under declared objective/weights; no unproved minimum-cost or calibrated ROI claim.',
        economics)
    add('C12', 'One authoritative design/log/README/submission/UI story', 'non_velox_core',
        ['Combined plan item6 local preparation', 'Review priority5', 'Challenge §11 consistency/design/log'],
        ['PROJECT_DESIGN.md', 'DEVELOPMENT_LOG.md', 'README.md', 'docs/STAGE2_COMBINED_DIRECTION.md', 'docs/STAGE2_SUBMISSION.md', 'presentation/manufacturing/'],
        'All current entrypoints include enriched frontier, deadline query, integrated quantum scope, economics and feature table; no stale claim that2,499bits is necessary; links/hashes/claims and static build checked.',
        lambda: document_consistency(consistency_receipt))
    add('C13', 'Reproducible final local acceptance tests and build', 'non_velox_core',
        ['Combined plan item6 reproducibility', 'Challenge §11 reproducibility/consistency'],
        ['scripts/verify-stage2-merit.py', 'tests/stage2/', 'tests/manufacturing-studio.test.mjs', 'package.json'],
        'Run targeted meaningful tests for changed model/compiler/bridge/economics/packets plus presentation checks and static build on final sources; retained command result and hash scope recorded.',
        lambda: final_checks(validation_receipt))
    add('C14', 'Preserve failures and distinguish solver loss from representation loss', 'non_velox_core',
        ['Combined plan item2', 'Review corrections', 'Challenge §5 state approximation gaps'],
        ['docs/STAGE2_REVIEW_PASSES.md', 'output/deadline-boundary-review-v1/', 'output/deadline-boundary-review-v2/', 'output/manufacturing-anneal-pilot-v1/', 'output/recipe-bridge-review-v1/', 'output/realism-continuous-counts-v1/'],
        'Failed greedy quantum gates, failed penalty tuning, sampling failures, initial bridge pool loss and rejected streaming-countv1 remain accessible; successful bridge/countv2 are distinct corrected evidence.',
        failures)
    add('V01', 'Actual VeloxQ pilot and bounded sponsor scaling campaign', 'held_external',
        ['Combined plan item4', 'Review priority2', 'Challenge §5/§11 sponsor'],
        ['docs/STAGE2_VELOXQ_RUNBOOK.md'],
        'Separate authorization lifts backend/credit hold; validated platform limits and cost; identical-model baselines, repeated raw returned schedules, full time/cost accounting.', status='held')
    add('R01', 'Recovery-centered final ≤3-minute video', 'release_or_human',
        ['Combined plan item6', 'Review priority5', 'Challenge §11 video'],
        ['docs/STAGE2_MANUFACTURING_VIDEO_SCRIPT.json', 'output/manufacturing-video-v3/receipt.json'],
        'Local cut/script matches final newly extended evidence; duration≤180s; human content review, accessible hosted URL and upload separate.', status='pending')
    add('R02', 'Live presentation and Q&A readiness', 'release_or_human',
        ['Combined plan item6', 'Challenge §11 live'], ['docs/STAGE2_LIVE_SCRIPT.md'],
        'Team understands code/model, rehearses slot and answers limitations. Cannot be completed by local documents alone.', status='human_required')
    add('R03', 'Public MIT repository, exact release and submission receipt', 'release_or_human',
        ['Combined plan item6', 'Challenge submission requirements'], ['docs/STAGE2_SUBMISSION.md'],
        'Separately authorize exact public release/commit/push; verify visibility/license; human team/declaration data, final video URL, official form and receipt.', status='held')
    add('S01', 'Full calibrated weekly monetary optimization and purchase ROI', 'optional_stretch',
        ['Combined plan item5 explicit stretch'], [],
        'Not promised for core completion. Requires new tariff/overtime/activation/investment assumptions, optimization model and matching independent reference.', status='optional')
    add('S02', 'Stochastic robust scheduling, external industrial data and QOBLIB trials', 'optional_stretch',
        ['Combined plan secondary work', 'Review corrections'], [],
        'Not required for accepted combined core; must not be inferred from a linear exposure proxy or synthetic scenarios.', status='optional')
    counts = dict(Counter(x['status'] for x in requirements))
    core = [x for x in requirements if x['category'] == 'non_velox_core']
    return dict(schema='qfactoria-stage2-merit-acceptance.v1', auditor_sha256=sha(Path(__file__)),
                scope='Read-only retained-artifact audit; not optimizer execution, public release, independent run authentication, prize eligibility or claimed score',
                requirements=requirements, counts=counts,
                non_velox_core_complete=all(x['status'] == 'passed' for x in core),
                incomplete_core=[x['id'] for x in core if x['status'] != 'passed'],
                veloxq_calls=0, physical_qpu_calls=0, solver_calls=0)


def markdown(result):
    lines = ['# Stage 2 merit acceptance matrix', '',
             '17 October 2026. This matrix audits agreed non-VeloxQ merit work against the official challenge and combined plan. It does not declare the goal complete, certify a prize, or authorize remote use/publication.', '',
             f'The current machine-readable snapshot is [requirements.json](../{result.get("report_path", "output/merit-audit-v1/requirements.json")}). Re-run the verifier into a fresh output directory after new evidence arrives. A missing artifact stays pending. Frozen campaign source hashes identify historical code; they need not equal later implementation hashes.', '',
             'Authority: [official challenge](../Quantum_Hackathon_2026_ERP_Challenge.pdf), §§4–5 and11; [combined plan](STAGE2_COMBINED_DIRECTION.md), items1–6; [independent review](STAGE2_REVIEW_PASSES.md), priorities1–5.', '',
             '| ID | Scope | Status | Requirement and completion evidence |', '|---|---|---|---|']
    for item in result['requirements']:
        proofs = ', '.join(f'`{p}`' for p in item['evidence']) or 'Explicit optional scope'
        lines.append(f"| {item['id']} | {item['category']} | **{item['status']}** | {item['requirement']}. {proofs} |")
    lines += ['', '## Completion rules', '',
              'Each non-VeloxQ core item needs semantic acceptance, not merely a file. Actual backend calls remain held. Final video production/review, live rehearsal and public release/submission are tracked separately; unfinished external duties do not become completed because local numerical work passes.', '',
              'The weekly calibrated monetary model, stochastic robustness, external data and QOBLIB are explicitly optional. Parameterized economics is core. No feature may be silently dropped by changing this checklist.', '',
              '## Exact current-document fixes to apply with final integration', '',
              '- `docs/STAGE2_COMBINED_DIRECTION.md`: replace the outstanding-item3 paragraph with actual bridge results when checked; keep its restriction, preprocessing cost and source identity. Add the final fixed-grid feature table and economic artifact links.',
              '- `docs/STAGE2_ENTRY.md`: retain the separate18–34qubit study specification, but link the later full-recipe bridge instead of allowing the small fixture to serve as the only quantum entrypoint.',
              '- `docs/STAGE2_MANUFACTURING_STUDY.md`: append enriched cap64 and exact deadline comparisons; its original pool table is historical evidence, not the final representation frontier.',
              '- `docs/STAGE2_SUBMISSION.md`: rewrite the material table and summary around final manufacturing/query/bridge/economics/feature artifacts. Earlier claims that offline packets top out at1,602bits or that `/entry/` is the main demonstration are superseded.',
              '- `PROJECT_DESIGN.md`, `README.md`, `DEVELOPMENT_LOG.md`, current studio data and live script: use identical final numbers and labels. Preserve complete-versus-pool and decision-versus-optimization distinctions.',
              '- Video/script: current manufacturing-v3 cut predates the new frontier/query/bridge evidence. Keep it labeled review draft until final content is reconciled.', '',
              '## Verification', '',
              '```sh', '.venv-stage2/bin/python scripts/verify-stage2-merit.py --output output/NEW-MERIT-AUDIT', '```', '',
              'The command verifies retained manifests, input-domain nesting, whole-plan checks and numerical identities without any optimizer, SDK, network or quantum execution. The overall result remains incomplete while an agreed core acceptance item is pending or failed.']
    if next(item for item in result['requirements'] if item['id'] == 'C12')['status'] == 'passed':
        first = lines.index('## Exact current-document fixes to apply with final integration')
        last = lines.index('## Verification')
        lines[first:last] = ['## Consistency closure', '',
                             'The final source-hashed document/display receipt resolves the earlier stale scope and artifact references. Historical failure reports remain separate. This closes local consistency; final video review, live rehearsal and public release remain explicitly tracked above.', '']
    return '\n'.join(lines) + '\n'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--write-doc', action='store_true', help='Write the new merit acceptance document from this snapshot')
    parser.add_argument('--allow-pending', action='store_true', help='Development only: permit unresolved core acceptance items without exit status2')
    parser.add_argument('--validation-receipt', default='output/merit-final-checks-v1/report.json')
    parser.add_argument('--consistency-receipt', default='output/merit-document-consistency-v1/report.json')
    args = parser.parse_args()
    result = audit(args.validation_receipt, args.consistency_receipt)
    result['report_path'] = str(args.output / 'requirements.json')
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / 'requirements.json').write_text(json.dumps(result, indent=2) + '\n')
    if args.write_doc:
        (ROOT / 'docs/STAGE2_MERIT_ACCEPTANCE.md').write_text(markdown(result))
    print(json.dumps({k: result[k] for k in ['counts', 'non_velox_core_complete', 'incomplete_core', 'solver_calls', 'veloxq_calls']}, indent=2))
    sys.exit(1 if any(x['status'] == 'failed' for x in result['requirements']) else
             2 if not result['non_velox_core_complete'] and not args.allow_pending else 0)
