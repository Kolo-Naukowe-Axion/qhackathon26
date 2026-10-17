"""Predeclared local planning-window comparisons with copied source provenance."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import resource
import sys
import time
import traceback

from .window_experiments import factory_cell, encode_plan
from .window_qubo import compile_qubo, solve_cp, solve_literal_qubo, digest
from .window_search import constructive, anneal, block_search


def save(path,value):
    Path(path).write_text(json.dumps(value,indent=2)+'\n')


def sources(output):
    root=Path(__file__).resolve().parents[1]
    names=['stage2/'+name for name in ('__init__.py','window_qubo.py','window_experiments.py','planning_quantum.py','window_search.py','window_campaign.py','spec.py','bounds.py')]
    names+=['instances/stage2/metaltech_pressure.json']
    hashes={}
    for name in names:
        data=(root/name).read_bytes();target=output/'sources'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        hashes[name]=hashlib.sha256(data).hexdigest()
    return root,hashes


def run(output,cases=((2,3,480,30),(3,4,720,30),(4,5,960,30)),seeds=(7,13,29),seconds=15,iterations=16,proposals=12000):
    output=Path(output);output.mkdir(parents=True,exist_ok=False);root,hashes=sources(output)
    began=time.perf_counter();cpu=time.process_time()
    protocol=dict(schema='stage2-window-development-comparison.v1',cases=cases,seeds=seeds,
        cp_seconds=seconds,cp_workers=4,literal_seconds=5,literal_max_couplers=150000,
        annealing_proposals_per_restart=proposals,annealing_restarts=2,
        block_methods=['uniform','qaoa','exact'],iterations=iterations,shots=512,angle_evaluations=48,
        initializer='Earliest-finish constructive, no CP hints; failed initialization remains a failed case',
        comparisons='Paired seeds and initial incumbents; wall/CPU budgets NOT equal. Exact-block is exponential classical control.',
        final_tapes_used=0,factory_rollouts=0,physical_qpu_calls=0,gpu_hours=0,
        source_hashes=hashes,runtime=dict(python=platform.python_version(),machine=platform.machine(),packages={n:importlib.metadata.version(n)for n in ('numpy','ortools')}))
    save(output/'protocol.json',protocol);results=[]
    for index,case in enumerate(cases):
        folder=output/f'case{index}';folder.mkdir();report=dict(case=case,case_index=index,methods=[])
        try:
            problem=factory_cell(*case);save(folder/'problem.json',problem)
            t=time.perf_counter();q=compile_qubo(problem);report.update(qubo=q.metadata(),compile_seconds=time.perf_counter()-t,problem_sha256=digest(problem))
            save(folder/'qubo.json',dict(linear=q.linear,quadratic=[[i,j,v]for(i,j),v in sorted(q.quadratic.items())],offset=q.offset,variables=q.variables,groups=q.groups))
            cp=solve_cp(problem,seconds,4);report['native_cp']=cp
            if 'plan'in cp:
                reference=encode_plan(q,cp['plan']);assert q.decode(reference)['valid']and q.energy(reference)==cp['objective']
            print(json.dumps(dict(case=case,variables=len(q.linear),couplers=len(q.quadratic),cp_status=cp['status'],cp_objective=cp.get('objective'))),flush=True)
            if len(q.quadratic)<=150000:report['literal_qubo']=solve_literal_qubo(q,5,4)
            initial=constructive(q);report['constructive']=initial;save(folder/'report.json',report)
            if initial['valid']:
                for seed in seeds:
                    result=anneal(q,seed,proposals,2,initial['bits']);report['methods'].append(result);save(folder/'report.json',report)
                    print(json.dumps(dict(case=case,seed=seed,method=result['method'],energy=result['energy'],valid=result['decoded']['valid'],seconds=result['wall_seconds'])),flush=True)
                    for method in ('uniform','qaoa','exact'):
                        result=block_search(q,initial['bits'],method,seed,iterations,512,48);report['methods'].append(result);save(folder/'report.json',report)
                        print(json.dumps(dict(case=case,seed=seed,method=result['method'],energy=result['energy'],valid=result['decoded']['valid'],seconds=result['wall_seconds'])),flush=True)
        except Exception as exc:
            report.update(error=str(exc),traceback=traceback.format_exc());save(folder/'report.json',report)
            print(json.dumps(dict(case=case,error=str(exc))),flush=True)
        results.append(report)
    stable=all(hashlib.sha256((root/name).read_bytes()).hexdigest()==value for name,value in hashes.items())
    summary=dict(protocol_sha256=digest(protocol),source_stable=stable,results=results,
        wall_seconds=time.perf_counter()-began,process_cpu_seconds=time.process_time()-cpu,
        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024))
    save(output/'summary.json',summary)
    manifest={str(p.relative_to(output)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted(output.rglob('*'))if p.is_file()}
    save(output/'manifest.json',manifest)
    if not stable:raise RuntimeError('Copied sources changed during run; results must remain developmental')
    return dict(output=str(output),cases=len(results),errors=sum('error'in r for r in results),wall_seconds=summary['wall_seconds'],process_cpu_seconds=summary['process_cpu_seconds'])


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--seconds',type=float,default=15)
    p.add_argument('--iterations',type=int,default=16);p.add_argument('--proposals',type=int,default=12000)
    a=p.parse_args();print(json.dumps(run(a.output,seconds=a.seconds,iterations=a.iterations,proposals=a.proposals),indent=2))
