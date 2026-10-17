"""Observed conditional final summaries; no factory or policy selection.

Each cell averages actors within a tape, then the32 tapes within a declared
exogenous leaf. Exact probability reweighting recovers the overall estimates.
"""
from collections import defaultdict
from fractions import Fraction as Q
import hashlib
import json
import math
from pathlib import Path
import time

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
METRICS=dict(missing_orders='unfulfilled_orders',deadline_debt_ticks='terminal_deadline_debt_ticks',
             delivered_only_tardiness_ticks='tardiness_ticks',total_cost='total_cost',
             carbon_kg='carbon_kg',grid_kwh='grid_kwh')


def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def key(config):return json.dumps(config,sort_keys=True,separators=(',',':'))
def rational(x):return Q(int(x)) if type(x) is bool else Q(str(x))
def fraction(x):return [x.numerator,x.denominator]
def close(a,b):assert math.isclose(float(a),b,rel_tol=1e-10,abs_tol=1e-7),(float(a),b)


def actor_nested(rows,metric,expected_seeds,expected_actors):
    """Return exact tape means; reject duplicates/incomplete actor replication."""
    grouped=defaultdict(dict)
    for row in rows:
        if not row['valid']:raise ValueError('Invalid row cannot enter conditional performance')
        if row['policy_seed'] in grouped[row['seed']]:raise ValueError('Duplicate actor/tape')
        grouped[row['seed']][row['policy_seed']]=row
    if set(grouped)!=set(expected_seeds):raise ValueError('Missing/extra environment tape')
    if any(set(g)!=set(expected_actors) for g in grouped.values()):raise ValueError('Missing/extra actor replica')
    values={seed:sum(rational(metric(grouped[seed][actor])) for actor in expected_actors)/len(expected_actors)
            for seed in expected_seeds}
    return sum(values.values())/len(values),values


def reweight(means,probabilities):
    if len(means)!=len(probabilities) or sum(probabilities)!=1:raise ValueError('Complete normalized leaf probabilities required')
    return sum(value*probability for value,probability in zip(means,probabilities))


def metric_value(row,name):
    if name=='all_orders_fulfilled':
        assert row['metrics']['all_orders_fulfilled']==(row['checker_metrics']['unfulfilled_orders']==0)
        return row['metrics']['all_orders_fulfilled']
    return row['checker_metrics'][METRICS[name]]


def build():
    began=time.perf_counter();index=BASE/'final-complete-index.json';main_path=BASE/'final-complete-report/report.json'
    main=read(main_path);assert main['cohort_scope']=='complete' and main['executions']==23552 and main['invalid_executions']==0
    protocol_path=BASE/'final-frozen-bundle-v20p2/final-heldout-protocol.json';protocol=read(protocol_path)
    assert protocol['protocol_sha256']==main['protocol_sha256'] and protocol['total_tapes']==256 and len(protocol['leaves'])==8
    probabilities=[Q(*leaf['probability']) for leaf in protocol['leaves']];assert sum(probabilities)==1
    assert all(len(leaf['seeds'])==32 for leaf in protocol['leaves'])
    leaf_by_seed={seed:i for i,leaf in enumerate(protocol['leaves']) for seed in leaf['seeds']}
    metadata={};grouped=defaultdict(list);inputs={};tracked=[index,main_path,protocol_path,Path(__file__),BASE/'final-complete-report/all-groups.json',BASE/'final-independent-audit/complete-audit-seal.json']
    for label,folder in read(index).items():
        folder=Path(folder);manifest=read(folder/'manifest.json');assert manifest['protocol']['payload']==protocol
        inputs[label]=dict(directory=str(folder),files={name:sha(folder/name) for name in ('manifest.json','evaluation.json','rows.jsonl')},
                           actor_seeds=manifest['actor_seeds'],source_hashes=manifest['source_hashes'])
        tracked.extend(folder/name for name in ('manifest.json','evaluation.json','rows.jsonl'))
        metadata[label]=manifest
        for line in (folder/'rows.jsonl').read_text().splitlines():
            row=json.loads(line);assert row['valid'] and row['leaf']==leaf_by_seed[row['seed']]
            assert row['leaf_outcomes']==protocol['leaves'][row['leaf']]['outcomes']
            assert row['metrics']['orders']==row['checker_metrics']['delivered_orders']+row['checker_metrics']['unfulfilled_orders']
            grouped[label,row['method_id'],key(row['config'])].append(row)
    before={str(path):sha(path) for path in tracked}
    published={(g['cohort'],g['method_id'],key(g['config'])):g for g in read(BASE/'final-complete-report/all-groups.json')}
    assert set(grouped)==set(published) and len(grouped)==74
    groups=[];exact={};cell_count=0;names=('all_orders_fulfilled',*METRICS)
    for identity,rows in grouped.items():
        cohort,method,_=identity;actors=metadata[cohort]['actor_seeds'];cells=[];leaf_means=defaultdict(list)
        for li,leaf in enumerate(protocol['leaves']):
            batch=[row for row in rows if row['leaf']==li];values={};exact_values={}
            for name in names:
                mean,tapes=actor_nested(batch,lambda row,n=name:metric_value(row,n),leaf['seeds'],actors)
                leaf_means[name].append(mean);values[name]=float(mean);exact_values[name]=fraction(mean)
                if name=='all_orders_fulfilled':
                    boundary='all_sampled_tapes_and_actors_succeeded' if all(v==1 for v in tapes.values()) else 'no_sampled_tape_actor_succeeded' if all(v==0 for v in tapes.values()) else None
                    tape_details=[dict(seed=seed,actor_mean_all_fulfilled=float(v)) for seed,v in tapes.items()]
            demand={row['metrics']['orders'] for row in batch};assert len(demand)==1
            cells.append(dict(leaf_index=li,outcomes=leaf['outcomes'],true_probability=leaf['probability'],
                              environment_tapes=32,actor_seeds=actors,execution_rows=len(batch),realized_orders=demand.pop(),
                              conditional_actor_averaged_means=values,exact_conditional_means=exact_values,
                              observed_success_boundary=boundary,all_fulfilled_by_tape=tape_details,
                              uncertainty_intervals=None))
        overall={name:reweight(leaf_means[name],probabilities) for name in names}
        # Separately sum literal actor rows with their true environment masses.
        for name in names:
            direct=sum(rational(metric_value(row,name))*probabilities[row['leaf']]/32/len(actors) for row in rows)
            assert direct==overall[name]
        summary=published[identity]['summary']
        for own,old in (('missing_orders','unfulfilled'),('deadline_debt_ticks','total_tardiness_ticks'),('total_cost','total_cost'),('carbon_kg','carbon_kg')):
            close(overall[own],summary['metrics'][old]['mean'])
        close(overall['all_orders_fulfilled'],summary['probability_all_orders_fulfilled'])
        exact[identity]=dict(leaf_means=leaf_means,rows=rows)
        groups.append(dict(cohort=cohort,method_id=method,config=rows[0]['config'],actor_seeds=actors,
                           source_manifest_sha256=metadata[cohort]['manifest_sha256'],leaves=cells,
                           true_probability_reweighted_means={name:float(value) for name,value in overall.items()},
                           exact_reweighted_means={name:fraction(value) for name,value in overall.items()},
                           published_overall_means_recovered=True))
        cell_count+=len(cells)
    selected={(g['cohort'],g['method_id'],key(g['config'])) for g in main['preselected_frontier']}
    compact=[g for g in groups if (g['cohort'],g['method_id'],key(g['config'])) in selected or g['cohort'].startswith('mpc-')]
    assert len(compact)==13 and cell_count==592
    left=next(g for g in groups if g['method_id']=='cem6-2026-16');right=next(g for g in groups if g['method_id']=='mpc-2future-16')
    paired=[]
    for a,b in zip(left['leaves'],right['leaves']):
        assert a['outcomes']==b['outcomes']
        lrows=exact[left['cohort'],left['method_id'],key(left['config'])]['rows'];rrows=exact[right['cohort'],right['method_id'],key(right['config'])]['rows']
        lm={r['seed']:r for r in lrows if r['leaf']==a['leaf_index']};rm={r['seed']:r for r in rrows if r['leaf']==a['leaf_index']}
        assert set(lm)==set(rm) and len(lm)==32
        assert all(lm[seed]['physical_instance_sha256']==rm[seed]['physical_instance_sha256'] for seed in lm)
        paired.append(dict(leaf_index=a['leaf_index'],outcomes=a['outcomes'],environment_pairs=32,
                           mpc_minus_cem_conditional_missing=float(sum(Q(rm[s]['checker_metrics']['unfulfilled_orders']-lm[s]['checker_metrics']['unfulfilled_orders']) for s in lm)/32)))
    assert all(sha(path)==value for path,value in before.items())
    return dict(schema='stage2-observed-final-conditional-leaves.v1',groups=groups,method_context_groups=74,
                leaf_cells=592,execution_rows=23552,environment_tapes_per_leaf=32,leaves=protocol['leaves'],
                protocol_sha256=protocol['protocol_sha256'],inputs=inputs,input_hashes=before,
                compact_group_ids=[dict(cohort=g['cohort'],method_id=g['method_id'],config=g['config']) for g in compact],
                descriptive_paired_mpc16_minus_cem16=paired,all_probability_reweighting_exact=True,
                factory_simulations=0,policy_changes=0,wall_seconds=time.perf_counter()-began,
                interpretation='Observed conditional estimates on32 environment tapes perleaf, actors nested and averaged within each tape. No confidence intervals calculated: observed0/1 is not population0/1. Leaf comparisons are descriptive, not causal effects; different leaves use different quality seeds. No new primary contrasts, policy selection, independence replicas or robustness guarantee.',
                compact_groups=compact)


if __name__=='__main__':
    result=build();compact=result.pop('compact_groups')
    with (HERE/'report.json').open('x') as stream:stream.write(json.dumps(result,indent=2)+'\n')
    subset=dict(schema='stage2-observed-final-conditional-selected-and-mpc.v1',report_sha256=sha(HERE/'report.json'),
                interpretation=result['interpretation'],groups=compact,
                descriptive_paired_mpc16_minus_cem16=result['descriptive_paired_mpc16_minus_cem16'])
    with (HERE/'selected-and-mpc.json').open('x') as stream:stream.write(json.dumps(subset,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('groups','inputs','input_hashes','leaves')},indent=2))
