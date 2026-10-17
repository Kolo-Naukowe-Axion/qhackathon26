"""Small causal PPO/CEM policies around the strong physical recovery decoder.

Six actions change WIP and QA-worker protection only. Static routing/admission,
tool homes and physical recovery remain explicit context choices. An exact
static controller stays eligible during per-context validation selection.
"""
from concurrent.futures import ProcessPoolExecutor
from copy import deepcopy
import hashlib
import json
import math
import multiprocessing
from pathlib import Path
import random
import time

from . import sequential as seq
from .recovery_routing import run
from .spec import build
from .check import check_trace

ROOT=Path(__file__).resolve().parents[1]
ACTIONS=tuple(dict(wip_limit=w,qa_guard_threshold=g) for w in (4,6,8) for g in (0,4))
SOURCES=tuple('stage2/'+n+'.py' for n in ('adaptive_recovery','sequential','recovery_routing','routing',
    'kit_recovery','kitting','admission','tooling','specialist','advanced','engine','spec','check','dispatch','qubo','quantum'))+('instances/stage2/metaltech_pressure.json',)


def hashes():return {n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in SOURCES}


class Controller:
    def __init__(self,policy,base_weights,actor_seed=0,deterministic=False,interval=720):
        import numpy as np
        self.np=np;self.policy=deepcopy(policy);self.base=dict(base_weights,policy_seed=actor_seed)
        self.rng=random.Random(actor_seed);self.deterministic=deterministic;self.interval=interval
        if interval<=0:raise ValueError('Positive macro interval required')
        self.next_tick=0;self.last=None;self.previous=None;self.memory={};self.trajectory=[]
        self.parameters={k:np.asarray(v,dtype=np.float32) for k,v in policy.get('network',{}).items()}

    def __call__(self,observation):
        if observation['tick']<self.next_tick:return deepcopy(self.last)
        self.next_tick=observation['tick']+self.interval
        x=seq.features(observation,self.previous,self.memory);kind=self.policy['kind'];value=0.;logp=0.
        if kind=='static':action=self.policy['action']
        elif kind=='schedule':
            sequence=self.policy['schedule'];segment=min(len(sequence)-1,int(observation['tick']/observation['horizon_ticks']*len(sequence)))
            action=sequence[segment]
        elif kind=='ppo':
            p=self.parameters;np=self.np
            h=np.tanh(p['second.weight']@np.tanh(p['first.weight']@np.asarray(x,dtype=np.float32)+p['first.bias'])+p['second.bias'])
            logits=p['actor.weight']@h+p['actor.bias'];probabilities=np.exp(logits-logits.max());probabilities/=probabilities.sum()
            action=int(np.argmax(probabilities)) if self.deterministic else self.rng.choices(range(len(ACTIONS)),weights=probabilities)[0]
            logp=math.log(max(float(probabilities[action]),1e-30));value=float((p['critic.weight']@h+p['critic.bias'])[0])
        else:raise ValueError('Unsupported adaptive recovery policy')
        if type(action) is not int or not 0<=action<len(ACTIONS):raise ValueError('Action outside the declared6-action domain')
        weights=dict(self.base,**ACTIONS[action]);self.previous=deepcopy(observation)
        self.memory.update(wip=weights['wip_limit'],lease=weights.get('lease_calibration',False))
        self.trajectory.append(dict(features=x,action=action,old_logp=logp,value=value,
            potential=seq.potential(observation),tick=observation['tick']))
        self.last=dict(weights=weights,action_id=f'adaptive-recovery-{kind}-{action}')
        return deepcopy(self.last)


def rollout(task):
    started=time.perf_counter();cpu=time.process_time()
    if hashes()!=task['source_hashes']:raise RuntimeError('Adaptive recovery source changed before rollout')
    context=task['context'];instance=build(**context['config'],seed=task['seed'])
    controller=Controller(task['policy'],context['weights'],task['actor_seed'],task.get('deterministic',False),task.get('interval',720))
    trace=run(instance,context['weights'],controller,**context['solver_options']);checked=check_trace(trace,instance)
    valid=checked['valid'] and checked.get('terminal_requirements_met',False)
    reward=seq.terminal_reward(trace['metrics'],valid,context['config']['horizon'])
    rewards=seq.trajectory_rewards([step['potential'] for step in controller.trajectory],reward)
    for step,r in zip(controller.trajectory,rewards):step['reward']=r
    if hashes()!=task['source_hashes']:raise RuntimeError('Adaptive recovery source changed during rollout')
    return dict(context_id=task['context_id'],seed=task['seed'],actor_seed=task['actor_seed'],phase=task['phase'],
        valid=valid,issues=checked['issues'],metrics=trace['metrics'],reward=reward,
        trajectory=controller.trajectory,decisions=len(controller.trajectory),
        action_changes=sum(a['action']!=b['action'] for a,b in zip(controller.trajectory,controller.trajectory[1:])),
        wall_seconds=time.perf_counter()-started,cpu_seconds=time.process_time()-cpu)


def make_network(torch):
    network=seq.make_network(torch)
    network.actor=torch.nn.Linear(64,len(ACTIONS))
    return network


def selection_key(rows):
    return (sum(not r['valid'] for r in rows),sum(r['metrics']['orders']-r['metrics']['shipped'] for r in rows),
        sum(r['metrics']['total_tardiness_ticks'] for r in rows),sum(r['metrics']['total_cost'] for r in rows))


def train(contexts,output,method='ppo',seconds=1200,workers=32,seed=2026,max_updates=None):
    if method not in ('ppo','cem') or seconds<=0 or workers<1:raise ValueError('PPO/CEM and positive budgets required')
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=False)
    started=time.perf_counter();sources=hashes();rng=random.Random(seed);contexts=deepcopy(contexts)
    for context in contexts:
        if not context.get('selection_provenance'):raise ValueError('Every static context needs training selection/cost provenance')
        if context['weights'].get('selector','priority')!='priority':raise ValueError('This ablation holds the local selector at priority')
    teachers=[next(a for a,w in enumerate(ACTIONS) if all(context['weights'].get(k)==v for k,v in w.items())) for context in contexts]
    baseline=[dict(kind='static',action=a) for a in teachers]
    selected=deepcopy(baseline);best=[None]*len(contexts);curves=[];fit_episodes=0;validation_episodes=0;update=0
    probabilities=[[[.8 if a==teacher else .2/(len(ACTIONS)-1) for a in range(len(ACTIONS))] for _ in range(8)] for teacher in teachers]
    pools=[{tuple([a]*8):None} for a in teachers];cache={};torch=None;network=None;optimizer=None
    if method=='ppo':
        import torch
        torch.set_num_threads(1);torch.manual_seed(seed);network=make_network(torch)
    for name in SOURCES:
        path=output/'source_snapshot'/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes((ROOT/name).read_bytes())
    protocol=dict(schema='stage2-adaptive-recovery-training.v1',method=method,contexts=contexts,actions=list(ACTIONS),
        source_hashes=sources,train_seeds=list(range(32)),validation_seeds=list(range(100,116)),final_tapes=0,
        seed=seed,requested_wall_seconds=seconds,workers=workers,interval_minutes=720,
        selection='Per-context lexicographic validation; exact static fallback always eligible',
        inference='PPO evaluated by deterministic argmax; training samples from its actor RNG; CEM is an8-segment time policy',
        cpu_scope='Factory simulation dominates these small networks; no GPU requested')
    (output/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    def task(context_id,policy,tape,actor,phase,deterministic=False):
        return dict(context_id=context_id,context=contexts[context_id],policy=deepcopy(policy),seed=tape,
            actor_seed=actor,phase=phase,deterministic=deterministic,source_hashes=sources)
    def compact(row):return {k:v for k,v in row.items() if k!='trajectory'}
    def save(name,artifact):
        temporary=output/(name+'.tmp');temporary.write_text(json.dumps(artifact,indent=2)+'\n');temporary.replace(output/name)
    with ProcessPoolExecutor(max_workers=workers,mp_context=multiprocessing.get_context('spawn')) as pool,\
         (output/'episodes.jsonl').open('x') as log:
        def measure(tasks):
            rows=list(pool.map(rollout,tasks))
            for row in rows:log.write(json.dumps(compact(row))+'\n')
            log.flush();return rows
        def validate(policies):
            nonlocal validation_episodes
            rows=measure([task(c,p,tape,0,'VALIDATION',True) for c,p in enumerate(policies) for tape in range(100,116)])
            validation_episodes+=len(rows)
            for c,policy in enumerate(policies):
                group=[r for r in rows if r['context_id']==c];key=selection_key(group)
                if best[c] is None or key<tuple(best[c]['key']):
                    best[c]=dict(key=list(key),selected_update=update,summary=seq.summary(group));selected[c]=deepcopy(policy)
            return rows
        validate(baseline)
        if method=='ppo':
            teacher_rows=measure([task(c,p,tape,0,'TRAIN-cloning',True) for c,p in enumerate(baseline) for tape in range(8)])
            if any(not r['valid'] for r in teacher_rows):raise RuntimeError('Strong teacher has an invalid physical execution')
            cloning=seq.behavioral_clone(torch,network,teacher_rows,epochs=80)
            optimizer=torch.optim.Adam(network.parameters(),lr=.0003)
            fit_episodes+=len(teacher_rows)
            validate([dict(kind='ppo',network=seq.export_network(network)) for _ in contexts])
        else:cloning=None
        artifact=dict(schema='stage2-adaptive-recovery-policy.v1',method=method,source_hashes=sources,
            configs=[c['config'] for c in contexts],contexts=contexts,actions=list(ACTIONS),feature_names=list(seq.FEATURE_NAMES),
            policies_by_context=deepcopy(selected),selection=deepcopy(best),policy_selection_role='validation_selected_with_exact_static_fallback',
            train_seeds=list(range(32)),validation_seeds=list(range(100,116)),final_tapes=0,seed=seed,interval=720,
            fit_episodes=fit_episodes,validation_episodes=validation_episodes,cloning=cloning,curves=curves,
            requested_wall_seconds=seconds,actual_wall_seconds=time.perf_counter()-started,workers=workers,last_training_policies=None)
        save('selected-checkpoint.json',artifact)
        while time.perf_counter()-started<seconds and (max_updates is None or update<max_updates):
            if hashes()!=sources:raise RuntimeError('Adaptive recovery training source changed')
            update+=1;batch=[];metadata=[]
            if method=='ppo':
                policy=dict(kind='ppo',network=seq.export_network(network))
                for j in range(64):
                    c=rng.randrange(len(contexts));batch.append(task(c,policy,rng.randrange(32),seed+fit_episodes+j,'TRAIN-PPO'))
                rows=measure(batch);diagnostic=seq.update_ppo(torch,network,optimizer,rows,epochs=4)
                candidates=[dict(kind='ppo',network=seq.export_network(network)) for _ in contexts]
            else:
                c=rng.randrange(len(contexts));tape=rng.randrange(32)
                for j in range(64):
                    sequence=tuple(rng.choices(range(len(ACTIONS)),weights=p)[0] for p in probabilities[c])
                    batch.append(task(c,dict(kind='schedule',schedule=list(sequence)),tape,0,'TRAIN-CEM',True));metadata.append(sequence)
                rows=measure(batch);elite=sorted(range(len(rows)),key=lambda j:selection_key([rows[j]]))[:16]
                for segment in range(8):
                    target=[.05/len(ACTIONS)]*len(ACTIONS)
                    for j in elite:target[metadata[j][segment]]+=.95/len(elite)
                    probabilities[c][segment]=[.75*a+.25*b for a,b in zip(probabilities[c][segment],target)]
                for sequence,row in zip(metadata,rows):
                    record=pools[c].setdefault(sequence,{})
                    if record is None:record={};pools[c][sequence]=record
                    record[tape]=row['reward']
                diagnostic=dict(context=c,paired_training_tape=tape)
                candidates=None
            fit_episodes+=len(rows)
            if update==1 or update%10==0:
                if method=='cem':
                    candidates=[]
                    for c,history in enumerate(pools):
                        ordered=sorted(history,key=lambda s:sum((history[s] or {0:-1e9}).values())/len(history[s] or {0:0}),reverse=True)[:7]
                        incumbent=tuple([teachers[c]]*8)
                        if incumbent not in ordered:ordered.append(incumbent)
                        pending=[];keys=[]
                        for sequence in ordered:
                            for tape in range(8):
                                key=(c,sequence,tape)
                                if key not in cache:pending.append(task(c,dict(kind='schedule',schedule=list(sequence)),tape,0,'TRAIN-rerank',True));keys.append(key)
                        measured=measure(pending) if pending else []
                        fit_episodes+=len(measured)
                        for key,row in zip(keys,measured):cache[key]=row
                        winner=min(ordered,key=lambda s:selection_key([cache[c,s,t] for t in range(8)]))
                        candidates.append(dict(kind='schedule',schedule=list(winner)))
                validate(candidates)
            curve=dict(update=update,fit_episodes=fit_episodes,elapsed_seconds=time.perf_counter()-started,
                batch=seq.summary(rows),diagnostic=diagnostic,selected_contexts=deepcopy(best))
            curves.append(curve);print(json.dumps(curve),flush=True)
            artifact=dict(schema='stage2-adaptive-recovery-policy.v1',method=method,source_hashes=sources,
                configs=[c['config'] for c in contexts],contexts=contexts,actions=list(ACTIONS),feature_names=list(seq.FEATURE_NAMES),
                policies_by_context=deepcopy(selected),selection=deepcopy(best),policy_selection_role='validation_selected_with_exact_static_fallback',
                train_seeds=list(range(32)),validation_seeds=list(range(100,116)),final_tapes=0,seed=seed,interval=720,
                fit_episodes=fit_episodes,validation_episodes=validation_episodes,cloning=cloning,curves=curves,
                requested_wall_seconds=seconds,actual_wall_seconds=time.perf_counter()-started,workers=workers,
                last_training_policies=candidates if candidates is not None else None)
            save('selected-checkpoint.json',artifact)
        if hashes()!=sources:raise RuntimeError('Adaptive source changed at completion')
        artifact['actual_wall_seconds']=time.perf_counter()-started;save('selected-checkpoint.json',artifact)
    return artifact


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--contexts',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--method',choices=('ppo','cem'),default='ppo')
    p.add_argument('--seconds',type=float,default=1200);p.add_argument('--workers',type=int,default=32)
    p.add_argument('--seed',type=int,default=2026);p.add_argument('--max-updates',type=int)
    a=p.parse_args();train(json.loads(a.contexts.read_text()),a.output,a.method,a.seconds,a.workers,a.seed,a.max_updates)
