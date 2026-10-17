"""CPU annealing controls on identical saved manufacturing QUBOs; no SDK."""
import argparse
from dataclasses import replace
import importlib.metadata
import json
from pathlib import Path
import time
import dimod
from dwave.samplers import SimulatedAnnealingSampler
from .manufacturing_io import load


def run(study,output,recovery_study=None):
    study=Path(study);output=Path(output);output.mkdir(parents=True,exist_ok=False)
    tasks=['nominal-32/full-domain','rush-and-outage-32/full-domain','heat-outage-32','nominal-64','nominal-128']
    protocol=dict(tasks=tasks,seeds=[101,103,107],reads=8,sweeps=256,
        penalties=['original_bound','checked_incumbent_bound'],initialization=['random','heuristic_witness'],
        scope='CPU simulated annealing development controls. Identical domains/feasible objectives; penalty variants intentionally change infeasible energies. No VeloxQ prediction or equal-runtime claim.',
        veloxq_calls=0,physical_qpu_calls=0)
    (output/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    rows=[]
    for task in tasks:
        source=Path(recovery_study)if recovery_study and task=='heat-outage-32'else study
        if not(source/task/'qubo.json').exists():
            rows.append(dict(task=task,status='SKIPPED',reason='Heuristic witness/model unavailable'));continue
        q,raw,witness=load(source/task)
        for penalty in protocol['penalties']:
            model=q
            if penalty=='original_bound':
                old=raw['metadata']['penalty_certificate']['original_penalty'];new=q.penalty
                model=replace(q,linear=[v+new-old for v in q.linear],
                    quadratic={ij:v//new*old for ij,v in q.quadratic.items()},offset=len(q.groups)*old,penalty=old)
            bqm=dimod.BinaryQuadraticModel(dict(enumerate(model.linear)),model.quadratic,model.offset,dimod.BINARY)
            for initial in protocol['initialization']:
                for seed in protocol['seeds']:
                    began=time.perf_counter()
                    kwargs=dict(num_reads=8,num_sweeps=256,seed=seed)
                    if initial=='heuristic_witness':kwargs.update(initial_states=dict(enumerate(witness['bits'])),initial_states_generator='tile')
                    samples=SimulatedAnnealingSampler().sample(bqm,**kwargs)
                    solver_seconds=time.perf_counter()-began
                    records=[]
                    for sample in samples.data(sorted_by=None):
                        bits=[int(sample.sample[i])for i in range(len(model.linear))]
                        energy=model.energy(bits)
                        if abs(energy-float(sample.energy))>1e-6:raise AssertionError('Sampler energy changed')
                        decoded=model.decode(bits)
                        records.append(dict(bits=bits,energy=energy,count=int(sample.num_occurrences),decoded=decoded))
                    valid=[r for r in records if r['decoded']['valid']]
                    best=min(valid,key=lambda r:r['decoded']['objective'])if valid else None
                    row=dict(task=task,method='CPU simulated annealing',penalty=penalty,initialization=initial,seed=seed,
                        returned_samples=sum(r['count']for r in records),feasible_samples=sum(r['count']for r in valid),
                        best_returned_objective=best['decoded']['objective']if best else None,
                        witness_objective=witness['energy'],
                        retained_policy_objective=min(witness['energy'],best['decoded']['objective'])if best else witness['energy'],
                        witness_retained=not best or best['decoded']['objective']>=witness['energy'],
                        solver_seconds=solver_seconds,end_to_end_seconds=time.perf_counter()-began,
                        records=records,veloxq_calls=0)
                    name=task.replace('/','-')+f'-{penalty}-{initial}-{seed}.json'
                    (output/name).write_text(json.dumps(row,indent=2)+'\n')
                    rows.append({k:v for k,v in row.items()if k!='records'})
        print(json.dumps(dict(task=task,runs=sum(r['task']==task for r in rows))),flush=True)
    result=dict(protocol=protocol,rows=rows,dimod=importlib.metadata.version('dimod'),sampler=importlib.metadata.version('dwave-samplers'),veloxq_calls=0)
    (output/'report.json').write_text(json.dumps(result,indent=2)+'\n');return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--study',required=True);p.add_argument('--output',required=True);p.add_argument('--recovery-study');a=p.parse_args();r=run(a.study,a.output,a.recovery_study);print(json.dumps(dict(runs=len(r['rows']))))
