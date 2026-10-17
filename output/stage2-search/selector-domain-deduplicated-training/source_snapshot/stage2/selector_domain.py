"""Audit and optionally expand fixed-operation crew assignments.

Default-off delegates to the original run. The opt-in run differs only by three
explicit boundary hooks in an AST-verified copy of the unchanged factory loop.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
from copy import deepcopy
import gzip
import hashlib
import inspect
import itertools
import json
from pathlib import Path
import textwrap
import time
import traceback

from .admission import AdmissionMixin
from .engine import Factory
from .kit_recovery import RecoveryFactory
from .recovery_routing import BASE_WEIGHTS,ROOT,SOURCES as SHARED_SOURCES

ENGINE_SHA256='ec97bf3c1e57110cc0ddef02e54fafc2626b3aab079718a8ab0f04a5ba26244f'
SOURCES=('stage2/selector_domain.py',)+SHARED_SOURCES


def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def _derived_run():
    if hashlib.sha256((ROOT/'stage2/engine.py').read_bytes()).hexdigest()!=ENGINE_SHA256:
        raise RuntimeError('Physical loop changed; re-audit selector hooks before use')
    original=ast.parse(textwrap.dedent(inspect.getsource(Factory.run)));tree=deepcopy(original)
    loop=tree.body[0].body[0]
    if not isinstance(loop,ast.For):raise RuntimeError('Unexpected physical run loop')
    inserted=[];body=[];counts=Counter()
    for node in loop.body:
        if isinstance(node,ast.Assign) and ast.unparse(node.targets[0])=='method':
            hook=ast.parse('offers,valid_requests=self.expand_dispatch(offers,valid_requests)').body[0]
            body.append(hook);inserted.append(hook);counts['expand']+=1
        if isinstance(node,ast.For) and ast.unparse(node.target)=='idx' and ast.unparse(node.iter)=='selected':
            hook=ast.parse('self.prepare_selected_crews(offers,selected)').body[0]
            body.append(hook);inserted.append(hook);body.append(node);counts['commit']+=1
            hook=ast.parse('self.verify_selected_commits(evidence)').body[0]
            body.append(hook);inserted.append(hook)
        else:body.append(node)
    if counts!={'expand':1,'commit':1}:raise RuntimeError('Unexpected dispatch hook anchors')
    loop.body=body
    recovered=deepcopy(tree);recovered.body[0].body[0].body=[node for i,node in enumerate(loop.body) if loop.body[i] not in inserted]
    if ast.dump(recovered,include_attributes=False)!=ast.dump(original,include_attributes=False):
        raise RuntimeError('Derived run changed physical statements beyond declared hooks')
    tree.body[0].name='_crew_run';ast.fix_missing_locations(tree)
    namespace=dict(Factory.run.__globals__);exec(compile(tree,'<audited-expanded-crew-loop>','exec'),namespace)
    return namespace['_crew_run'],ast.unparse(tree)


CREW_RUN,CREW_RUN_SOURCE=_derived_run()
CREW_RUN_SHA256=hashlib.sha256(CREW_RUN_SOURCE.encode()).hexdigest()


def operation_key(op):return (op['machine_id'],tuple(op['unit_ids']),op['mode'])


def assignment_payload(op):
    return {k:op[k] for k in ('unit_ids','machine_id','start','end','mode','worker_intervals','tool_ids','power_kw')}


class SelectorDomainMixin:
    def __init__(self,*args,selector_domain=None,**kwargs):
        policy=dict(mode='off',max_candidates=18,audit_boundaries=12)
        if selector_domain:policy.update(selector_domain)
        if set(policy)!={'mode','max_candidates','audit_boundaries'} or policy['mode'] not in ('off','audit','expanded'):
            raise ValueError('Unknown selector-domain policy')
        if not 1<=policy['max_candidates']<=24 or not 0<=policy['audit_boundaries']<=64:raise ValueError('Unbounded selector-domain policy')
        super().__init__(*args,**kwargs)
        self.selector_domain=policy;self._crew_context=None;self._crew_commits={};self.domain_audit=[];self.domain_counts=Counter();self._domain_seen=set()
        self.domain_wall_seconds=0.;self._domain_shadow=False

    def available_worker(self,skill,hall,length,allow_walk=True,start=None):
        if self._crew_context is None:return super().available_worker(skill,hall,length,allow_walk,start)
        context=self._crew_context;call=context['_calls'];context['_calls']+=1
        # HEAT/WASH can themselves require the setup skill. Distinguish the
        # first process-role call from a later setup-role call by call order
        # and interval length, rather than conflating identical skill names.
        role='primary' if call==0 or length>context['_setup_ticks'] else 'setup'
        target=context[role]
        saved={wid:w['skills'] for wid,w in self.workers.items() if wid!=target and skill in w['skills']}
        try:
            for wid,skills in saved.items():self.workers[wid]['skills']=[s for s in skills if s!=skill]
            return super().available_worker(skill,hall,length,allow_walk,start)
        finally:
            for wid,skills in saved.items():self.workers[wid]['skills']=skills

    def process(self,m,parts,mode='standard',parents=None,kind='process',preview=False,prepare_only=False):
        key=(m['id'],tuple(p['id'] for p in parts),mode)
        plan=self._crew_commits.get(key) if not preview and not prepare_only else None
        previous=self._crew_context
        if plan:self._crew_context=plan['crew']
        if self._crew_context is not None:
            setup=0 if m['family'] in (None,parts[0]['family']) else self.i['setup_matrix'][m['family']][parts[0]['family']]
            self._crew_context=dict(self._crew_context,_calls=0,_setup_ticks=setup)
        try:result=super().process(m,parts,mode,parents,kind,preview,prepare_only)
        finally:self._crew_context=previous
        if plan:
            if not result:raise RuntimeError('Selected crew alternative failed physical commit')
            actual=self.trace['operations'][-1]
            if assignment_payload(actual)!=assignment_payload(plan['offer']):raise RuntimeError('Selected and committed physical assignment differ')
            actual['dispatch_candidate_id']=plan['candidate_id'];del self._crew_commits[key]
        return result

    def _shadow_priority(self,offers,evidence):
        # No completions/reveals/QA are executed: this is the same public live
        # boundary, with sequential original process commits on a private copy.
        shadow=deepcopy(self);shadow._domain_shadow=True;shadow._crew_commits={};shadow._crew_context=None
        actual=[]
        for idx,op in enumerate(offers):
            before=len(shadow.trace['operations'])
            success=shadow.process(shadow.machines[op['machine_id']],[shadow.parts[u] for u in op['unit_ids']],op['mode'])
            if success:
                if len(shadow.trace['operations'])!=before+1:raise RuntimeError('Unexpected shadow process bookkeeping')
                actual.append(dict(candidate_id=f'C{idx}',offer=deepcopy(shadow.trace['operations'][-1])))
        chosen={v['candidate_id'] for v in actual};rewards={c['id']:c['reward'] for c in evidence['candidates']}
        conflicts=[pair for pair in evidence['conflicts'] if set(pair)<=chosen]
        return dict(selected=sorted(chosen),started=len(actual),reward=sum(rewards[c] for c in chosen),
            frozen_conflicts_violated=conflicts,actual_assignments=actual,
            changed_worker_assignments=[v['candidate_id'] for v in actual if v['offer']['worker_intervals']!=offers[int(v['candidate_id'][1:])]['worker_intervals']],
            scope='Same-boundary private original-process commits; no future outcomes, not a measured full execution')

    def _variants(self,op,request):
        m,parts,mode=request;skill=self.i['process_skills'][op['process']]
        primary=[wid for wid,w in self.workers.items() if skill in w['skills'] and w['hall']==m['hall']]
        setup=[wid for wid,w in self.workers.items() if 'setup' in w['skills'] and w['hall']==m['hall']]
        variants=[];seen=set();original=self._crew_context
        try:
            for wid in primary:
                worker=self.workers[wid]
                separate=m['family'] not in (None,parts[0]['family']) and not ('setup' in worker['skills'] and worker['busy']<=self.t)
                for swid in (setup if separate else [wid]):
                    crew=dict(primary=wid,setup=swid);self._crew_context=crew
                    offer=self.process(m,parts,mode,preview=True)
                    if not offer:continue
                    key=digest(assignment_payload(offer))
                    if key in seen:continue
                    seen.add(key);offer['_crew_assignment']=crew;variants.append(offer)
        finally:self._crew_context=original
        if not variants:raise RuntimeError('Original offered crew disappeared during alternative generation')
        if not any(assignment_payload(v)==assignment_payload(op) for v in variants):raise RuntimeError('Expanded crew domain omitted original assignment')
        return variants

    def expand_dispatch(self,offers,requests):
        if not offers:return offers,requests
        started=time.perf_counter();mode=self.selector_domain['mode'];method=self.weights.get('selector','priority')
        priorities=[self.priority(parts[0]) for _,parts,_ in requests]
        from .dispatch import choose
        signature=digest([dict(unit_ids=o['unit_ids'],machine_id=o['machine_id'],mode=o['mode'],tool_ids=o['tool_ids'],
            intervals=[dict(worker_id=v['worker_id'],start=v['start']-self.t,end=v['end']-self.t) for v in o['worker_intervals']]) for o in offers])
        if len(offers)>1 and signature not in self._domain_seen and len(self.domain_audit)<self.selector_domain['audit_boundaries']:
            _,fixed=choose(offers,self.i,self.active,self.t,self.grid_cap,priorities,'exact',seed=self.weights.get('policy_seed',0)+self.t)
            if fixed['conflicts']:
                self._domain_seen.add(signature)
                sequential=self._shadow_priority(offers,fixed)
                self.domain_audit.append(dict(tick=self.t,pool_sha256=digest(dict(offers=offers,priorities=priorities)),
                    original_offers=deepcopy(offers),fixed_pool=deepcopy(fixed),shadow_priority=sequential,
                    strict_domain_reward_loss=sequential['reward']>fixed['result']['reward']+1e-8,
                    start_count_delta=sequential['started']-len(fixed['result']['selected'])))
        if mode!='expanded' or method=='priority':
            self.domain_wall_seconds+=time.perf_counter()-started;return offers,requests
        expanded=[];expanded_requests=[]
        for op,request in zip(offers,requests):
            variants=self._variants(op,request)
            for variant in variants:expanded.append(variant);expanded_requests.append(request)
        self.domain_counts['boundaries']+=1;self.domain_counts['original_candidates']+=len(offers)
        self.domain_counts['generated_crew_candidates']+=len(expanded)
        self.domain_counts['max_generated_candidates']=max(self.domain_counts['max_generated_candidates'],len(expanded))
        if len(expanded)>self.selector_domain['max_candidates']:
            self.domain_counts['oversize_original_pool_fallbacks']+=1
            self.domain_wall_seconds+=time.perf_counter()-started;return offers,requests
        self.domain_counts['expanded_boundaries']+=len(expanded)>len(offers)
        self.domain_wall_seconds+=time.perf_counter()-started;return expanded,expanded_requests

    def prepare_selected_crews(self,offers,selected):
        if self.selector_domain['mode']!='expanded' or self.weights.get('selector','priority')=='priority':return
        if self._crew_commits:raise RuntimeError('Unconsumed previous crew assignment')
        for idx in selected:
            offer=offers[idx]
            if '_crew_assignment' not in offer:continue  # explicit oversize original-domain fallback
            key=operation_key(offer)
            if key in self._crew_commits:raise RuntimeError('Selector chose multiple crew alternatives for one operation')
            self._crew_commits[key]=dict(offer=offer,crew=offer['_crew_assignment'],candidate_id=f'C{idx}')

    def verify_selected_commits(self,evidence):
        if self._crew_commits:raise RuntimeError('Expanded selected crew was not committed')
        if evidence is not None and sorted(evidence['result']['selected'])!=sorted(evidence['committed']):
            raise RuntimeError('Selector selected/committed candidate IDs differ')

    def run(self):
        if self.selector_domain['mode']=='off':return super().run()
        return CREW_RUN(self)

    def finish(self):
        super().finish()
        self.trace.setdefault('algorithm_audit',{})['selector_domain']=dict(policy=deepcopy(self.selector_domain),
            boundary_audits=deepcopy(self.domain_audit),counts=dict(self.domain_counts),
            generation_and_audit_wall_seconds=self.domain_wall_seconds,derived_loop_sha256=CREW_RUN_SHA256,
            scope='Operation + complete fixed crew alternatives; original machine/tool/worker/power constraints; oversize domain fallback disclosed')


class SelectorDomainFactory(SelectorDomainMixin,RecoveryFactory):pass
class AdmissionSelectorDomainFactory(AdmissionMixin,SelectorDomainFactory):pass


def run(instance,weights=None,controller=None,*,admission=False,**options):
    cls=AdmissionSelectorDomainFactory if admission else SelectorDomainFactory
    return cls(instance,weights,controller,**options).run()


def hashes():return {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in SOURCES}


def campaign(output,seeds=(0,1,2,4),orders=12,modes=('audit','expanded'),methods=('exact',),max_candidates=18):
    from .spec import build
    from .check import check_trace
    if any(s not in range(32) for s in seeds):raise ValueError('TRAIN0–31 only')
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=False);sources=hashes()
    tasks=[dict(config=dict(orders=orders,horizon=5760,profile='full',seed=seed),domain_mode=mode,selector=method)
        for mode,method,seed in itertools.product(modes,methods,seeds)]
    protocol=dict(schema='stage2-selector-domain.v1',source_hashes=sources,tasks=tasks,actor_seed=7,
        selection='TRAIN0/1/2 plus severe TRAIN4 chosen from completed strong-selector cohort; no VAL/final',max_candidates=max_candidates,
        scope='Frozen recovery,hard tool homes,family admission,QA guard4,WIP8; same operation objective; explicit crew alternatives')
    (output/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    for name in SOURCES:
        path=output/'source_snapshot'/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes((ROOT/name).read_bytes())
    rows=[];start=time.perf_counter()
    with (output/'rows.jsonl').open('x') as log:
        for task in tasks:
            before=time.perf_counter();cpu=time.process_time();trace=None;row=dict(task)
            try:
                if hashes()!=sources:raise RuntimeError('Source drift')
                instance=build(**task['config']);weights=dict(BASE_WEIGHTS,selector=task['selector'],policy_seed=7)
                trace=run(instance,weights,admission=True,tool_policy={'mode':'hard'},kit_reservation=True,
                    recovery_policy={'enabled':True},selector_domain=dict(mode=task['domain_mode'],max_candidates=max_candidates))
                checked=check_trace(trace);mismatch=[d['tick'] for d in trace['qubo_decisions'] if sorted(d['result']['selected'])!=sorted(d['committed'])]
                row.update(valid=checked['valid'] and not mismatch,issues=checked['issues'],decode_mismatches=mismatch,metrics=trace['metrics'],
                    domain=trace['algorithm_audit']['selector_domain'],physical_instance_sha256=digest(instance))
                if hashes()!=sources:raise RuntimeError('Source drift')
            except Exception as exc:row.update(valid=False,error=dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc()))
            if trace is not None:
                payload=json.dumps(trace,separators=(',',':')).encode();path=output/f'trace-task{len(rows)}.json.gz';path.write_bytes(gzip.compress(payload,mtime=0))
                row.update(trace_path=str(path),trace_sha256=hashlib.sha256(payload).hexdigest())
            row.update(wall_seconds=time.perf_counter()-before,cpu_seconds=time.process_time()-cpu)
            rows.append(row);log.write(json.dumps(row)+'\n');log.flush()
    result=dict(**protocol,rows=rows,wall_seconds=time.perf_counter()-start)
    (output/'report.json').write_text(json.dumps(result,indent=2)+'\n');return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--seeds',type=int,nargs='+',default=[0,1,2,4]);p.add_argument('--orders',type=int,default=12)
    p.add_argument('--modes',nargs='+',default=['audit','expanded']);p.add_argument('--methods',nargs='+',default=['exact'])
    p.add_argument('--max-candidates',type=int,default=18);a=p.parse_args()
    result=campaign(a.output,a.seeds,a.orders,a.modes,a.methods,a.max_candidates)
    print(json.dumps(dict(wall_seconds=result['wall_seconds'],rows=[{k:r.get(k) for k in ('config','domain_mode','selector','valid','metrics','error','wall_seconds')} for r in result['rows']]),indent=2))


if __name__=='__main__':main()
