"""Resource/quality comparison for compact full-trajectory quantum masters."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import time
import traceback

from .window_campaign import save,sources
from .window_qubo import WindowQUBO,digest
from .window_search import constructive
from .planning_quantum import sample_block,energy_table
from .trajectory_qubo import columns_from_parents,compile_trajectory_qubo


def run(campaign,output,seeds=(7,13,29),attempts=64):
    campaign=Path(campaign);output=Path(output);output.mkdir(parents=True,exist_ok=False);root,hashes=sources(output)
    for name in ('trajectory_qubo.py','trajectory_experiments.py'):
        relative='stage2/'+name;data=(root/relative).read_bytes();(output/'sources'/relative).write_bytes(data);hashes[relative]=hashlib.sha256(data).hexdigest()
    protocol=dict(schema='stage2-trajectory-master-development.v1',source_campaign=str(campaign),seeds=seeds,parent_attempt_cap=attempts,
        parent_rule='First two distinct complete feasible randomized list schedules; no CP teacher, no objective-based parent selection',
        methods=['uniform','qaoa_p1','qaoa_p2'],shots=512,angle_evaluations=64,source_hashes=hashes,
        scope='Exact restricted-pool QUBO; compare full-model CP reference separately. Parent construction and reference costs are classical. No final tapes, physical QPU or GPU calls.')
    save(output/'protocol.json',protocol);began=time.perf_counter();cpu=time.process_time();results=[]
    for path in sorted(campaign.glob('case*/report.json')):
        folder=output/path.parent.name;folder.mkdir();report=dict(source_report_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),methods=[])
        try:
            prior=json.loads(path.read_text());problem=json.loads((path.parent/'problem.json').read_text());data=json.loads((path.parent/'qubo.json').read_text());meta=prior['qubo']
            raw=WindowQUBO(problem,data['variables'],data['groups'],data['linear'],{(i,j):v for i,j,v in data['quadratic']},data['offset'],meta['penalty'],meta['feasible_objective_upper_bound'],{})
            parents=[];history=[];start=time.perf_counter()
            for trial in range(attempts):
                row=constructive(raw,7001+trial*1009,'randomized');history.append(dict(trial=trial,valid=row['valid'],energy=row.get('energy'),scheduled=row.get('scheduled')))
                if row['valid']:
                    plan=row['decoded']['plan']
                    if all(digest(plan)!=digest(p)for p in parents):parents.append(plan)
                    if len(parents)==2:break
            report.update(case=prior['case'],parent_history=history,parent_wall_seconds=time.perf_counter()-start,parent_count=len(parents),native_raw_cp=prior['native_cp'],raw_qubo=meta)
            if len(parents)!=2:raise ValueError('No two distinct feasible heuristic parents; no hidden CP fallback')
            columns=columns_from_parents(problem,parents);q=compile_trajectory_qubo(problem,columns)
            save(folder/'problem.json',problem);save(folder/'columns.json',columns);save(folder/'qubo.json',dict(linear=q.linear,quadratic=[[i,j,v]for(i,j),v in sorted(q.quadratic.items())],offset=q.offset,metadata=q.metadata()))
            # Independent exhaustive raw checking for EVERY restricted selection,
            # before execution is verification, never exposed as sampler guidance.
            checked=0
            for choices in itertools.product((0,1),repeat=len(columns)):
                plan=[r for c,options in zip(choices,columns.values())for r in options];end=max(r['end']for r in plan)
                bits=list(choices)+[int(t==end)for t in q.makespans];decoded=q.decode(bits);energy=q.energy(bits)
                if decoded['valid']:assert energy==decoded['objective']
                else:assert energy>=q.penalty
                checked+=1
            report.update(master=q.metadata(),all_pattern_selections_checked=checked,quantum_runs=[])
            for seed in seeds:
                for method,layers in (('uniform',1),('qaoa',1),('qaoa',2)):
                    result=sample_block(q,list(range(len(q.linear))),{},method,seed,512,64,layers);result['layers']=layers;report['quantum_runs'].append(result)
            # Classical exact solution is explicit control, not QAOA initialization.
            table=energy_table(dict(linear=q.linear,quadratic=q.quadratic,offset=q.offset));optimum=int(table.min());report['restricted_exact_objective']=optimum
            fullref=prior['native_cp'];report['gap_to_full_cp_incumbent']=optimum-fullref['objective']if 'objective'in fullref else None
            report['gap_to_full_cp_bound']=optimum-fullref['bound']if 'bound'in fullref else None
            print(json.dumps(dict(case=report['case'],raw_bits=len(raw.linear),master_bits=len(q.linear),master_couplers=len(q.quadratic),pool_optimum=optimum,full_cp=fullref.get('objective'),
                full_cp_status=fullref['status'],parents_seconds=report['parent_wall_seconds'],sample_valid=sum(r['decoded']['valid']for r in report['quantum_runs']))),flush=True)
        except Exception as exc:report.update(error=str(exc),traceback=traceback.format_exc());print(json.dumps(dict(case=report.get('case'),error=str(exc))),flush=True)
        save(folder/'report.json',report);results.append(report)
    stable=all(hashlib.sha256((root/name).read_bytes()).hexdigest()==value for name,value in hashes.items())
    summary=dict(results=results,source_stable=stable,wall_seconds=time.perf_counter()-began,process_cpu_seconds=time.process_time()-cpu);save(output/'summary.json',summary)
    save(output/'manifest.json',{str(p.relative_to(output)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted(output.rglob('*'))if p.is_file()})
    return dict(output=str(output),cases=len(results),failures=sum('error'in r for r in results),source_stable=stable,wall_seconds=summary['wall_seconds'])


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--campaign',required=True);p.add_argument('--output',required=True);a=p.parse_args();print(json.dumps(run(a.campaign,a.output),indent=2))
