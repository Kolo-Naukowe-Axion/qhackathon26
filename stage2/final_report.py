"""Audited aggregation of completed frozen final evaluations; no policy changes.

Input is a JSON mapping from cohort label to a downloaded evidence directory.
All groups must be complete and valid; failed groups never become valid-only
performance tables. Selection remains the pre-outcome frozen incumbent map.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import json
from pathlib import Path
import random
import time

from .compare_evaluations import load_evidence,select_rows,compare_payloads,file_hash
from .primary_intervals import mean_interval
from .statistics import clustered_rows,weighted_mean
from .final_eval import summarize

EXPECTED_COHORTS={'strong-cheap','quantum-deterministic','quantum-stochastic','frontier','legacy',
                  'mpc-12','mpc-13','mpc-14','mpc-16','mpc-24'}


def config(n):return dict(orders=n,horizon=14400 if n==32 else 5760,profile='full')


def contrasts():
    pairs=[]
    def add(label,a,am,b,bm,n,primary=False):pairs.append(dict(id=label,left=a,left_method=am,right=b,right_method=bm,config=config(n),primary_quantum=primary))
    chosen={12:'static-grid-12',16:'cem6-2026-16',24:'cem6-2026-24'}
    for n in (12,16,24):
        for other in ('sa','uniform'):
            add(f'quantum-qaoa-vs-{other}-{n}','quantum-stochastic',f'no-batch-{other}-{n}','quantum-stochastic',f'no-batch-qaoa-{n}',n,n==12)
        add(f'selected-vs-original-{n}','strong-cheap',f'original-strong-{n}','strong-cheap',chosen[n],n)
        if n!=12:add(f'cem6-vs-broad-static-{n}','strong-cheap',f'static-grid-{n}','strong-cheap',chosen[n],n)
        for legacy in ('legacy-warm-ppo-2026','legacy-warm-ppo-2027','legacy-warm-cem-2026','legacy-warm-bandit-2026','legacy-threshold-cem-2026','legacy-threshold-cem-2027'):
            add(f'{legacy}-vs-legacy-teacher-{n}','legacy','legacy-routing-teacher','legacy',legacy,n)
    for n,count in ((12,4),(13,2),(14,2),(16,2),(24,4)):
        left='strong-cheap' if n in (12,16,24) else 'frontier';method=f'original-strong-{n}' if left=='strong-cheap' else f'selected-cheap-{n}'
        add(f'mpc-vs-exact-static-{n}',left,method,f'mpc-{n}',f'mpc-{count}future-{n}',n)
        if n in (12,16,24):add(f'mpc-vs-selected-cheap-{n}','strong-cheap',chosen[n],f'mpc-{n}',f'mpc-{count}future-{n}',n)
    for n in (10,11,13,14):add(f'selected-vs-original-{n}','frontier',f'original-prior-{n}','frontier',f'selected-cheap-{n}',n)
    return pairs


def group_cost(rows,protocol):
    timings={}
    for key in ('wall_seconds','cpu_seconds','simulation_wall_seconds','checker_wall_seconds','planning_wall_seconds','controller_inference_wall_seconds','controller_inference_cpu_seconds'):
        grouped=clustered_rows(rows,protocol,lambda r,k=key:r.get(k,0.))
        timings[key]=dict(weighted_actor_mean_environment=weighted_mean([x['value'] for x in grouped],[x['weight'] for x in grouped]),literal_sum_all_executions=sum(r.get(key,0.) for r in rows))
    counters=defaultdict(int);maxima=defaultdict(int)
    for row in rows:
        for key,value in row['qubo_telemetry'].items():
            if type(value) not in (int,float):continue
            if key.startswith('max_'):maxima[key]=max(maxima[key],value)
            else:counters[key]+=value
    return dict(timings=timings,qubo_literal_execution_totals=dict(counters),qubo_maxima=dict(maxima),
        scope='Literal completed rollout costs plus probability-weighted actor means. Planning and local optimization are nested inside simulation; do not sum them twice. Allocated cluster time and training costs remain in the compute ledger. Cross-host runtime is not a speedup claim.')


def mean_uncertainty(rows,protocol,metric,bootstrap=2000,seed=60819,probability=False):
    """Exploratory single-policy interval, with whole environment clusters."""
    clustered=clustered_rows(rows,protocol,metric);strata=defaultdict(list)
    for i,row in enumerate(clustered):strata[row['leaf']].append(i)
    rng=random.Random(seed);samples=[]
    for _ in range(bootstrap):
        indices=[rng.choice(group) for group in strata.values() for _ in group]
        samples.append(weighted_mean([clustered[i]['value'] for i in indices],[clustered[i]['weight'] for i in indices]))
    samples.sort()
    interval=None if not samples else [samples[int(.025*(len(samples)-1))],samples[int(.975*(len(samples)-1))]]
    boundary=None
    if probability and (all(r['value']==0 for r in clustered) or all(r['value']==1 for r in clustered)):
        maximum_weight=max(r['weight'] for r in clustered)/sum(r['weight'] for r in clustered);tail=.05**maximum_weight
        boundary=dict(one_sided_nominal_coverage=.95,interval=[0.,1-tail] if clustered[0]['value']==0 else [tail,1.],
            maximum_environment_weight=maximum_weight,
            scope='Conservative boundary-only bound assuming independent bounded environment outcomes; Pr(all zero) <= (1-mean)^(1/max_weight), with the complementary all-one result. Pseudorandom-tape assumptions remain explicit.')
        interval=None
    return dict(mean=weighted_mean([r['value'] for r in clustered],[r['weight'] for r in clustered]),
        percentile_interval_95=interval,bootstrap_replicates=bootstrap,bootstrap_seed=seed,
        boundary_probability_bound=boundary,
        scope='Pointwise exploratory; whole environment clusters resampled within leaves, actors nested; conditional pseudorandom-tape uncertainty, not a robust all-future guarantee')


def report(index_path,output,*,bootstrap=2000,include_comparisons=True,allow_partial=False):
    source_names=('final_report.py','final_eval.py','compare_evaluations.py','statistics.py','primary_intervals.py')
    sources={name:file_hash(Path(__file__).with_name(name)) for name in source_names}
    began=time.perf_counter();paths=json.loads(Path(index_path).read_text());output=Path(output).resolve();output.mkdir(parents=True,exist_ok=False)
    missing=sorted(EXPECTED_COHORTS-set(paths))
    if missing and not allow_partial:raise ValueError('Missing final cohorts: '+','.join(missing))
    if set(paths)-EXPECTED_COHORTS:raise ValueError('Unknown final cohort label')
    evidence={};groups=[];protocol_sha=None
    for label,path in paths.items():
        m,e,reference=load_evidence(path)
        if m['evaluation_role']!='final':raise ValueError('Final evidence only')
        current=m['protocol']['payload']['protocol_sha256']
        if protocol_sha is not None and current!=protocol_sha:raise ValueError('Cohorts use different final protocols')
        protocol_sha=current;evidence[label]=(m,e,reference)
        # Cached summaries are not an authority: enumerate the frozen manifest
        # and validate every declared group, then reconstruct weighted metrics.
        for method in m['methods']:
            for context in method.get('configs',m['configs']):
                select_rows(m,e,method['id'],context)
        for summary in summarize(e['rows'],m):
            rows=select_rows(m,e,summary['method_id'],summary['config'])
            groups.append(dict(cohort=label,method_id=summary['method_id'],config=summary['config'],summary=summary,
                cost=group_cost(rows,m['protocol']['payload']),manifest_sha256=m['manifest_sha256'],source_evidence=reference))
    (output/'all-groups.json').write_text(json.dumps(groups,indent=2)+'\n')
    selected=[]
    for n in (10,11,12,13,14,16,24,32):
        label='strong-cheap' if n in (12,16,24) else 'frontier'
        method={12:'static-grid-12',16:'cem6-2026-16',24:'cem6-2026-24',32:'selected-stretch-32'}.get(n,f'selected-cheap-{n}')
        if label in evidence:
            group=next(g for g in groups if g['cohort']==label and g['method_id']==method and g['config']==config(n))
            m,e,_=evidence[label];rows=select_rows(m,e,method,config(n))
            group['exploratory_frontier_intervals']={
                'all_orders_fulfilled_probability':mean_uncertainty(rows,m['protocol']['payload'],lambda r:float(r['metrics']['all_orders_fulfilled']),bootstrap,probability=True),
                'mean_missing':mean_uncertainty(rows,m['protocol']['payload'],lambda r:r['checker_metrics']['unfulfilled_orders'],bootstrap)}
            selected.append(group)
    (output/'preselected-frontier.json').write_text(json.dumps(selected,indent=2)+'\n')
    results=[]
    if include_comparisons:
        directory=output/'comparisons';directory.mkdir()
        for pair in contrasts():
            if pair['left'] not in evidence or pair['right'] not in evidence:continue
            lm,le,lr=evidence[pair['left']];rm,re,rr=evidence[pair['right']]
            answer=compare_payloads(lm,le,pair['left_method'],rm,re,pair['right_method'],pair['config'],bootstrap=bootstrap)
            answer['source_evidence']=dict(left=lr,right=rr)
            if pair['primary_quantum']:
                left=select_rows(lm,le,pair['left_method'],pair['config']);right=select_rows(rm,re,pair['right_method'],pair['config'])
                answer['predeclared_primary_missing_interval']=mean_interval(left,right,lm['protocol']['payload'],lambda r:r['checker_metrics']['unfulfilled_orders'],bootstrap=bootstrap,family_size=2)
            (directory/(pair['id']+'.json')).write_text(json.dumps(answer,indent=2)+'\n')
            results.append(dict(**pair,path='comparisons/'+pair['id']+'.json',missing=answer['metrics']['missing'],deadline_debt=answer['metrics']['deadline_debt'],primary_interval=answer.get('predeclared_primary_missing_interval')))
            print('Compared',pair['id'],flush=True)
    if any(file_hash(Path(__file__).with_name(name))!=sha for name,sha in sources.items()):
        raise ValueError('Reporting/statistics source changed during aggregation; preserve partial output as failed')
    result=dict(schema='stage2-final-evidence-report.v1',cohort_scope='partial' if missing else 'complete',missing_cohorts=missing,expected_comparison_count=len(contrasts()),comparisons_computed=include_comparisons,protocol_sha256=protocol_sha,inputs=paths,groups=len(groups),executions=sum(e['actual_rows'] for _,e,_ in evidence.values()),invalid_executions=sum(e['missing_or_invalid'] for _,e,_ in evidence.values()),preselected_frontier=selected,comparisons=results,source_hashes=sources,wall_seconds=time.perf_counter()-began,
        interpretation='No post-final policy switching. All contrasts other than the two named n12 quantum missing-order means are pointwise exploratory. Quantum is CPU simulation with measured classical fallback; primary global gap requires separate offline certificates; secondary gap unknown.')
    (output/'report.json').write_text(json.dumps(result,indent=2)+'\n');return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--index',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--bootstrap',type=int,default=2000);p.add_argument('--no-comparisons',action='store_true');p.add_argument('--allow-partial',action='store_true');a=p.parse_args()
    r=report(a.index,a.output,bootstrap=a.bootstrap,include_comparisons=not a.no_comparisons,allow_partial=a.allow_partial);print(json.dumps({k:r[k] for k in ('cohort_scope','groups','executions','invalid_executions','wall_seconds')}))


if __name__=='__main__':main()
