"""Predeclared stratified tapes and paired, environment-clustered statistics.

Scenario selection reads only exogenous branch hashes, never solver outcomes.
This module has no role in a controller's observation or action generation.
"""
from __future__ import annotations

from collections import defaultdict
from fractions import Fraction
import hashlib
import itertools
import json
import math
import random
from statistics import mean


def branch(seed,stages):
    ids=[]
    for index,stage in enumerate(stages):
        value=int.from_bytes(hashlib.sha256(f'{seed}:stage:{index}'.encode()).digest()[:8],'big')
        draw=Fraction(value,2**64);cumulative=Fraction(0)
        for outcome in stage['outcomes']:
            cumulative+=Fraction(*outcome['probability'])
            if draw<cumulative:ids.append(outcome['id']);break
        else:raise ValueError('Outcome probabilities must sum to one')
    return tuple(ids)


def stratified_protocol(stages,per_leaf=32,start=10000):
    if per_leaf<1 or start<10000:raise ValueError('Final tapes start at 10000 and need positive allocation')
    leaves={}
    for outcomes in itertools.product(*(stage['outcomes'] for stage in stages)):
        ids=tuple(outcome['id'] for outcome in outcomes);probability=Fraction(1)
        for outcome in outcomes:probability*=Fraction(*outcome['probability'])
        if probability>0:leaves[ids]=dict(probability=probability,seeds=[])
    candidate=start
    while any(len(leaf['seeds'])<per_leaf for leaf in leaves.values()):
        ids=branch(candidate,stages)
        if len(leaves[ids]['seeds'])<per_leaf:leaves[ids]['seeds'].append(candidate)
        candidate+=1
        if candidate-start>per_leaf*len(leaves)*10000:raise RuntimeError('Stratification failed')
    rows=[]
    for ids,leaf in sorted(leaves.items()):
        p=leaf['probability']
        rows.append(dict(outcomes=list(ids),probability=[p.numerator,p.denominator],
            seeds=leaf['seeds'],per_tape_weight=float(p/per_leaf)))
    protocol=dict(schema='stage2-stratified-final-protocol.v1',seed_role='FINAL; no training or policy selection',
        selection='First increasing seeds per exogenous leaf; solver outcomes never inspected',
        quality_randomness='Keyed per-unit hashes on the same seeds; conditional pseudorandom tapes',
        per_leaf=per_leaf,start_seed=start,candidates_examined=candidate-start,
        total_tapes=per_leaf*len(leaves),leaves=rows,
        uncertainty_scope='Eight declared exogenous leaves plus seeded endogenous quality, not unmodeled factory uncertainty')
    protocol['protocol_sha256']=hashlib.sha256(json.dumps(protocol,sort_keys=True).encode()).hexdigest()
    return protocol


def weighted_mean(values,weights):
    if len(values)!=len(weights) or not values or min(weights)<0 or sum(weights)<=0:
        raise ValueError('Matching nonnegative positive-total weighted values required')
    return sum(x*w for x,w in zip(values,weights))/sum(weights)


def weighted_cvar(values,weights,alpha=.9):
    if not 0<=alpha<1:raise ValueError('CVaR alpha in [0,1) required')
    total=sum(weights)
    if len(values)!=len(weights) or not values or min(weights)<0 or total<=0:
        raise ValueError('Matching nonnegative positive-total weighted values required')
    tail=(1-alpha)*total;remaining=tail;value=0.
    for x,w in sorted(zip(values,weights),reverse=True):
        taken=min(w,remaining);value+=taken*x;remaining-=taken
        if remaining<=1e-14*total:break
    return value/tail


def clustered_rows(rows,protocol,metric):
    """Average actor replicas *within* a factory, never count them as new tapes."""
    grouped=defaultdict(list)
    for row in rows:grouped[row['seed']].append(row)
    result=[]
    expected={seed for leaf in protocol['leaves'] for seed in leaf['seeds']}
    if set(grouped)!=expected:raise ValueError('Missing or extra factory tapes relative to fixed protocol')
    actor_sets={tuple(sorted(r.get('policy_seed',0) for r in rs)) for rs in grouped.values()}
    if len(actor_sets)!=1:raise ValueError('Actor replication must use the same seed set on every factory tape')
    for index,leaf in enumerate(protocol['leaves']):
        for seed in leaf['seeds']:
            rs=grouped[seed]
            actors=[r.get('policy_seed',0) for r in rs]
            if len(set(actors))!=len(actors):raise ValueError('Duplicate actor/tape pair')
            if any(not r['valid'] for r in rs):raise ValueError('Invalid physical trace cannot enter performance comparison')
            result.append(dict(seed=seed,leaf=index,weight=leaf['per_tape_weight'],
                value=mean(metric(r) for r in rs),actor_replicas=len(rs)))
    return result


def paired_report(left,right,protocol,metric,bootstrap=2000,seed=60819):
    """B−A differences, paired by factory; resample within exogenous strata."""
    a=clustered_rows(left,protocol,metric);b=clustered_rows(right,protocol,metric)
    if [(r['seed'],r['weight']) for r in a]!=[(r['seed'],r['weight']) for r in b]:raise ValueError('Unpaired tapes')
    weights=[r['weight'] for r in a];x=[r['value'] for r in a];y=[r['value'] for r in b]
    groups=defaultdict(list)
    for i,row in enumerate(a):groups[row['leaf']].append(i)
    rng=random.Random(seed);means=[];tails=[]
    for _ in range(bootstrap):
        chosen=[rng.choice(indices) for indices in groups.values() for _ in indices]
        w=[weights[i] for i in chosen];xx=[x[i] for i in chosen];yy=[y[i] for i in chosen]
        means.append(weighted_mean(yy,w)-weighted_mean(xx,w))
        tails.append(weighted_cvar(yy,w)-weighted_cvar(xx,w))
    def interval(values):
        if not values:return None
        values=sorted(values)
        return [values[int(.025*(len(values)-1))],values[int(.975*(len(values)-1))]]
    return dict(schema='stage2-paired-stratified-comparison.v1',direction='right minus left; negative favors right for losses',
        environment_tapes=len(a),actor_replicas_left=sum(r['actor_replicas'] for r in a),
        actor_replicas_right=sum(r['actor_replicas'] for r in b),
        left_mean=weighted_mean(x,weights),right_mean=weighted_mean(y,weights),
        mean_difference=weighted_mean([v-u for u,v in zip(x,y)],weights),
        mean_difference_percentile_bootstrap_95=interval(means),
        left_cvar90=weighted_cvar(x,weights),right_cvar90=weighted_cvar(y,weights),
        cvar90_difference_percentile_bootstrap_95=interval(tails),
        bootstrap_replicates=bootstrap,bootstrap_seed=seed,
        risk_scope='CVaR across exogenous/quality tapes of actor-averaged loss; actor randomness not new factories',
        limitation='Empirical conditional pseudorandom-tape estimate; no global-optimality or all-future-scenario proof')


if __name__=='__main__':
    import argparse
    from pathlib import Path
    from .spec import build
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--per-leaf',type=int,default=32)
    a=p.parse_args();protocol=stratified_protocol(build()['uncertainty_stages'],a.per_leaf)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    if a.output.exists():raise ValueError('Preserve existing protocol')
    a.output.write_text(json.dumps(protocol,indent=2)+'\n')
    print(json.dumps(dict(tapes=protocol['total_tapes'],hash=protocol['protocol_sha256'])))
