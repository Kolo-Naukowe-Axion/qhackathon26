"""Independent rational point/tail reconstruction and primary bootstrap replay.

Reads literal completed rows; does not import the production statistics helpers
and never executes a factory or selects a policy.
"""
from collections import defaultdict
from fractions import Fraction as Q
import hashlib
import json
import math
from pathlib import Path
import random
import time

ROOT = Path(__file__).resolve().parent
METRICS = dict(missing='unfulfilled_orders', deadline_debt='terminal_deadline_debt_ticks',
               delivered_tardiness='tardiness_ticks', total_cost='total_cost', carbon_kg='carbon_kg')


def read(path): return json.loads(Path(path).read_text())
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def key(config): return json.dumps(config, sort_keys=True)
def near(a, b): assert math.isclose(float(a), b, rel_tol=1e-9, abs_tol=1e-7), (float(a), b)
def number(value): return Q(int(value)) if type(value) is bool else Q(str(value))


def tail(atoms):
    remaining = Q(1, 10); total = Q(0)
    for value, mass in sorted(atoms, reverse=True):
        take = min(mass, remaining); total += take * value; remaining -= take
        if not remaining: break
    assert remaining == 0
    return total * 10


def audit():
    started = time.perf_counter(); index = ROOT.parent / 'final-complete-index.json'
    report_path = ROOT.parent / 'final-complete-report/report.json'; report = read(report_path)
    assert report['cohort_scope'] == 'complete' and report['missing_cohorts'] == []
    assert report['executions'] == 23552 and report['groups'] == 74 and report['invalid_executions'] == 0
    assert report['expected_comparison_count'] == len(report['comparisons']) == 41
    groups = defaultdict(list); protocols = {}; input_hashes = {}
    for cohort, folder in read(index).items():
        folder = Path(folder); manifest = read(folder/'manifest.json'); protocol = manifest['protocol']['payload']
        protocols[cohort] = protocol
        assert report['protocol_sha256'] == protocol['protocol_sha256']
        input_hashes[cohort] = {name: sha(folder/name) for name in ('manifest.json', 'rows.jsonl', 'evaluation.json')}
        for line in (folder/'rows.jsonl').read_text().splitlines():
            row = json.loads(line); assert row['valid']
            groups[cohort, row['method_id'], key(row['config'])].append(row)
    assert len(groups) == 74
    cache = {}
    def quantities(cohort, method, config, metric):
        identity = (cohort, method, key(config), metric)
        if identity in cache: return cache[identity]
        rows = groups[cohort, method, key(config)]; by_seed = defaultdict(list)
        for row in rows: by_seed[row['seed']].append(row)
        env = []; joint = []; weights = []; strata = []; seeds = []
        for leaf in protocols[cohort]['leaves']:
            stratum = []; weight = Q(*leaf['probability']) / len(leaf['seeds'])
            for seed in leaf['seeds']:
                values = [number(row['metrics']['all_orders_fulfilled']) if metric == 'probability'
                          else number(row['checker_metrics'][METRICS[metric]]) for row in by_seed[seed]]
                value = sum(values) / len(values)
                stratum.append(len(env)); seeds.append(seed); env.append(value); weights.append(weight)
                joint.extend((v, weight/len(values)) for v in values)
            strata.append(stratum)
        assert sum(weights) == 1 and len(env) == 256
        answer = dict(mean=sum(v*w for v,w in zip(env,weights)),
                      cvar=tail(list(zip(env,weights))), joint_cvar=tail(joint),
                      env=env, weights=weights, strata=strata, seeds=seeds)
        cache[identity] = answer; return answer
    all_groups = read(report_path.parent/'all-groups.json')
    for group in all_groups:
        summary = group['summary']; context = group['config']; cohort = group['cohort']; method = group['method_id']
        for label, metric in (('unfulfilled','missing'),('total_tardiness_ticks','deadline_debt'),('total_cost','total_cost'),('carbon_kg','carbon_kg')):
            exact = quantities(cohort,method,context,metric); actual = summary['metrics'][label]
            near(exact['mean'],actual['mean']); near(exact['cvar'],actual['actor_mean_environment_cvar90'])
            near(exact['joint_cvar'],actual['joint_actor_environment_cvar90'])
        near(quantities(cohort,method,context,'probability')['mean'],summary['probability_all_orders_fulfilled'])
    primary = []; comparisons = []
    for pair in report['comparisons']:
        path = report_path.parent / pair['path']; result = read(path)
        for metric in METRICS:
            left = quantities(pair['left'],pair['left_method'],pair['config'],metric)
            right = quantities(pair['right'],pair['right_method'],pair['config'],metric)
            actual = result['metrics'][metric]
            assert left['seeds'] == right['seeds'] and left['weights'] == right['weights']
            for field,value in (('left_mean',left['mean']),('right_mean',right['mean']),
                                ('mean_difference',right['mean']-left['mean']),
                                ('left_cvar90',left['cvar']),('right_cvar90',right['cvar']),
                                ('left_joint_actor_environment_cvar90',left['joint_cvar']),
                                ('right_joint_actor_environment_cvar90',right['joint_cvar'])): near(value,actual[field])
        if pair['primary_quantum']:
            actual = result['predeclared_primary_missing_interval']
            assert actual['family_size'] == 2 and actual['individual_nominal_coverage'] == .975
            assert actual['bootstrap_replicates'] == 2000 and actual['bootstrap_seed'] == 60819
            left=quantities(pair['left'],pair['left_method'],pair['config'],'missing')
            right=quantities(pair['right'],pair['right_method'],pair['config'],'missing')
            # Literal protocol binary64 weights reproduce the declared runtime;
            # exact rational weights above independently verify point estimates.
            weights=[leaf['per_tape_weight'] for leaf in protocols[pair['left']]['leaves'] for _ in leaf['seeds']]
            diff=[float(b)-float(a) for a,b in zip(left['env'],right['env'])]
            rng=random.Random(60819); samples=[]
            for _ in range(2000):
                chosen=[rng.choice(indices) for indices in left['strata'] for _ in indices]
                samples.append(sum(diff[i]*weights[i] for i in chosen)/sum(weights[i] for i in chosen))
            samples.sort(); expected=[samples[math.floor(.0125*1999)],samples[math.ceil(.9875*1999)]]
            for a,b in zip(expected,actual['percentile_interval']):near(a,b)
            near(right['mean']-left['mean'],actual['mean_difference'])
            primary.append(dict(id=pair['id'],mean_difference=float(right['mean']-left['mean']),
                                interval=expected,zero_inside=expected[0]<=0<=expected[1]))
        comparisons.append(dict(id=pair['id'],sha256=sha(path)))
    assert len(primary) == 2
    selected = []
    expected_ids={10:'selected-cheap-10',11:'selected-cheap-11',12:'static-grid-12',13:'selected-cheap-13',
                  14:'selected-cheap-14',16:'cem6-2026-16',24:'cem6-2026-24',32:'selected-stretch-32'}
    assert len(report['preselected_frontier']) == 8
    for group in report['preselected_frontier']:
        n=group['config']['orders']; assert group['method_id']==expected_ids[n]
        probability=quantities(group['cohort'],group['method_id'],group['config'],'probability')
        actual=group['exploratory_frontier_intervals']['all_orders_fulfilled_probability'];near(probability['mean'],actual['mean'])
        if all(v==0 for v in probability['env']) or all(v==1 for v in probability['env']):
            assert actual['percentile_interval_95'] is None
            wmax=max(probability['weights']); edge=.05**float(wmax)
            expected=[0.,1-edge] if probability['env'][0]==0 else [edge,1.]
            for a,b in zip(expected,actual['boundary_probability_bound']['interval']):near(a,b)
        selected.append(dict(orders=n,method_id=group['method_id'],mean_missing=float(quantities(group['cohort'],group['method_id'],group['config'],'missing')['mean']),all_fulfilled_probability=float(probability['mean'])))
    for filename,digest in report['source_hashes'].items():assert sha(Path('stage2')/filename)==digest
    return dict(schema='stage2-independent-complete-final-statistics-audit.v1',valid=True,
                groups=74,comparisons=41,rows=23552,primary_intervals=primary,preselected_frontier=selected,
                report_sha256=sha(report_path),all_groups_sha256=sha(report_path.parent/'all-groups.json'),
                comparison_hashes=comparisons,input_hashes=input_hashes,source_sha256=sha(__file__),
                factory_simulations=0,wall_seconds=time.perf_counter()-started,
                scope='Independent exact-rational weighted means and CVaR90 for all74 groups/all41 five-metric contrast point estimates; independent2000-draw paired-cluster primary interval reproduction; fixed incumbent IDs and boundary probability checks. Other bootstrap intervals not recomputed; no quantum advantage, population guarantee or secondary optimality inference.')


if __name__=='__main__':
    result=audit()
    with (ROOT/'complete-statistics-audit.json').open('x') as stream:stream.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('comparison_hashes','input_hashes')},indent=2))
