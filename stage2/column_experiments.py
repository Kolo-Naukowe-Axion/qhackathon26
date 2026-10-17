"""Start ambitious and step down: bounded multi-parent component-QUBO pilot."""
import argparse
import hashlib
import json
from pathlib import Path
import resource
import sys
import time
import traceback

from .window_campaign import sources,save
from .window_pump import pump_cell
from .window_qubo import solve_cp,solve_literal_qubo
from .column_parents import generate
from .column_qubo import compile_columns,component_columns


def run(output):
    output=Path(output);output.mkdir(parents=True,exist_ok=False);root,hashes=sources(output)
    for file in('trajectory_qubo.py','column_qubo.py','column_parents.py','column_experiments.py'):
        name='stage2/'+file;data=(root/name).read_bytes();(output/'sources'/name).write_bytes(data);hashes[name]=hashlib.sha256(data).hexdigest()
    protocol=dict(schema='stage2-component-column-development.v1',cases=[dict(jobs=n,horizon=h,grid=15,metric_setups=True)for n,h in((8,4320),(4,2880),(3,1920),(2,1440))],
        parent_attempts=64,wanted_parents=8,parent_seconds=30,raw_domain_cap=500000,raw_cp_max_operations=64,raw_cp_seconds=30,raw_cp_workers=4,
        literal_master_seconds=15,literal_master_workers=4,source_hashes=hashes,
        scope='New deterministic component-column research. Larger unconstrained pattern domain does not imply all combinations feasible. Pool restricted to generated trajectories. Full raw CP guard/unknown gap disclosed. No quantum run in this parent/master probe.')
    save(output/'protocol.json',protocol);results=[];began=time.perf_counter();cpu=time.process_time()
    for index,case in enumerate(protocol['cases']):
        folder=output/f'case{index}';folder.mkdir();report=dict(case=case)
        try:
            p=pump_cell(**case);save(folder/'problem.json',p);parents=generate(p,64,8,7001,30);report['parent_generation']=parents
            save(folder/'report.json',report)
            if len(p['operations'])<=64:report['native_raw_cp']=solve_cp(p,30,4)
            else:report['native_raw_cp']=dict(status='GUARDED_SKIP',reason='More than64 raw operations; complete raw gap unknown')
            if len(parents['parents'])<2:raise ValueError('Fewer than two feasible heuristic parents; retain failure, no CP fallback')
            columns=component_columns(parents['parents']);q=compile_columns(p,columns);report['master']=q.metadata()
            save(folder/'columns.json',columns);save(folder/'qubo.json',dict(linear=q.linear,quadratic=[[i,j,v]for(i,j),v in sorted(q.quadratic.items())],offset=q.offset,groups=q.groups,variables=q.variables,metadata=q.metadata()))
            anchors=[]
            for plan in parents['parents']:
                bits=q.encode(plan);decoded=q.decode(bits);assert decoded['valid']and q.energy(bits)==decoded['objective'];anchors.append(dict(energy=q.energy(bits),bits=bits))
            report['parent_anchors']=anchors;report['best_parent_objective']=min(a['energy']for a in anchors)
            result=solve_literal_qubo(q,15,4);report['literal_master']=result
            if result.get('optimal'):assert result['decoded']['valid']and result['energy']<=report['best_parent_objective']
            reference=report['native_raw_cp'];report['pool_vs_raw_incumbent_difference']=result.get('energy',0)-reference['objective']if 'energy'in result and 'objective'in reference else None
            print(json.dumps(dict(case=case,parents=len(anchors),raw_assignments=parents['raw_assignment_candidates'],master=q.metadata(),best_parent=report['best_parent_objective'],
                master_status=result['status'],master_energy=result.get('energy'),raw_status=reference['status'],raw_objective=reference.get('objective'))),flush=True)
        except Exception as exc:report.update(error=str(exc),traceback=traceback.format_exc());print(json.dumps(dict(case=case,error=str(exc))),flush=True)
        save(folder/'report.json',report);results.append(report)
    stable=all(hashlib.sha256((root/name).read_bytes()).hexdigest()==value for name,value in hashes.items())
    summary=dict(results=results,source_stable=stable,wall_seconds=time.perf_counter()-began,process_cpu_seconds=time.process_time()-cpu,
        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024));save(output/'summary.json',summary)
    save(output/'manifest.json',{str(p.relative_to(output)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted(output.rglob('*'))if p.is_file()})
    return {k:v for k,v in summary.items()if k!='results'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True);a=p.parse_args();print(json.dumps(run(a.output),indent=2))
