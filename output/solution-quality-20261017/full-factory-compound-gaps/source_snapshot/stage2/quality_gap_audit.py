"""Posthoc realized-instance optimality intervals for every frozen final group.

Reads original valid outcome rows; it does not tune a policy or run a factory.
For each physical tape, the quality/material certificate is a primary lower
bound and the best valid retained execution is a primary upper bound. Neither
is claimed to optimize deadline debt/cost or a nonanticipating policy.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import time

from .quality_material_bound import certificate
from .spec import build

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def config_key(config):
    return json.dumps(config, sort_keys=True, separators=(',', ':'))


def summarize(rows, bounds):
    """Strict actor-within-tape weighting; never discard an invalid outcome."""
    groups, best, anchors = defaultdict(list), {}, {}
    for row in rows:
        if not (row['valid'] and row['terminal_requirements_met'] and row['identity_audit']['valid']):
            raise ValueError('Invalid execution in complete group')
        if row['issues']:
            raise ValueError('Execution with unresolved issues')
        config = config_key(row['config'])
        tape = (config, row['seed'])
        if tape not in bounds:
            raise ValueError('Missing numerical bound')
        bound = bounds[tape]
        if row['physical_instance_sha256'] != bound['instance_sha256']:
            raise ValueError('Mismatched physical instance')
        if row['checker_metrics']['unfulfilled_orders'] != row['metrics']['orders']-row['metrics']['shipped']:
            raise ValueError('Checker/outcome disagreement')
        missing = row['checker_metrics']['unfulfilled_orders']
        if type(missing) is not int or missing < bound['unfulfilled_lower_bound']:
            raise ValueError('Observed outcome contradicts lower bound')
        if row['metrics']['orders'] != bound['observed_realized_orders']:
            raise ValueError('Realized demand mismatch')
        weight = Fraction(str(row['tape_weight']))
        if weight <= 0:
            raise ValueError('Nonpositive tape weight')
        if tape in anchors and anchors[tape] != (weight, tuple(row['leaf_outcomes'])):
            raise ValueError('Inconsistent tape weight or leaf')
        anchors[tape] = weight, tuple(row['leaf_outcomes'])
        best[tape] = min(best.get(tape, missing), missing)
        groups[row['cohort'], row['method_id'], config].append(row)
    results = []
    for (cohort, method, config), members in sorted(groups.items()):
        tapes = defaultdict(list)
        for row in members:
            tapes[row['seed']].append(row)
        actors = None
        total_weight = Fraction(0)
        lower = upper = observed = gap_lower = gap_upper = attained = Fraction(0)
        for seed, replicas in tapes.items():
            these_actors = {row['policy_seed'] for row in replicas}
            if len(these_actors) != len(replicas):
                raise ValueError('Duplicate actor execution')
            if actors is not None and actors != these_actors:
                raise ValueError('Incomplete actor/tape group')
            actors = these_actors
            tape = config, seed
            weight = anchors[tape][0]
            total_weight += weight
            lb = bounds[tape]['unfulfilled_lower_bound']
            ub = best[tape]
            mean_missing = sum(Fraction(r['checker_metrics']['unfulfilled_orders']) for r in replicas)/len(replicas)
            lower += weight*lb
            upper += weight*ub
            observed += weight*mean_missing
            gap_lower += weight*(mean_missing-ub)
            gap_upper += weight*(mean_missing-lb)
            attained += weight*Fraction(sum(r['checker_metrics']['unfulfilled_orders']==lb for r in replicas),len(replicas))
        if total_weight != 1:
            raise ValueError('Complete tape weights must sum exactly to one')
        results.append(dict(cohort=cohort, method_id=method, config=json.loads(config),
            tapes=len(tapes), actors_per_tape=len(actors), executions=len(members),
            mean_missing=float(observed), realized_optimum_mean_interval=[float(lower),float(upper)],
            mean_excess_missing_interval=[float(gap_lower),float(gap_upper)],
            probability_primary_optimum_certified=float(attained),
            exact_rationals=dict(mean_missing=[observed.numerator,observed.denominator],
                optimum_mean_lower=[lower.numerator,lower.denominator],
                optimum_mean_upper=[upper.numerator,upper.denominator],
                gap_lower=[gap_lower.numerator,gap_lower.denominator],
                gap_upper=[gap_upper.numerator,gap_upper.denominator],
                primary_optimum_attainment=[attained.numerator,attained.denominator])))
    return results


def execute(index_path, summary_path, output, bound_kind='max_step'):
    if bound_kind not in ('max_step','compound'):
        raise ValueError('Unknown necessary-bound method')
    bound_function = certificate
    if bound_kind == 'compound':
        from .quality_compound_bound import certificate as bound_function
    began = time.perf_counter()
    output = Path(output);output.mkdir(parents=True,exist_ok=False)
    index = json.loads(Path(index_path).read_text())
    expected = json.loads(Path(summary_path).read_text())
    rows, sources = [], {str(index_path):sha(index_path), str(summary_path):sha(summary_path)}
    for cohort, directory in index.items():
        path = Path(directory)/'rows.jsonl'
        sources[str(path.relative_to(ROOT))] = sha(path)
        for line in path.read_text().splitlines():
            row = json.loads(line);row['cohort']=cohort;rows.append(row)
    expected_by_key = {(g['cohort'],g['method_id'],config_key(g['config'])):g for g in expected}
    grouped = defaultdict(list)
    for row in rows:
        grouped[row['cohort'],row['method_id'],config_key(row['config'])].append(row)
    if set(grouped) != set(expected_by_key):
        raise ValueError('Cohort/method/context set differs from frozen report')
    for key, members in grouped.items():
        g = expected_by_key[key]
        if len(members) != g['summary']['expected_rows'] or g['summary']['invalid']:
            raise ValueError('Incomplete or invalid frozen group')
    unique = {(config_key(r['config']),r['seed']) for r in rows}
    bounds = {}
    with (output/'necessary-bounds.jsonl').open('x') as handle:
        for config, seed in sorted(unique):
            instance = build(**json.loads(config),seed=seed)
            bound = bound_function(instance)
            bounds[config,seed] = bound
            handle.write(json.dumps(dict(config=json.loads(config),**bound))+'\n')
    groups = summarize(rows,bounds)
    for group in groups:
        original = expected_by_key[group['cohort'],group['method_id'],config_key(group['config'])]
        if group['tapes'] != original['summary']['unique_environment_tapes'] or group['actors_per_tape'] != original['summary']['actor_replicas']:
            raise ValueError('Tape/actor coverage differs from frozen group')
        if abs(group['mean_missing']-original['summary']['metrics']['unfulfilled']['mean']) > 1e-12:
            raise ValueError('Weighted result differs from original frozen summary')
    frontier = json.loads((ROOT/'output/stage2-search/final-complete-report/preselected-frontier.json').read_text())
    selected_keys = {(g['cohort'],g['method_id'],config_key(g['config'])) for g in frontier}
    report = dict(schema='stage2-realized-primary-gap-audit.v1', valid=True,
        role='Posthoc audit of unchanged frozen outcomes; no policy selection or new performance samples',
        rows=len(rows), bound_kind=bound_kind, groups=groups, preselected_frontier=[g for g in groups if (g['cohort'],g['method_id'],config_key(g['config'])) in selected_keys],
        distinct_numerical_instances=len(unique), sources=sources,
        necessary_bounds_sha256=sha(output/'necessary-bounds.jsonl'),
        source_sha256={n:sha(ROOT/n) for n in ('stage2/quality_gap_audit.py','stage2/quality_material_bound.py','stage2/quality_compound_bound.py','stage2/engine.py','stage2/spec.py','stage2/check.py')},
        factory_runs=0, solver_calls=0, final_policies_changed=False,
        interpretation=[
            'Every interval concerns realized-tape missing-order optimum only. Deadline debt/cost optimality is unknown.',
            'The upper bound is the best valid retained execution on the identical tape, including different actors/methods; hindsight selection is an offline comparator, not a deployable controller.',
            'Mean excess interval averages per-realization gaps with original probability weights; it is not regret against an optimal nonanticipating stochastic policy.',
            'Attainment rates describe this fixed final sample; no new confidence interval or generalization guarantee is inferred.',
            '23552 executions rely on original anchored physical/identity checks; this audit rebuilds numerical instances/certificates, not all original traces.'],
        wall_seconds=time.perf_counter()-began)
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    for name in report['source_sha256']:
        dest=output/'source_snapshot'/name;dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes((ROOT/name).read_bytes())
    lines=['# Realized primary optimality audit', '',
        'Posthoc certificates for unchanged frozen outcomes; missing-order objective only. These are empirical weighted values, not population guarantees.', '',
        '| Initial orders | Calendar hours | Mean missing | Mean excess above realized optimum, certified interval | Primary optimum certified |',
        '|---:|---:|---:|---:|---:|']
    for g in sorted(report['preselected_frontier'],key=lambda g:g['config']['orders']):
        a,b=g['mean_excess_missing_interval']
        lines.append(f"| {g['config']['orders']} | {g['config']['horizon']/60:g} | {g['mean_missing']:.5f} | [{a:.5f}, {b:.5f}] | {100*g['probability_primary_optimum_certified']:.2f}% |")
    lines.extend(['',*report['interpretation']])
    (output/'table.md').write_text('\n'.join(lines)+'\n')
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--index',type=Path,default=ROOT/'output/stage2-search/final-complete-index.json')
    parser.add_argument('--summaries',type=Path,default=ROOT/'output/stage2-search/final-complete-report/all-groups.json')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--bound-kind',choices=('max_step','compound'),default='max_step')
    args=parser.parse_args()
    report=execute(args.index,args.summaries,args.output,args.bound_kind)
    print(json.dumps({k:report[k] for k in ('valid','rows','distinct_numerical_instances','wall_seconds')}))


if __name__=='__main__':
    main()
