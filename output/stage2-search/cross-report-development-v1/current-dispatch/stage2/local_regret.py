"""Offline full-factory continuation regret for one frozen local action pool.

The continuation oracle uses realized future outcomes for analysis only. It is
not deployed causally, and is neither a global optimizer nor quantum advantage.
"""
from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
import gzip
import hashlib
import itertools
import json
from pathlib import Path
import threading
import time
import traceback

ROOT=Path(__file__).resolve().parents[1]
SOURCES=('stage2/local_regret.py','stage2/engine.py','stage2/spec.py','stage2/check.py',
    'stage2/dispatch.py','stage2/qubo.py','stage2/quantum.py','stage2/advanced.py',
    'stage2/specialist.py','stage2/tooling.py','instances/stage2/metaltech_pressure.json')
_ACTIVE_OVERRIDE=False


def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def hashes():return {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in SOURCES}


def pool_payload(decision):
    return {key:decision[key] for key in ('candidates','conflicts','capacities','offered_operations')}


def pool_sha(decision):return digest(pool_payload(decision))


def prefix_payload(trace,tick):
    """All physical commitments/observations strictly before the forced tick.

    Full records of previously committed future intervals remain included.
    Result timers, generated timestamps and future outcomes are excluded.
    """
    return {key:[row for row in trace[key] if row['tick' if key in ('events','energy') else 'start']<tick]
        for key in ('operations','moves','worker_moves','events','energy')}


def independently_feasible(pool,selected):
    candidates={c['id']:c for c in pool['candidates']};selected=list(selected);chosen=set(selected)
    if len(chosen)!=len(selected) or not chosen<=set(candidates):return False
    if any(a in chosen and b in chosen for a,b in pool['conflicts']):return False
    return all(sum(candidates[uid].get('resources',{}).get(resource,0) for uid in chosen)<=capacity
        for resource,capacity in pool['capacities'].items())


def feasible_subsets(pool):
    ids=[c['id'] for c in pool['candidates']]
    if len(ids)>4:raise ValueError('Audit enumerates at most four core candidates')
    return [list(subset) for n in range(len(ids)+1) for subset in itertools.combinations(ids,n)
            if independently_feasible(pool,subset)]


@contextmanager
def force_boundary(boundary,selected):
    """Override exactly one dispatch tick, only in this process/thread.

    Original choose reconstructs the pool first. The forced set is checked
    against both independent original constraints and the compiled QUBO.
    """
    global _ACTIVE_OVERRIDE
    from . import dispatch
    from .qubo import build_qubo
    if _ACTIVE_OVERRIDE:raise RuntimeError('Nested/concurrent dispatch overrides are prohibited')
    original=dispatch.choose;owner=threading.get_ident();record=dict(hits=0,forced_selected=list(selected))
    expected=pool_sha(boundary);_ACTIVE_OVERRIDE=True
    def wrapped(offers,instance,active,tick,grid_cap,priorities,method='greedy',seed=0):
        if threading.get_ident()!=owner:raise RuntimeError('Dispatch override cannot run in a different thread')
        if tick!=boundary['tick']:return original(offers,instance,active,tick,grid_cap,priorities,method,seed)
        started=time.perf_counter();indices,evidence=original(offers,instance,active,tick,grid_cap,priorities,method,seed)
        record['hits']+=1
        if record['hits']!=1:raise RuntimeError('Target dispatch boundary occurred more than once')
        reconstructed=dict(evidence,offered_operations=deepcopy(offers));record['reconstructed_pool_sha256']=pool_sha(reconstructed)
        if record['reconstructed_pool_sha256']!=expected:raise ValueError('Frozen full candidate pool differs at forced boundary')
        if not independently_feasible(reconstructed,selected):raise ValueError('Forced set violates original candidate/resource/conflict constraints')
        q=build_qubo(evidence['candidates'],evidence['conflicts'],evidence['capacities'])
        selected_indices=[i for i,c in enumerate(q.candidates) if c.id in selected]
        if not q.feasible(selected_indices):raise ValueError('Independent/QUBO feasibility disagreement')
        prior=evidence['result']
        evidence['result']=dict(selected=list(selected),reward=sum(q.candidates[i].reward for i in selected_indices),
            feasible=True,method='forced_offline_counterfactual',requested_method='exact',
            quantum_executed=False,quantum_algorithm_simulated=False,physical_quantum_executed=False,
            qubo=q.summary(),repaired=False,raw=dict(bits=q.encode(selected_indices),selected=list(selected),feasible=True),
            reconstruction_result=prior,elapsed_seconds=time.perf_counter()-started,
            provenance=dict(role='Offline one-tick forced action; exact causal selector resumes afterward',
                pool_sha256=expected,actual_future_outcomes_used_only_for_posthoc_oracle=True,
                no_claim='Not a deployed future oracle or global factory optimum'))
        return selected_indices,evidence
    dispatch.choose=wrapped
    try:yield record
    finally:dispatch.choose=original;_ACTIVE_OVERRIDE=False


def _factory(instance,weights):
    from .tooling import ToolingFactory
    return ToolingFactory(instance,weights,tool_policy=dict(mode='hard'))


def _checked(trace):
    from .check import check_trace
    report=check_trace(trace)
    mismatches=[dict(tick=d['tick'],selected=d['result']['selected'],committed=d.get('committed'))
        for d in trace['qubo_decisions'] if sorted(d['result']['selected'])!=sorted(d.get('committed',[]))]
    if mismatches:report['valid']=False;report['issues'].append(dict(code='decode_commit_mismatch',evidence=mismatches))
    return report


def rank(metrics):
    return [metrics['orders']-metrics['shipped'],metrics['total_tardiness_ticks'],metrics['total_cost']]


def execute(instance,weights,*,boundary=None,selected=None,expected_prefix=None,trace_path=None):
    started=time.perf_counter();cpu=time.process_time();factory=_factory(instance,weights);record={};error=None
    try:
        if boundary is None:trace=factory.run()
        else:
            with force_boundary(boundary,selected) as record:trace=factory.run()
            if record['hits']!=1:raise ValueError('Forced boundary was never encountered')
        checked=_checked(trace)
        observed=digest(prefix_payload(trace,boundary['tick'])) if boundary is not None else None
        if expected_prefix is not None and observed!=expected_prefix:
            checked['valid']=False;checked['issues'].append(dict(code='frozen_prefix_mismatch',expected=expected_prefix,actual=observed))
    except Exception as exc:
        trace=factory.trace
        try:checked=_checked(trace)
        except Exception as checker_exc:checked=dict(valid=False,issues=[dict(code='incomplete_trace_checker_error',message=str(checker_exc))])
        checked['valid']=False;checked['issues'].append(dict(code='counterfactual_execution_error',message=str(exc)))
        observed=digest(prefix_payload(trace,boundary['tick'])) if boundary is not None else None
        error=dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc())
    if boundary is not None:
        trace['provenance'].update(kind='offline_one_tick_counterfactual_execution',
            disclosure='Full measured simulation on one fixed tape; action chosen by offline audit, not deployed clairvoyant policy',
            forced_tick=boundary['tick'],forced_selected=list(selected))
    trace['validation']=checked
    result=dict(valid=checked['valid'],issues=checked['issues'],metrics=trace.get('metrics'),
        objective=rank(trace['metrics']) if 'metrics' in trace else None,
        selected=list(selected) if selected is not None else None,forced_boundary=deepcopy(record),
        prefix_sha256=observed,error=error,
        physical_instance_sha256=digest(instance),checker_sha256=hashes()['stage2/check.py'])
    if trace_path:
        path=Path(trace_path);path.parent.mkdir(parents=True,exist_ok=True)
        payload=json.dumps(trace,separators=(',',':')).encode()
        if path.exists():raise FileExistsError(path)
        path.write_bytes(gzip.compress(payload,mtime=0));result.update(trace_path=str(path),trace_sha256=hashlib.sha256(payload).hexdigest())
    result.update(wall_seconds=time.perf_counter()-started,cpu_seconds=time.process_time()-cpu)
    return result,trace


def controls(boundary,seed):
    from .qubo import select
    measured={}
    for method in ('qaoa','uniform','exact_random_tie'):
        started=time.perf_counter();cpu=time.process_time()
        result=select(boundary['candidates'],boundary['conflicts'],boundary['capacities'],method=method,seed=seed)
        measured[method]=dict(result=result,wall_seconds=time.perf_counter()-started,cpu_seconds=time.process_time()-cpu,
            cost_scope='Includes QUBO preprocessing and QAOA angle training/sampling when requested')
    return measured


def audit(teacher_path,output,max_boundaries=12):
    from .spec import build
    if not 1<=max_boundaries<=12:raise ValueError('Audit is limited to twelve coupled boundaries')
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=False)
    frozen=hashes();teacher_path=Path(teacher_path).resolve();teacher=json.loads(teacher_path.read_text())
    if teacher.get('policy_selection_role')!='training_only_last_update':raise ValueError('Training-only weight prior required')
    for name in ('stage2/engine.py','stage2/spec.py','stage2/check.py','instances/stage2/metaltech_pressure.json'):
        if teacher['source_hashes'].get(name)!=frozen[name]:raise ValueError('Prior physical source mismatch: '+name)
    for name in SOURCES:
        path=output/'source_snapshot'/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes((ROOT/name).read_bytes())
    protocol=dict(schema='stage2-offline-local-continuation-regret.v1',source_hashes=frozen,
        teacher=dict(path=str(teacher_path),sha256=hashlib.sha256(teacher_path.read_bytes()).hexdigest(),
            metadata={k:v for k,v in teacher.items() if k not in ('policy','actions')}),
        backend='ToolingFactory hard homes; no kitting, no QA guard; exact selector at every other tick',
        configs=[dict(orders=n,horizon=5760,profile='full') for n in (8,12)],seeds=[0,1,2],
        selection='First two chronological coupled boundaries per trace with2–4core and≤5totalbits',
        max_boundaries=max_boundaries,max_counterfactual_runs=16*max_boundaries,
        oracle='Offline realized-future continuation oracle among one-tick feasible core subsets; not causal deployment or global optimum',
        prefix_scope='Physical commitments/observations strictly before target tick; full target pool also hashed',
        objective=['unfulfilled_count','total_tardiness_ticks','total_cost'],validation_tapes=0,final_tapes=0)
    (output/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    baselines=[];boundaries=[];started=time.perf_counter();cpu=time.process_time()
    with (output/'rows.jsonl').open('x') as log:
        for config in protocol['configs']:
            index=teacher['configs'].index(config)
            weights=dict(teacher['actions'][teacher['policy']['actions'][index]]['weights'],
                selector='exact',worker_calendar=True,preposition=False,policy_seed=0)
            for seed in protocol['seeds']:
                if hashes()!=frozen:raise RuntimeError('Frozen regret audit source changed')
                instance=build(**config,seed=seed);base,trace=execute(instance,weights,trace_path=output/f'baseline-n{config["orders"]}-s{seed}.json.gz')
                baselines.append(dict(config=config,seed=seed,weights=weights,**base))
                eligible=[d for d in trace['qubo_decisions'] if d['result']['qubo']['couplers']>0 and
                    2<=d['result']['qubo']['core_variables']<=4 and d['result']['qubo']['variables']<=5][:2]
                for boundary in eligible:
                    if len(boundaries)>=max_boundaries:break
                    number=len(boundaries);prefix=digest(prefix_payload(trace,boundary['tick']))
                    subsets=feasible_subsets(boundary);alternatives=[]
                    for selected in subsets:
                        row,_=execute(instance,weights,boundary=boundary,selected=selected,expected_prefix=prefix,
                            trace_path=output/f'boundary-{number}-subset-{len(alternatives)}.json.gz')
                        row.update(boundary_id=number,config=config,seed=seed,tick=boundary['tick'],
                            pool_sha256=pool_sha(boundary),source_hashes=frozen)
                        alternatives.append(row);log.write(json.dumps(row)+'\n');log.flush()
                    measured=controls(boundary,seed=weights['policy_seed']+boundary['tick'])
                    measured['exact_linear']=dict(result=boundary['result'],wall_seconds=0.,
                        cost_scope='Exact action already measured in baseline full-run cost; no zero-cost claim')
                    by_action={tuple(sorted(r['selected'])):i for i,r in enumerate(alternatives)}
                    valid=[r for r in alternatives if r['valid']]
                    best=min(valid,key=lambda r:(tuple(r['objective']),tuple(r['selected']))) if valid else None
                    for method,control in measured.items():
                        idx=by_action.get(tuple(sorted(control['result']['selected'])))
                        control['enumerated_subset_index']=idx
                        evaluated=alternatives[idx] if idx is not None else None
                        if evaluated is None:control['error']='Control selected a core absent from complete feasible-subset enumeration'
                        elif best and evaluated['valid']:
                            control.update(continuation_objective=evaluated['objective'],
                                continuation_delta_vs_oracle=[a-b for a,b in zip(evaluated['objective'],best['objective'])],
                                same_unfulfilled_as_oracle=evaluated['objective'][0]==best['objective'][0])
                    result=dict(boundary_id=number,config=config,seed=seed,tick=boundary['tick'],weights=weights,
                        pool=pool_payload(boundary),pool_sha256=pool_sha(boundary),prefix_sha256=prefix,
                        original_qubo_summary=boundary['result']['qubo'],feasible_subsets=subsets,
                        counterfactuals=alternatives,controls=measured,observed_best=best and dict(selected=best['selected'],objective=best['objective']),
                        complete_valid_audit=base['valid'] and len(valid)==len(subsets) and all(c.get('enumerated_subset_index') is not None for c in measured.values()),
                        invalid_counterfactuals=sum(not r['valid'] for r in alternatives),
                        future_evaluation_wall_seconds=sum(r['wall_seconds'] for r in alternatives),
                        control_generation_wall_seconds=sum(c['wall_seconds'] for c in measured.values()))
                    boundaries.append(result)
                    (output/f'boundary-{number}.json').write_text(json.dumps(result,indent=2)+'\n')
    if hashes()!=frozen:raise RuntimeError('Frozen regret audit source changed')
    report=dict(**protocol,baselines=baselines,boundaries=boundaries,actual_boundaries=len(boundaries),
        actual_counterfactual_runs=sum(len(b['counterfactuals']) for b in boundaries),
        wall_seconds=time.perf_counter()-started,cpu_seconds=time.process_time()-cpu,
        all_audits_complete=all(b['complete_valid_audit'] for b in boundaries),
        limitation='Only first coupled pools and one-tick deviations under fixed subsequent exact policy; realized-future action selection is offline clairvoyance')
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


def main():
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--teacher',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--max-boundaries',type=int,default=12)
    a=p.parse_args();report=audit(a.teacher,a.output,a.max_boundaries)
    print(json.dumps({k:report[k] for k in ('actual_boundaries','actual_counterfactual_runs','all_audits_complete','wall_seconds')}))


if __name__=='__main__':main()
