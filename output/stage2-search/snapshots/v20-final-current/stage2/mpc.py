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
import math
from pathlib import Path
import statistics
import textwrap
import time

from .engine import Factory

ROOT=Path(__file__).resolve().parents[1]
CORE=("stage2/engine.py","stage2/spec.py","stage2/check.py","stage2/dispatch.py",
      "stage2/qubo.py","stage2/quantum.py","instances/stage2/metaltech_pressure.json")
DEFAULT_WEIGHTS=dict(wip_limit=6,mode="standard",family=0.,due=1.,remaining=-4.,
    setup=3.,tool_distance=4.,noise=0.,lease_calibration=False,selector="priority",policy_seed=0)


def source_hashes(threshold=False):
    names=CORE+("stage2/mpc.py",)+(("stage2/threshold.py",) if threshold else ())
    return {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in names}


def _verify_physics(recorded):
    current=source_hashes()
    for name in CORE:
        if recorded.get(name)!=current[name]:
            raise ValueError(f"Policy artifact uses a different physical source: {name}")


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
    simulated.trace['provenance'].update(kind='counterfactual_continuation',
        boundary_tick=tick,planning_seed_role='independent future; inherited historical prefix',
        disclosure='Mixed historical/future tape: not a measured single-seed execution')
    return simulated


def candidates():
    result=[]
    for wip in (3,4,6,8):
        for mode in ('eco','standard'):
            for family in (0.,24.):
                for lease in (False,True):
                    result.append(dict(wip_limit=wip,mode=mode,family=family,
                        due=.25 if family else 1.,remaining=-4.,setup=10. if family else 3.,
                        lease_calibration=lease,selector='priority'))
    return result


def objective(metrics,horizon):
    """Legacy per-scenario display score; MPC v3 selects by lexicographic rank."""
    return (metrics['orders']-metrics['shipped']+
        .2*min(1.,metrics['total_tardiness_ticks']/max(1,metrics['orders']*horizon))+
        .01*metrics['total_cost']/(1000+metrics['total_cost']))


def cvar90(values):
    ordered=sorted(values,reverse=True);mass=.1*len(ordered)
    count=math.floor(mass);fraction=mass-count
    return (sum(ordered[:count])+(fraction*ordered[count] if fraction else 0))/mass


def scenario_rank(metrics,invalid,risk_weight=.25):
    tardy=[row['total_tardiness_ticks'] for row in metrics]
    return [sum(invalid),statistics.mean(row['orders']-row['shipped'] for row in metrics),
        statistics.mean(tardy)+risk_weight*cvar90(tardy),
        statistics.mean(row['total_cost'] for row in metrics)]


def _policy(kind,body,provenance=None):
    key=json.dumps(dict(kind=kind,**body),sort_keys=True,separators=(',',':'))
    return dict(kind=kind,id=kind+'-'+hashlib.sha256(key.encode()).hexdigest()[:20],
                **body,provenance=provenance or dict(source='inline controller parameters'))


def normalize_policy(action,base):
    if action.get('kind')=='threshold':
        from .threshold import canonical
        return _policy('threshold',dict(params=canonical(action['params']),
            base_weights=dict(base,**action.get('base_weights',{}))),action.get('provenance'))
    if action.get('kind') not in (None,'static'):
        raise ValueError('Only static and causal threshold continuation policies are supported')
    weights=action.get('weights',{}) if action.get('kind')=='static' else action
    return _policy('static',dict(weights=dict(base,**weights)),action.get('provenance') if action.get('kind') else None)


class StaticController:
    def __init__(self,spec):self.spec=spec
    def __call__(self,observation):
        return dict(weights=dict(self.spec['weights']),action_id=self.spec['id'])


def make_handler(spec):
    if spec['kind']=='static':return StaticController(spec)
    from .threshold import Controller
    return Controller(spec['params'],spec['base_weights'])


def _memory(handler):
    return dict(kind='threshold',congested=handler.congested,
        decisions=handler.count,previous_weights=deepcopy(handler.previous_weights)) if hasattr(handler,'congested') else dict(kind='static')


def _instance_config(instance):
    return dict(orders=len(instance['orders']),horizon=instance['horizon_ticks'],profile=instance['profile'])


def load_static_teacher(path,instance):
    path=Path(path);artifact=json.loads(path.read_text());_verify_physics(artifact['source_hashes'])
    role=artifact.get('policy_selection_role','validation_selected_checkpoint' if 'selected_validation' in artifact else 'training_only_last_update')
    if role!='training_only_last_update' or artifact['policy']['kind']!='context_static':
        raise ValueError('Static routing teachers must have training-only policy selection')
    if set(artifact.get('train_seeds',[]))-set(range(32)):
        raise ValueError('Static teacher uses data outside the declared training split')
    index=artifact['configs'].index(_instance_config(instance))
    action=artifact['policy']['actions'][index];weights=artifact['actions'][action]['weights']
    provenance=dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        selection_role=role,external_fit_seconds=artifact['actual_wall_seconds'],
        external_fit_episodes=artifact['fit_episodes'],source='measured routing/static teacher')
    # Keep the strong routing policy while allowing the investment decision to change.
    return [dict(kind='static',weights=dict(weights,lease_calibration=lease),provenance=provenance)
            for lease in (False,True)]


def load_threshold_bank(paths,instance,adapt=False):
    from .threshold import adapt_checkpoint,canonical
    if isinstance(paths,(str,Path)):paths=[paths]
    result=[]
    expected_threshold=source_hashes(True)['stage2/threshold.py']
    for filename in paths:
        path=Path(filename);artifact=json.loads(path.read_text());_verify_physics(artifact['source_hashes'])
        original_hashes=deepcopy(artifact['source_hashes'])
        if artifact['source_hashes'].get('stage2/threshold.py')!=expected_threshold:
            if not adapt:raise ValueError('Threshold artifact/controller version differs; explicit adapter required')
            artifact=adapt_checkpoint(artifact)
        index=artifact['configs'].index(_instance_config(instance))
        params=canonical(artifact['params'][index])
        provenance=dict(source='frozen closed-loop threshold artifact',path=str(path),
            sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            source_hashes=original_hashes,threshold_adapter=artifact.get('controller_adapter'),
            selection_role=artifact.get('policy_selection_role','unknown'),
            external_fit_seconds=artifact.get('actual_fit_wall_seconds'),
            external_simulations=artifact.get('actual_simulations'))
        result.append(dict(kind='threshold',params=params,base_weights=artifact.get('base_weights',{}),
                           provenance=provenance))
    return result


def check_future_physics(trace):
    """Check physical constraints, deliberately omitting single-seed tape audits."""
    from .check import check_trace
    spec=deepcopy(trace['instance']);spec.pop('seed',None)
    checked=check_trace(trace,spec)
    return dict(valid=checked['valid'],issues=checked['issues'][:10],
        scope='physical-only conditional continuation; historical/future random-tape audits omitted',
        coverage_disclosure='Not a certificate for one immutable full-run random tape')


class RolloutController:
    def __init__(self,factory,actions=None,scenarios=4,interval=720,seed=27491,*,
                 policy_bank=None,initial_policy=None,risk_weight=.25,
                 physical_check_futures=False,candidate_limit=None):
        if scenarios<1 or interval<1:raise ValueError('Positive scenarios and interval required')
        if not math.isfinite(risk_weight) or risk_weight<0:raise ValueError('Nonnegative risk weight required')
        if candidate_limit is not None and candidate_limit<1:raise ValueError('Positive candidate limit required')
        self.factory=factory;self.base=dict(DEFAULT_WEIGHTS,**factory.weights)
        self.actions=candidates() if actions is None else actions
        self.bank=[normalize_policy(p,self.base) for p in (policy_bank or [])]
        self.options=[normalize_policy(p,self.base) for p in self.actions]
        self.active_spec=normalize_policy(initial_policy or dict(kind='static',weights=factory.weights),self.base)
        self.active_handler=make_handler(self.active_spec)
        self.uses_threshold=any(p['kind']=='threshold' for p in self.bank+[self.active_spec]+self.options)
        self.source_hashes=source_hashes(self.uses_threshold)
        self.risk_weight=risk_weight;self.physical_check_futures=physical_check_futures
        self.candidate_limit=candidate_limit
        self.scenarios=scenarios;self.interval=interval;self.seed=seed
        self.next_tick=0;self.history=[]

    def __call__(self,observation):
        tick=observation['tick']
        if source_hashes(self.uses_threshold)!=self.source_hashes:
            raise RuntimeError('MPC physical/controller source changed during execution')
        if tick<self.next_tick:
            answer=self.active_handler(observation)
            answer['action_id']='mpc-retain-'+answer['action_id']
            return answer
        self.next_tick=tick+self.interval
        began=time.perf_counter()
        # Same independent scenario futures for every candidate at this tick.
        seeds=[int.from_bytes(hashlib.sha256(f'{self.seed}:{tick}:{k}'.encode()).digest()[:8],'big')
               for k in range(self.scenarios)]
        incumbent_id=self.active_spec['id'];incumbent_before=_memory(self.active_handler)
        options=[self.active_spec]+self.bank+self.options
        # Once the single permitted rental is committed, lease-on/off choices
        # with otherwise identical policies have identical physical futures.
        # Keep the incumbent first, preserving its state, and avoid paying for
        # duplicate counterfactuals. This does not merge differing routing rules.
        lease_redundant=self.factory.lease_requested
        unique=[];keys=set()
        for option in options:
            if lease_redundant and option['kind']=='static':
                effective=deepcopy(option)
                effective.pop('id');effective.pop('provenance',None)
                effective['weights'].pop('lease_calibration',None)
                key=json.dumps(effective,sort_keys=True)
            else:key=option['id']
            if key not in keys:keys.add(key);unique.append(option)
        if self.candidate_limit is not None:unique=unique[:self.candidate_limit]
        rows=[]
        for action,spec in enumerate(unique):
            scores=[];metrics=[];invalid=[];checks=[];durations=[]
            # Every scenario gets the same pre-boundary policy memory. Incumbent
            # memory is preserved; switching to another policy starts fresh.
            template=deepcopy(self.active_handler) if spec['id']==incumbent_id else make_handler(spec)
            first_decision=deepcopy(template)(deepcopy(observation))
            for seed in seeds:
                scenario_started=time.perf_counter()
                future=continuation(self.factory,tick,{},seed)
                future.controller=deepcopy(template)
                trace=resume(future)
                scores.append(objective(trace['metrics'],future.i['horizon_ticks']))
                metric={key:trace['metrics'][key] for key in
                    ('orders','shipped','total_tardiness_ticks','total_cost','terminal_soc_satisfied')}
                metrics.append(metric)
                checked=check_future_physics(trace) if self.physical_check_futures else dict(
                    valid=None,scope='independent future physical check not requested')
                checks.append(checked)
                invalid.append(not metric['terminal_soc_satisfied'] or any(e['type']=='infeasibility' for e in trace['events'])
                               or checked['valid'] is False)
                durations.append(time.perf_counter()-scenario_started)
            rows.append(dict(action=action,policy=spec,first_decision_weights=first_decision['weights'],
                weights=first_decision['weights'],weights_role='first boundary only; closed-loop policies can change later',
                memory_source='preserved incumbent' if spec['id']==incumbent_id else 'fresh policy start',
                rank=scenario_rank(metrics,invalid,self.risk_weight),
                mean_loss=sum(scores)/len(scores),legacy_score_role='display only; selection uses lexicographic rank',
                scenario_losses=scores,scenario_metrics=metrics,scenario_checks=checks,
                scenario_wall_seconds=durations))
        winner=min(rows,key=lambda row:(tuple(row['rank']),row['action']))
        if winner['policy']['id']!=incumbent_id:
            self.active_spec=deepcopy(winner['policy']);self.active_handler=make_handler(self.active_spec)
        answer=self.active_handler(observation)
        if answer['weights']!=winner['first_decision_weights']:
            raise AssertionError('Actual selected controller differs from its simulated first decision')
        evidence=dict(tick=tick,scenario_seeds=seeds,planning_seed_role='independent future; never actual environment seed',
            candidates=rows,selected=winner['action'],wall_seconds=time.perf_counter()-began,
            selected_policy_id=self.active_spec['id'],incumbent_policy_id=incumbent_id,
            incumbent_memory_before=incumbent_before,selected_memory_after=_memory(self.active_handler),
            selected_actual_weights=answer['weights'],risk_weight=self.risk_weight,
            offered_policy_count=len(options),unique_policy_count=len(unique),
            lease_decision_redundant=lease_redundant,
            candidate_limit=self.candidate_limit,continuation_sha256=CONTINUATION_SHA256,
            scenario_trace_role='counterfactual conditional continuation; never measured full-run evidence')
        self.history.append(evidence)
        answer['action_id']='mpc-selected-'+answer['action_id']
        return answer


def run(instance,weights=None,actions=None,scenarios=4,interval=720,seed=27491,*,
        static_teacher=None,threshold_bank=None,adapt_threshold=False,
        initial_policy=None,start_with_bank=False,risk_weight=.25,
        physical_check_futures=False,candidate_limit=None):
    from .check import check_trace
    began=time.perf_counter();bank=[]
    if static_teacher:bank.extend(load_static_teacher(static_teacher,instance))
    if threshold_bank:bank.extend(load_threshold_bank(threshold_bank,instance,adapt_threshold))
    if start_with_bank:
        if not bank:raise ValueError('Starting with bank requires a nonempty verified policy bank')
        initial_policy=bank[0]
    factory=Factory(instance,weights)
    controller=RolloutController(factory,actions,scenarios,interval,seed,policy_bank=bank,
        initial_policy=initial_policy,risk_weight=risk_weight,
        physical_check_futures=physical_check_futures,candidate_limit=candidate_limit)
    factory.controller=controller
    setup_seconds=time.perf_counter()-began
    trace=factory.run()
    check_started=time.perf_counter();trace['validation']=check_trace(trace)
    trace['planning']=dict(method='independently-resampled-scenario-rollout',decisions=controller.history,
        wall_seconds=sum(r['wall_seconds'] for r in controller.history),
        setup_wall_seconds=setup_seconds,final_check_wall_seconds=time.perf_counter()-check_started,
        total_run_wall_seconds=time.perf_counter()-began,source_hashes=controller.source_hashes,
        continuation_sha256=CONTINUATION_SHA256,policy_bank=bank,
        physical_check_futures=physical_check_futures,risk_weight=risk_weight,
        actual_final_trace_valid=trace['validation']['valid'],
        disclosure='Classical closed-loop scenario lookahead; complete conditional counterfactual futures, not measured full-run traces; no quantum or global optimality claim')
    return trace


if __name__=='__main__':
    import argparse
    from .spec import build
    from .check import check_trace
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--orders',type=int,default=12);p.add_argument('--horizon',type=int,default=5760)
    p.add_argument('--seed',type=int,default=0);p.add_argument('--scenarios',type=int,default=2)
    p.add_argument('--interval',type=int,default=720);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--planning-seed',type=int,default=27491)
    p.add_argument('--static-teacher',type=Path)
    p.add_argument('--threshold-bank',type=Path,action='append')
    p.add_argument('--adapt-threshold',action='store_true')
    p.add_argument('--start-with-bank',action='store_true')
    p.add_argument('--no-default-actions',action='store_true')
    p.add_argument('--candidate-limit',type=int)
    p.add_argument('--risk-weight',type=float,default=.25)
    p.add_argument('--check-futures',action='store_true',help='Physical-only checks; mixed-past/future random-tape audit explicitly omitted')
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    trace=run(build(a.orders,a.horizon,a.seed),dict(wip_limit=6,mode='standard',lease_calibration=True),
        actions=[] if a.no_default_actions else None,scenarios=a.scenarios,interval=a.interval,
        seed=a.planning_seed,static_teacher=a.static_teacher,threshold_bank=a.threshold_bank,
        adapt_threshold=a.adapt_threshold,start_with_bank=a.start_with_bank,
        candidate_limit=a.candidate_limit,risk_weight=a.risk_weight,physical_check_futures=a.check_futures)
    (a.output/'trace.json').write_text(json.dumps(trace)+'\n')
    print(json.dumps(dict(metrics=trace['metrics'],valid=trace['validation']['valid'],planning_seconds=trace['planning']['wall_seconds'])))
