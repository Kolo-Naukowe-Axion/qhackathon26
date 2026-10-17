"""Worker/machine CP relaxation: bounds only, never physical schedule witnesses."""
import argparse
from collections import defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from stage2.reference_multi import activities,validate_scope
from stage2.reference import shortest_path
from stage2.check import check_trace
from ortools.sat.python import cp_model
import ortools

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text())
def write(path,data):path.write_text(json.dumps(data,indent=2)+'\n')

def solve(instance,hint,seconds):
    validate_scope(instance);checked=check_trace(hint)
    if hint['instance']!=instance or not(checked['valid']and checked['all_orders_fulfilled']and checked['terminal_requirements_met']):raise ValueError('Physical upper-bound witness must be complete and checked on identical instance')
    began=time.perf_counter();ops,moves=activities(instance);by={o['id']:o for o in ops};indices={o['id']:k+1 for k,o in enumerate(ops)}
    model=cp_model.CpModel();h=instance['horizon_ticks'];starts={};ends={};attendance={};machines=defaultdict(list);workers=[]
    for o in ops:
        key=o['id'];p=o['duration'];rule=instance['attendance'][o['process']];d=p if rule['kind']=='full'else min(p,rule['ticks'])
        starts[key]=model.new_int_var(0,h-p,'start:'+key);ends[key]=starts[key]+p;attendance[key]=d
        machines[o['machine_id']].append(model.new_interval_var(starts[key],p,ends[key],'machine:'+key))
        workers.append(model.new_interval_var(starts[key],d,starts[key]+d,'worker:'+key))
    for intervals in machines.values():model.add_no_overlap(intervals)
    model.add_no_overlap(workers)
    predecessors=defaultdict(set);successors=defaultdict(set);loaded=lambda m:2+sum(t for _,_,t in shortest_path(instance,m['from'],m['to']))
    final=[]
    for m in moves:
        if m['target_op']:
            model.add(starts[m['target_op']] >= (ends[m['source_op']]if m['source_op']else 0)+loaded(m))
            if m['source_op']:predecessors[m['target_op']].add(m['source_op']);successors[m['source_op']].add(m['target_op'])
        else:final.append(ends[m['source_op']]+loaded(m))
    def ancestors(key):
        result=set(predecessors[key])
        for p in predecessors[key]:result.update(ancestors(p))
        return result
    ancestral={key:ancestors(key)for key in by};arcs={}
    for a in range(len(ops)+1):
        for b in range(len(ops)+1):
            if a==b:continue
            if a and b and ops[b-1]['id']in ancestral[ops[a-1]['id']]:continue
            if not a and b and predecessors[ops[b-1]['id']]:continue
            if a and not b and successors[ops[a-1]['id']]:continue
            bit=model.new_bool_var(f'worker:{a}:{b}');arcs[a,b]=bit
            if b:
                prior_hall=ops[a-1]['hall']if a else instance['workers'][0]['initial_hall']
                walk=instance['worker_travel_ticks']if prior_hall!=ops[b-1]['hall']else 0
                prior_end=starts[ops[a-1]['id']]+attendance[ops[a-1]['id']]if a else 0
                model.add(starts[ops[b-1]['id']]>=prior_end+walk).only_enforce_if(bit)
    model.add_circuit([(a,b,literal)for (a,b),literal in arcs.items()])
    for early,late in zip(instance['orders'],instance['orders'][1:]):model.add(starts[f'{early["id"]}/housing/1/op0']<=starts[f'{late["id"]}/housing/1/op0'])
    makespan=model.new_int_var(0,h,'last_shipping');model.add_max_equality(makespan,final)
    spec=importlib.util.spec_from_file_location('arithmetic_bound',ROOT/'output/stage2-search/multi-reference-bounds/build.py')
    bound_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(bound_module)
    is_full=all(rule['kind']=='full'for rule in instance['attendance'].values())
    arithmetic=(bound_module.certificate if is_full else bound_module.automatic_certificate)(instance)
    model.add(makespan>=arithmetic['lower_bound_ticks'])
    physical_upper=max(checked['metrics']['delivery_ticks'].values());model.add(makespan<=physical_upper)
    physical_ops={row['id']:row for row in hint['operations']if row['kind']=='process'}
    order=[0]+[indices[row['id']]for row in sorted(physical_ops.values(),key=lambda row:row['start'])]+[0]
    used=set(zip(order,order[1:]))
    for key,var in starts.items():model.add_hint(var,physical_ops[key]['start'])
    for edge,var in arcs.items():model.add_hint(var,int(edge in used))
    model.add_hint(makespan,physical_upper);model.minimize(makespan)
    error=model.validate()
    if error:raise ValueError(error)
    solver=cp_model.CpSolver();solver.parameters.max_time_in_seconds=seconds;solver.parameters.max_deterministic_time=seconds
    solver.parameters.num_search_workers=1;solver.parameters.random_seed=0
    status=solver.solve(model);has_solution=status in (cp_model.FEASIBLE,cp_model.OPTIMAL)
    schedule={key:solver.value(value)for key,value in starts.items()}if has_solution else None
    # Independently check only constraints actually retained in the relaxation.
    relaxed_check=None
    if schedule is not None:
        issues=[]
        for m in moves:
            if m['target_op']and schedule[m['target_op']]<(schedule[m['source_op']]+by[m['source_op']]['duration']if m['source_op']else 0)+loaded(m):issues.append('precedence:'+m['id'])
        for machine in instance['machines']:
            rows=sorted((schedule[o['id']],schedule[o['id']]+o['duration'])for o in ops if o['machine_id']==machine['id'])
            if any(a[1]>b[0]for a,b in zip(rows,rows[1:])):issues.append('machine:'+machine['id'])
        rows=sorted(ops,key=lambda o:schedule[o['id']]);prior_end=0;prior_hall=instance['workers'][0]['initial_hall']
        for o in rows:
            walk=instance['worker_travel_ticks']if prior_hall!=o['hall']else 0
            if schedule[o['id']]<prior_end+walk:issues.append('worker:'+o['id'])
            prior_end=schedule[o['id']]+attendance[o['id']];prior_hall=o['hall']
        relaxed_check=dict(valid=not issues,issues=issues,physical_factory_feasibility_established=False)
        if issues:raise AssertionError(relaxed_check)
    return dict(schema='tiny-multi-worker-machine-relaxation.v1',pumps=len(instance['orders']),
        status=solver.status_name(status),relaxation_optimum_proven=status==cp_model.OPTIMAL,
        relaxed_objective_ticks=solver.value(makespan)if has_solution else None,
        factory_lower_bound_ticks=solver.best_objective_bound,actual_physical_upper_bound_ticks=physical_upper,
        physical_factory_feasibility_established=False,relaxed_schedule_check=relaxed_check,
        retained=['Matched recipe/BOM precedence','Minimum physical loaded transfer lags including handling','Fixed machine processing capacity',
            'Single worker attendance and actual hall-transition duration','Identical-order relabeling symmetry','Separate guarded analytic bound'],
        optimistically_dropped=['Shared AGV sequencing and empty repositioning','Finite input reservations','Machine output blocking','Route congestion'],
        explanation='Removing these minimization constraints enlarges the schedule domain. Only the relaxed optimum or CP best bound is a factory lower bound; the relaxed objective is never a physical feasible comparator.',
        workers=1,wall_limit_seconds=seconds,deterministic_limit=seconds,seed=0,
        elapsed_seconds=time.perf_counter()-began,solver_wall_seconds=solver.wall_time,
        ortools_version=ortools.__version__,solver_response=solver.response_stats(),model_stats=model.model_stats(),
        worker_arc_variables=len(arcs),analytic_bound=arithmetic,relaxed_operation_starts=schedule)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--pumps',type=int,choices=(3,4),required=True)
    p.add_argument('--seconds',type=float,default=30);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.seconds<=0:raise ValueError('Positive budget required')
    a.output.mkdir(parents=True,exist_ok=False)
    instance_path=ROOT/f'output/stage2-search/multi-reference-pilot/n{a.pumps}-scale15/instance.json'
    hint_path=ROOT/('output/stage2-search/multi-reference-600/n3/automatic/cp-trace.json'if a.pumps==3 else'output/stage2-search/multi-reference-constructive/n4/trace.json')
    inputs={str(path.relative_to(ROOT)):sha(path)for path in (instance_path,hint_path,Path(__file__),ROOT/'stage2/reference_multi.py',ROOT/'output/stage2-search/multi-reference-bounds/build.py')}
    write(a.output/'manifest.json',dict(source_sha256=inputs,pumps=a.pumps,wall_limit_seconds=a.seconds,workers=1,scope='Bounds only; no physical relaxed witness claim'))
    report=solve(read(instance_path),read(hint_path),a.seconds);report['source_sha256']=inputs
    report['sources_stable']=inputs=={name:sha(ROOT/name)for name in inputs};write(a.output/'report.json',report)
    print(json.dumps({key:report[key]for key in ('pumps','status','relaxed_objective_ticks','factory_lower_bound_ticks','actual_physical_upper_bound_ticks','elapsed_seconds')}),flush=True)

if __name__=='__main__':main()
