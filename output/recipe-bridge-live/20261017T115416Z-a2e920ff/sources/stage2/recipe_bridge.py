"""Quantum recombination of complete manufacturing component trajectories.

All32 raw recipe operations survive. Classical constructive work supplies a
restricted domain; the quantum circuit searches cross-component combinations.
Reference solutions never generate or select candidate columns.
"""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import time

from .column_parents import generate
from .column_qubo import component_columns, compile_columns, subproblem
from .window_qubo import check_plan, digest


def select_columns(problem, parents, cap, anchor_policy='first_two'):
    """Retain first two parents; append earliest remaining complete components.

    Ordering uses only raw trajectory times/cost definitions. It never receives
    the pool optimum or a native reference plan. Caps are nested prefixes.
    """
    if len(parents) < 2 or cap < 2:
        raise ValueError('Two constructive parents and cap>=2 required')
    if any(not check_plan(problem, plan)['valid'] for plan in parents):
        raise ValueError('Every constructive parent must be whole-model valid')
    all_columns = component_columns(parents)
    if anchor_policy == 'first_and_incumbent':
        incumbent = min(parents, key=lambda plan: check_plan(problem,plan)['objective'])
        anchors = [parents[0], incumbent]
    else:
        anchors = parents[:2]
    base = component_columns(anchors)
    columns = {}
    for name, options in all_columns.items():
        kept = list(base[name])
        seen = {digest(option) for option in kept}
        candidates = [option for option in options if digest(option) not in seen]
        candidates.sort(key=lambda option: (max(r['end'] for r in option),
                        sum(r['start'] for r in option), digest(option)))
        columns[name] = deepcopy((kept + candidates)[:cap])
    return columns


def save(path, data):
    path.write_text(json.dumps(data, indent=2) + '\n')


def run(source, output, anchor_policy='first_two'):
    output.mkdir(parents=True, exist_ok=False)
    root = Path(__file__).resolve().parents[1]
    names = ['recipe_bridge.py','column_parents.py','column_qubo.py','column_reference.py',
             'window_qubo.py','trajectory_qubo.py','assignment_qaoa.py']
    hashes = {}
    for name in names:
        src = root/'stage2'/name
        dst = output/'sources'/'stage2'/name
        dst.parent.mkdir(parents=True,exist_ok=True)
        dst.write_bytes(src.read_bytes())
        hashes[name]=hashlib.sha256(src.read_bytes()).hexdigest()
    protocol = dict(cases=['heat-outage-32','heat-lease-32'], parent_attempts=256,
        parent_wanted=64,parent_seed=17021,parent_seconds=12,
        caps=[2,3,4],anchor_policy=anchor_policy,
        choice_rule=('First two raw constructive parents' if anchor_policy=='first_two' else 'First and best raw constructive parent; explicit incumbent preservation')+' then earliest component completion/time sum; nested prefixes',
        quantum=dict(layers=2,evaluations=64,shots=512,alpha=.25,seeds=[7,13,29]),
        controls=['exact native restricted pool','exact complete sector','best constructive parent','uniform_onehot','sa_onehot'],
        max_states=1_000_000,reference_seconds=5,cp_teacher_used=False,
        gate='Genuine restricted same-model recombination; no required advantage or best-parent improvement',
        source_hashes=hashes,remote_calls=0,
        development='Known recovery fixture; new raw constructive seeds; not held-out industrial instances',
        prior_probe='Existing four-parent lease component pool exact native optimum65790; exploratory0.295s reference diagnostic before this redesign; no plan used in generation')
    save(output/'protocol.json',protocol)
    began=time.perf_counter()
    prepared=[]
    for case in protocol['cases']:
        directory=output/case
        directory.mkdir()
        p=json.loads((source/case/'problem.json').read_text())
        save(directory/'problem.json',p)
        parents=generate(p,attempts=256,wanted=64,seed=17021,seconds=12)
        save(directory/'constructive-parents.json',parents)
        print(json.dumps(dict(case=case,parents=len(parents['parents']),phase='generated')),flush=True)
        if len(parents['parents'])<2:
            prepared.append((case,p,None,None,directory,parents))
            continue
        for cap in protocol['caps']:
            target=directory/f'cap-{cap}'
            target.mkdir()
            columns=select_columns(p,parents['parents'],cap,anchor_policy)
            save(target/'columns.json',columns)
            prepared.append((case,p,cap,columns,target,parents))
    # All candidate domains above are frozen before any reference is imported.
    from .assignment_qaoa import AssignmentSector,sample
    from .column_reference import solve_column_cp
    rows=[]
    for case,p,cap,columns,target,parents in prepared:
        if columns is None:
            rows.append(dict(case=case,gate_failure='Fewer than two constructive parents'))
            continue
        start=time.perf_counter()
        q=compile_columns(p,columns)
        compilation=time.perf_counter()-start
        save(target/'qubo.json',dict(linear=q.linear,quadratic=[[i,j,c]for(i,j),c in sorted(q.quadratic.items())],
                                    offset=q.offset,variables=q.variables,groups=q.groups,metadata=q.metadata()))
        reference=solve_column_cp(p,columns,seconds=5,workers=1,initial_plan=parents['parents'][0])
        row=dict(case=case,cap=cap,model=q.metadata(),compilation_seconds=compilation,reference=reference,
                 best_constructive=min((check_plan(p,plan)for plan in parents['parents']),key=lambda x:x['objective']),
                 first_constructive=check_plan(p,parents['parents'][0]),runs=[])
        save(target/'reference.json',reference)
        try:
            start=time.perf_counter()
            sector=AssignmentSector.build(q,max_states=1_000_000)
            row['sector_preparation_seconds']=time.perf_counter()-start
            row['sector_states']=len(sector.energies)
        except ValueError as error:
            row['gate_failure']=str(error)
            save(target/'report.json',row)
            rows.append(row)
            continue
        row['exact_sector_energy']=int(sector.energies.min())
        row['exact_ground_states']=int((sector.energies==sector.energies.min()).sum())
        row['feasible_states']=int((sector.energies<q.penalty).sum())
        if reference['status']=='OPTIMAL':
            assert reference['objective']==row['exact_sector_energy']
        # All sampled selected plans receive the original complete-model check.
        for method in ['qaoa_xy','uniform_onehot','sa_onehot']:
            for seed in [7,13,29]:
                result=sample(sector,method=method,seed=seed,layers=2,evaluations=64,
                              shots=512,alpha=.25,sweeps=256)
                decoded=result['decoded']
                if decoded.get('valid'):
                    checked=check_plan(p,decoded['plan'])
                    assert checked['valid'] and checked['objective']==decoded['objective']
                    result['whole_plan_check']=checked
                result['scope']='All32 original operations via restricted complete component trajectories; no outside operation omitted; classical candidate generation charged separately'
                save(target/f'{method}-{seed}.json',result)
                row['runs'].append({k:v for k,v in result.items()if k!='qasm'})
        save(target/'report.json',row)
        rows.append(row)
        print(json.dumps(dict(case=case,cap=cap,qubits=len(q.linear),sector_states=row['sector_states'],
                              reference=reference.get('objective'),best_parent=row['best_constructive']['objective'])),flush=True)
    report=dict(protocol=protocol,rows=rows,wall_seconds=time.perf_counter()-began,
                source_stable=all(hashlib.sha256((root/'stage2'/name).read_bytes()).hexdigest()==sha for name,sha in hashes.items()))
    save(output/'report.json',report)
    save(output/'manifest.json',{str(path.relative_to(output)):hashlib.sha256(path.read_bytes()).hexdigest()
                                 for path in output.rglob('*')if path.is_file()})
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=Path('output/manufacturing-recovery-v2'))
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--anchor-policy',choices=['first_two','first_and_incumbent'],default='first_two')
    args=parser.parse_args()
    run(args.source,args.output,args.anchor_policy)
