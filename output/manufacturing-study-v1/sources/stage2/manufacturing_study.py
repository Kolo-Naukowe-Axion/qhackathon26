"""Local full-recipe campaign; no SDK, token, remote solver or QPU imports."""
import argparse
import hashlib
import json
from pathlib import Path
import time
from .manufacturing_cases import cases
from .column_parents import generate
from .operation_columns import operation_columns
from .operation_qubo import compile_operations
from .column_reference import solve_column_cp
from .manufacturing_penalty import tighten
from .window_qubo import compile_qubo,solve_cp,check_plan,digest


def save(path,value):path.write_text(json.dumps(value,indent=2)+'\n')


def export(q,directory,plan,domain):
    t=time.perf_counter()
    tightened,bits,certificate=tighten(q,plan,'Seeded list heuristic constructed before any CP reference')
    metadata=q.metadata()
    metadata.update(penalty=tightened.penalty,penalty_certificate=certificate,
                    proof=certificate['proof'],domain=domain)
    save(directory/'qubo.json',dict(linear=tightened.linear,
        quadratic=[[i,j,v]for(i,j),v in sorted(tightened.quadratic.items())],
        offset=tightened.offset,groups=tightened.groups,variables=tightened.variables,metadata=metadata))
    save(directory/'witness.json',dict(plan=plan,bits=bits,checked=check_plan(q.problem,plan),
         energy=tightened.energy(bits),cp_teacher_used=False))
    return dict(**metadata,export_seconds=time.perf_counter()-t)


def run(output,probe=False):
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    root=Path(__file__).resolve().parents[1]
    names=['manufacturing_cases.py','manufacturing_penalty.py','manufacturing_study.py','window_pump.py','window_qubo.py','window_reduction.py','column_parents.py','operation_columns.py','operation_qubo.py','column_reference.py','column_qubo.py','trajectory_qubo.py','window_experiments.py','spec.py','bounds.py']
    hashes={}
    for name in names:
        path=root/'stage2'/name;target=output/'sources'/'stage2'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(path.read_bytes());hashes['stage2/'+name]=hashlib.sha256(path.read_bytes()).hexdigest()
    protocol=dict(cases=list(cases()),grid=30,origin=1440,raw_cp_seconds=10,raw_cp_workers=4,
        parent_attempts=48,parent_count=4,parent_seconds=8,column_cap=24,column_radius=240,
        pool_cp_seconds=5,direct_full_qubo_cases=['nominal-32','rush-and-outage-32'],
        direct_full_qubo_variable_guard=12000,source_hashes=hashes,
        selection='Fixed scenarios and budgets declared before outcomes; development study, not held-out final evaluation',
        scope='Complete full recipes in raw model; operation-column QUBO is explicitly restricted. Raw pruned QUBO compiled on two32-operation cases. References are classical. Quantum validation fixture remains separate.',
        veloxq_calls=0,physical_qpu_calls=0)
    save(output/'protocol.json',protocol)
    began=time.perf_counter();rows=[]
    for name,p in cases().items():
        directory=output/name;directory.mkdir();save(directory/'problem.json',p)
        print(json.dumps(dict(phase='start',case=name,operations=len(p['operations']))),flush=True)
        row=dict(case=name,operations=len(p['operations']),problem_sha256=digest(p))
        if probe:
            row['raw_reference']=solve_cp(p,seconds=5,workers=1)
        else:
            parents=generate(p,attempts=48,wanted=4,seed=7001,seconds=8)
            save(directory/'parents.json',parents)
            row['parent_generation']={k:v for k,v in parents.items()if k!='parents'}
            if parents['parents']:
                best=min(parents['parents'],key=lambda plan:check_plan(p,plan)['objective'])
                row['initial']=dict(check_plan(p,best),plan=best)
                columns,restriction=operation_columns(p,parents['parents'],cap=24,radius=240)
                save(directory/'columns.json',columns)
                t=time.perf_counter();q=compile_operations(p,columns);row['pool_build_seconds']=time.perf_counter()-t
                row['pool']=export(q,directory,best,'Restricted operation pool, all raw operations retained; not lossless raw-domain compression')
                row['restriction']=restriction
                ref=solve_column_cp(p,columns,seconds=5,workers=1,initial_plan=best)
                if 'plan'in ref:
                    checked=check_plan(p,ref['plan']);assert checked['valid']
                    assert q.energy(q.encode(ref['plan']))==ref['objective']
                row['pool_reference']=ref
                if name in protocol['direct_full_qubo_cases']:
                    full=directory/'full-domain';full.mkdir()
                    t=time.perf_counter();raw=compile_qubo(p,max_variables=12000,support_pruning=True)
                    row['full_domain_build_seconds']=time.perf_counter()-t
                    row['full_domain']=export(raw,full,best,'Complete declared grid30 assignment domain after exact support pruning; no candidate cap')
            else:
                row['initializer_failure']='No feasible list-schedule parent; no CP fallback or quantum run'
            row['raw_reference']=solve_cp(p,seconds=10,workers=4,initial_plan=row.get('initial',{}).get('plan'))
        ref=row['raw_reference']
        if 'plan'in ref:assert check_plan(p,ref['plan'])['valid']
        save(directory/'report.json',row);rows.append(row)
        print(json.dumps(dict(phase='complete',case=name,status=ref['status'],objective=ref.get('objective'),bound=ref.get('bound'),
             initial=row.get('initial',{}).get('objective'),bits=row.get('pool',{}).get('variables'),couplers=row.get('pool',{}).get('couplers'))),flush=True)
    assert all(hashlib.sha256((root/name).read_bytes()).hexdigest()==value for name,value in hashes.items())
    result=dict(schema='qfactoria-full-manufacturing-study.v1',protocol=protocol,rows=rows,
                wall_seconds=time.perf_counter()-began,source_stable=True,veloxq_calls=0,physical_qpu_calls=0)
    save(output/'report.json',result)
    save(output/'manifest.json',{str(p.relative_to(output)):hashlib.sha256(p.read_bytes()).hexdigest()for p in output.rglob('*')if p.is_file()})
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True);parser.add_argument('--probe',action='store_true');args=parser.parse_args()
    r=run(args.output,args.probe);print(json.dumps(dict(cases=len(r['rows']),wall_seconds=r['wall_seconds'])))
