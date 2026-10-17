"""Summarize local training and independent checks without selecting on optima."""
import argparse
import hashlib
import json
import math
from pathlib import Path

from .qaoa_campaign import save


def shots99(probability):
    if probability <= 0:
        return None
    return 1 if probability >= 1 else math.ceil(math.log(.01) / math.log1p(-probability))


def run(campaign, polish, audit, output):
    campaign, polish, audit, output = [p.resolve() for p in (campaign, polish, audit, output)]
    depth_report = json.loads((campaign / 'report.json').read_text())
    polish_report = json.loads((polish / 'report.json').read_text())
    checked = json.loads((audit / 'report.json').read_text())
    if not checked['valid']:
        raise ValueError('Independent audit failed')
    output.mkdir(parents=True, exist_ok=False)
    rows = []
    for case in ['heat-outage-32', 'heat-lease-32']:
        baseline = json.loads((campaign / case / 'historical-baseline.json').read_text())
        cvar = json.loads((polish / case / 'initial-selection.json').read_text())
        final_path = polish / case / 'selected-alpha-1.0.json'
        final = json.loads(final_path.read_text())
        variants = {}
        intermediate = [(str(alpha), json.loads((polish / case / f'selected-alpha-{alpha}.json').read_text()))
                        for alpha in (.5, .75)]
        selections = [('cvar', cvar), *[('cvar-' + name, row) for name, row in intermediate],
                      ('expectation', final)]
        for name, selected_row in selections:
            fit, assessment = selected_row['fit'], selected_row['assessment']
            probability = assessment['exact_hit_probability']
            runs = assessment['runs']
            variants[name] = dict(layers=fit['layers'], alpha=fit['alpha'],
                                  exact_hit_probability=probability, feasible_probability=assessment['feasible_probability'],
                                  ideal_shots_for_99_percent_hit=shots99(probability),
                                  probability_gain_vs_historical=probability / baseline['exact_hit_probability'],
                                  optimal_returns=sum(r['decoded']['valid'] and r['energy'] == assessment['sector_exact_energy'] for r in runs),
                                  valid_returns=sum(r['decoded']['valid'] for r in runs),
                                  sample_replicas=len(runs), optimal_shots=sum(r['optimal_samples'] for r in runs),
                                  total_shots=sum(r['shots'] for r in runs))
            variant = dict(case=case, fit=fit, qasm=assessment['qasm'],
                           selection='Minimum declared ' + name + ' training objective', physical_qpu_calls=0)
            save(output / f'{case}-{name}-selected.json', variant)
            (output / f'{case}-{name}-selected.qasm').write_text(assessment['qasm'])
        selected = dict(case=case, fit=final['fit'], qasm=final['assessment']['qasm'],
                        problem_sha256=hashlib.sha256((campaign / case / 'problem.json').read_bytes()).hexdigest(),
                        columns_sha256=hashlib.sha256((campaign / case / 'columns.json').read_bytes()).hexdigest(),
                        selection='Final expectation-objective selection; no exact-hit-based choice',
                        source=str(final_path), physical_qpu_calls=0)
        save(output / f'{case}-selected.json', selected)
        (output / f'{case}-selected.qasm').write_text(selected['qasm'])
        rows.append(dict(case=case, logical_qubits=final['assessment']['logical_qubits'],
                         baseline=dict(layers=baseline['layers'], exact_hit_probability=baseline['exact_hit_probability'],
                                       feasible_probability=baseline['feasible_probability'],
                                       ideal_shots_for_99_percent_hit=shots99(baseline['exact_hit_probability'])),
                         variants=variants))
    report = dict(rows=rows, transfers=checked['transfers'],
                  depth_trials=len(depth_report['rows']), polish_trials=len(polish_report['rows']),
                  retained_training_cpu_seconds_lower_bound=depth_report['training_cpu_seconds'] +
                  sum(json.loads(p.read_text())['process_cpu_seconds'] for p in polish.glob('*/alpha-*.fit.json')),
                  depth_resume_invocation_wall_seconds=depth_report['wall_seconds'],
                  polish_wall_seconds=polish_report['wall_seconds'], audit_wall_seconds=checked['wall_seconds'],
                  independent_audit_passed=True, physical_qpu_calls=0, remote_calls=0,
                  limitations=['Two known synthetic problems, restricted constructive pools, no quantum advantage',
                               'Training budgets and circuit depths exceed historical baseline',
                               'Whole-table exact classical simulation is not a scalable quantum execution',
                               'Fresh pools test transfer on known physical problems, not unseen factories',
                               'Interrupted in-flight CPU and exploratory pilot CPU excluded from lower bound',
                               'Logical unrestricted-connectivity circuits; no device noise or routing'])
    save(output / 'report.json', report)
    markdown = ['# Local QAOA training — 17 October 2026', '',
                'All results use this Mac, classical statevector simulation and the same restricted 32-operation models.', '',
                '| Case | Historical p2 seed7 | CVaR alpha.25 | CVaR alpha.5 | CVaR alpha.75 | Expectation | Final depth |',
                '|---|---:|---:|---:|---:|---:|---:|']
    for row in rows:
        c, e = row['variants']['cvar'], row['variants']['expectation']
        half, three = row['variants']['cvar-0.5'], row['variants']['cvar-0.75']
        markdown.append(f"| {row['case']} | {row['baseline']['exact_hit_probability']:.4%} | {c['exact_hit_probability']:.4%} | "
                        f"{half['exact_hit_probability']:.4%} | {three['exact_hit_probability']:.4%} | "
                        f"{e['exact_hit_probability']:.4%} | {e['layers']} |")
    markdown += ['', f"{report['depth_trials']} depth/multistart fits and {report['polish_trials']} tail-lifting fits. "
                  f"Retained fit CPU: at least {report['retained_training_cpu_seconds_lower_bound']:.1f} seconds.", '',
                 'The CVaR and expectation variants are selected by their respective training losses. '
                 'The final export uses the expectation selection, even if another variant has a higher measured optimum probability.', '',
                 'See report.json for fresh-pool transfer probabilities and all measured returns. '
                 'The classical constructor and exact/SA controls remain essential; no quantum advantage is established.']
    (output / 'report.md').write_text('\n'.join(markdown) + '\n')
    save(output / 'inputs.json', {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in [campaign / 'report.json', polish / 'report.json', audit / 'report.json']})
    save(output / 'manifest.json', {str(p.relative_to(output)): hashlib.sha256(p.read_bytes()).hexdigest()
                                    for p in output.rglob('*') if p.is_file()})
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['campaign', 'polish', 'audit', 'output']:
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.campaign, args.polish, args.audit, args.output), indent=2))
