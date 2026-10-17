"""Bounded LOCAL development experiments for the complete planning-window QUBO.

No prior frozen final tapes, reports, controllers or snapshots are modified.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import platform
import random
import resource
import sys
import time

from .window_qubo import compile_qubo, solve_cp, solve_literal_qubo, digest


def tiny_problem():
    return dict(name='two-step exact compiler certificate', horizon=6, grid=2,
                machines={'M':dict(hall='A',available=[[0,6]])},
                workers={'W':dict(skills=['cut'],initial_hall='A',available=[[0,6]])},
                operations=[dict(id='a',durations={'M':2},skill='cut',attendance='full',release=0,due=4,predecessors=[]),
                            dict(id='b',durations={'M':2},skill='cut',attendance='full',release=0,due=4,predecessors=['a'])],
                transport_lags={'M':{'M':0}},worker_travel=1)


def factory_cell(jobs=2, steps=2, horizon=480, grid=30, origin=2160):
    """Hypothetical backlog cell using actual factory routes/durations/calendars.

    All selected housing components are still raw at the public window boundary.
    This is an explicitly separate cell, NOT an extraction from a measured run.
    Setups, tools, energy, QA randomness, heat batching and capacitated AGVs are
    omitted; transport supplies shortest loaded/handling lags only. Every one of
    the declared remaining timing/assignment constraints is compiled into QUBO.
    """
    from .spec import build
    from .bounds import shortest_costs
    if not 1<=jobs<=8 or not 1<=steps<=5:raise ValueError('Local development cell caps:8components,5steps')
    source=build(max(12,jobs),seed=0);recipe=source['recipes']['housing'][:steps]
    processes={s['process']for s in recipe}
    machines={m['id']:dict(hall=m['hall'],available=[[0,horizon]])for m in source['machines']if m['process']in processes}
    workers={}
    for w in source['workers']:
        active=[];begin=None
        for t in range(horizon+1):
            clock=(origin+t)%source['day_ticks'];lo,hi=w['daily_shift']
            legal=t<horizon and lo<=clock<hi and not any(a<=clock<b for a,b in w.get('breaks',[]))
            if legal and begin is None:begin=t
            if not legal and begin is not None:active.append([begin,t]);begin=None
        if active:
            workers[w['id']]=dict(skills=list(w['skills']),initial_hall=w['initial_hall'],available=active)
    distances=shortest_costs(source,lambda e:e['ticks'])
    operations=[]
    for ji in range(jobs):
        order=source['orders'][ji];prior=[]
        for k,step in enumerate(recipe):
            p=step['process'];mode='precision'if p=='QA'and order.get('precision_required')else'standard'
            a,b=source['modes'][p][mode]['duration_factor']
            durations={m['id']:math.ceil(Fraction(step['base_ticks']*a*m['duration_factor'][0],b*m['duration_factor'][1]))
                       for m in source['machines']if m['process']==p}
            release=max(0,order['release_tick']-origin);machine_release={}
            if not prior:
                machine_release={m:release+distances['RAW_A'][m]+source['transport']['load_ticks']+source['transport']['unload_ticks']for m in durations}
            rule=source['attendance'][p];oid=f'{order["id"]}/housing/step{k}'
            operations.append(dict(id=oid,durations=durations,skill=source['process_skills'][p],
                                   attendance=rule['kind'],start_attendance=rule.get('ticks',1),
                                   release=release,machine_release=machine_release,due=order['due_tick']-origin,predecessors=list(prior)))
            prior=[oid]
    handling=source['transport']['load_ticks']+source['transport']['unload_ticks']
    return dict(name=f'factory-derived hypothetical backlog:{jobs}housing×{steps}steps',horizon=horizon,grid=grid,
                machines=machines,workers=workers,operations=operations,
                transport_lags={a:{b:(0 if a==b else distances[a][b]+handling)for b in machines}for a in machines},
                worker_travel=source['worker_travel_ticks'],
                provenance=dict(factory_instance_sha256=digest(source),source_origin_minutes=origin,
                    actual_recorded_snapshot=False,remaining_recipe='housing prefix; terminal means end of declared prefix, not a shipped pump',
                    transport='Uncapacitated machine-dependent minimum lags and exact per-machine initial loaded/handling release',
                    excluded=['sequence-dependent setups','portable tools/service','energy','quality/recovery','finite buffers','capacitated AGV motion','heat batching'],
                    current_claim='Complete declared scheduling-cell QUBO, not lossless full-factory formulation or measured rollout improvement'))


def encode_plan(q,plan):
    bits=[0]*len(q.variables)
    for row in plan:
        matches=[i for i in q.groups[row['operation']]if all(q.variables[i][k]==row[k]for k in ('machine','worker','start','end','attended_end','hall'))]
        if len(matches)!=1:raise ValueError('Raw CP plan does not have exactly one compiler-domain assignment')
        bits[matches[0]]=1
    end=max(a['end']for a in plan)
    bits[next(i for i in q.groups['@makespan']if q.variables[i]['start']==end)]=1
    return bits


def run(output,jobs=2,steps=2,horizon=480,grid=30,seconds=15,workers=4,literal=True):
    if not 1<=workers<=8 or not 0<seconds<=120:raise ValueError('Local guard:1–8 solverworkers and <=120seconds per solver')
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    source_paths=[Path(__file__),Path(__file__).with_name('window_qubo.py'),Path(__file__).with_name('spec.py'),Path(__file__).with_name('bounds.py'),Path(__file__).resolve().parents[1]/'instances/stage2/metaltech_pressure.json']
    source={str(p):hashlib.sha256(p.read_bytes()).hexdigest()for p in source_paths}
    began=time.perf_counter();cpu=time.process_time();problem=factory_cell(jobs,steps,horizon,grid)
    buildstart=time.perf_counter();q=compile_qubo(problem);build_seconds=time.perf_counter()-buildstart
    (output/'problem.json').write_text(json.dumps(problem,indent=2)+'\n')
    coefficients=dict(linear=q.linear,quadratic=[[i,j,v]for(i,j),v in sorted(q.quadratic.items())],offset=q.offset,
                      variables=q.variables,groups=q.groups,metadata=q.metadata())
    (output/'qubo.json').write_text(json.dumps(coefficients,separators=(',',':'))+'\n')
    cp=solve_cp(problem,seconds,workers)
    anchor=None
    if 'plan'in cp:
        bits=encode_plan(q,cp['plan']);anchor=dict(energy=q.energy(bits),decoded=q.decode(bits),bits=bits)
        assert anchor['decoded']['valid']and anchor['energy']==cp['objective']
    literal_result=solve_literal_qubo(q,seconds,workers)if literal and len(q.quadratic)<=150000 else None
    if literal_result and literal_result.get('optimal')and cp.get('optimal'):
        assert literal_result['energy']==cp['objective']
        assert literal_result['decoded']['valid']
    stable=source=={str(p):hashlib.sha256(p.read_bytes()).hexdigest()for p in source_paths}
    if not stable:raise ValueError('Experiment source changed during execution; do not publish scores')
    report=dict(schema='stage2-local-planning-window-experiment.v1',problem_sha256=digest(problem),qubo=q.metadata(),
        compiler_wall_seconds=build_seconds,native_raw_cp=cp,cp_plan_encoded_into_qubo=anchor,literal_unconstrained_qubo=literal_result,
        runtime=dict(python=platform.python_version(),machine=platform.machine(),wall_seconds=time.perf_counter()-began,
                     process_cpu_seconds=time.process_time()-cpu,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)),
        source_hashes=source,sources_stable_during_run=stable,resource_caps=dict(solver_workers=workers,seconds_per_solver=seconds,literal_couplers_cap=150000,qubo_variable_cap=2500),
        final_tapes_used=0,factory_rollouts=0,physical_qpu_calls=0,gpu_hours=0,
        scope='New development scheduling-cell experiment; previous frozen final results untouched. CP grounding is not quantum advantage. No full-factory integration result yet.')
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    return dict(output=str(output),variables=len(q.variables),couplers=len(q.quadratic),native_status=cp['status'],native_objective=cp.get('objective'),
                literal_status=literal_result['status']if literal_result else'guarded_skip',literal_energy=literal_result.get('energy')if literal_result else None,
                wall_seconds=report['runtime']['wall_seconds'],peak_rss_bytes=report['runtime']['peak_rss_bytes'])


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--jobs',type=int,default=2);p.add_argument('--steps',type=int,default=2);p.add_argument('--horizon',type=int,default=480);p.add_argument('--grid',type=int,default=30)
    p.add_argument('--seconds',type=float,default=15);p.add_argument('--workers',type=int,default=4);p.add_argument('--no-literal',action='store_true')
    a=p.parse_args();print(json.dumps(run(a.output,a.jobs,a.steps,a.horizon,a.grid,a.seconds,a.workers,not a.no_literal),indent=2))


if __name__=='__main__':main()
