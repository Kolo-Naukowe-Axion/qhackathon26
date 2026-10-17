"""Causal scenario rollout control over the frozen physical factory.

Plans use an independently seeded future, never the actual factory random tape.
The continuation loop is mechanically derived from Factory.run: only its initial
tick and the already-processed boundary change. Physical operations stay in the
original engine; independently checked final traces are the acceptance test.
"""
from __future__ import annotations

import ast
from copy import deepcopy
import hashlib
import inspect
import json
from pathlib import Path
import textwrap
import time

from .engine import Factory


def _continuation():
    tree=ast.parse(textwrap.dedent(inspect.getsource(Factory.run)))
    function=tree.body[0]
    loop=function.body[0]
    if not isinstance(loop,ast.For) or ast.unparse(loop.iter)!="range(self.i['horizon_ticks'] + 1)":
        raise RuntimeError("Factory loop changed; independently audit continuation before reuse")
    controller_index=next(i for i,node in enumerate(loop.body)
        if isinstance(node,ast.If) and ast.unparse(node.test).startswith('self.controller and'))
    # self.t=t remains unconditional. Completions/revelations at the initial
    # decision boundary have already happened in the actual factory.
    prefix=loop.body[1:controller_index-1]
    horizon_guard=loop.body[controller_index-1]
    if ast.unparse(horizon_guard.test)!="t == self.i['horizon_ticks']":
        raise RuntimeError("Unexpected boundary guard")
    loop.iter=ast.parse("range(self._resume_tick,self.i['horizon_ticks']+1)",mode='eval').body
    condition=ast.parse("not(t==self._resume_tick and self._boundary_processed)",mode='eval').body
    loop.body=[loop.body[0],ast.If(test=condition,body=prefix,orelse=[]),horizon_guard]+loop.body[controller_index:]
    function.name='_resume';ast.fix_missing_locations(tree)
    namespace=dict(Factory.run.__globals__)
    exec(compile(tree,'<audited-factory-continuation>','exec'),namespace)
    return namespace['_resume'],ast.unparse(tree)


resume,CONTINUATION_SOURCE=_continuation()
CONTINUATION_SHA256=hashlib.sha256(CONTINUATION_SOURCE.encode()).hexdigest()


def continuation(factory,tick,weights,planning_seed,boundary_processed=True):
    """Create a simulation with a fresh future before executing any decision."""
    saved=factory.controller;factory.controller=None
    try: simulated=deepcopy(factory)
    finally: factory.controller=saved
    simulated.controller=None
    simulated.i['seed']=int(planning_seed)
    simulated.trace['instance']=simulated.i
    simulated.weights.update(weights)
    simulated._resume_tick=tick
    simulated._boundary_processed=boundary_processed
    # Neither a run ID nor past audit uniforms can influence this engine's
    # physical actions. Clear identifiers anyway to make the boundary explicit.
    simulated.trace['run_id']='independent-planning-future'
    return simulated


def candidates():
    result=[]
    for wip in (3,4,6,8):
        for mode in ('eco','standard'):
            for family in (0.,24.):
                result.append(dict(wip_limit=wip,mode=mode,family=family,
                    due=.25 if family else 1.,remaining=-4.,setup=10. if family else 3.,
                    lease_calibration=True,selector='priority'))
    return result


def objective(metrics,horizon):
    """Bounded secondary terms retain order-count priority for each scenario."""
    return (metrics['orders']-metrics['shipped']+
        .2*min(1.,metrics['total_tardiness_ticks']/max(1,metrics['orders']*horizon))+
        .01*metrics['total_cost']/(1000+metrics['total_cost']))


class RolloutController:
    def __init__(self,factory,actions=None,scenarios=4,interval=720,seed=27491):
        if scenarios<1 or interval<1:raise ValueError('Positive scenarios and interval required')
        self.factory=factory;self.actions=actions or candidates()
        self.scenarios=scenarios;self.interval=interval;self.seed=seed
        self.next_tick=0;self.history=[]

    def __call__(self,observation):
        tick=observation['tick']
        if tick<self.next_tick:return dict(weights={},action_id='retain-rollout-policy')
        self.next_tick=tick+self.interval
        began=time.perf_counter()
        # Same independent scenario futures for every candidate at this tick.
        seeds=[int.from_bytes(hashlib.sha256(f'{self.seed}:{tick}:{k}'.encode()).digest()[:8],'big')
               for k in range(self.scenarios)]
        options=[dict(self.factory.weights)]+self.actions
        unique=[];keys=set()
        for option in options:
            key=json.dumps(option,sort_keys=True)
            if key not in keys:keys.add(key);unique.append(option)
        rows=[]
        for action,weights in enumerate(unique):
            scores=[];metrics=[]
            for seed in seeds:
                future=continuation(self.factory,tick,weights,seed)
                trace=resume(future)
                scores.append(objective(trace['metrics'],future.i['horizon_ticks']))
                metrics.append({key:trace['metrics'][key] for key in
                    ('orders','shipped','total_tardiness_ticks','total_cost','terminal_soc_satisfied')})
            rows.append(dict(action=action,weights=weights,mean_loss=sum(scores)/len(scores),
                scenario_losses=scores,scenario_metrics=metrics))
        winner=min(rows,key=lambda row:(row['mean_loss'],row['action']))
        evidence=dict(tick=tick,scenario_seeds=seeds,planning_seed_role='independent future; never actual environment seed',
            candidates=rows,selected=winner['action'],wall_seconds=time.perf_counter()-began,
            continuation_sha256=CONTINUATION_SHA256)
        self.history.append(evidence)
        return dict(weights=winner['weights'],action_id=f'rollout-{winner["action"]}')


def run(instance,weights=None,actions=None,scenarios=4,interval=720,seed=27491):
    factory=Factory(instance,weights)
    controller=RolloutController(factory,actions,scenarios,interval,seed)
    factory.controller=controller
    trace=factory.run()
    trace['planning']=dict(method='independently-resampled-scenario-rollout',decisions=controller.history,
        wall_seconds=sum(r['wall_seconds'] for r in controller.history),
        continuation_sha256=CONTINUATION_SHA256,
        disclosure='Classical lookahead, including complete simulated futures; no quantum or global optimality claim')
    return trace


if __name__=='__main__':
    import argparse
    from .spec import build
    from .check import check_trace
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--orders',type=int,default=12);p.add_argument('--horizon',type=int,default=5760)
    p.add_argument('--seed',type=int,default=0);p.add_argument('--scenarios',type=int,default=2)
    p.add_argument('--interval',type=int,default=720);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    trace=run(build(a.orders,a.horizon,a.seed),dict(wip_limit=6,mode='standard',lease_calibration=True),
        scenarios=a.scenarios,interval=a.interval)
    trace['validation']=check_trace(trace)
    (a.output/'trace.json').write_text(json.dumps(trace)+'\n')
    print(json.dumps(dict(metrics=trace['metrics'],valid=trace['validation']['valid'],planning_seconds=trace['planning']['wall_seconds'])))
