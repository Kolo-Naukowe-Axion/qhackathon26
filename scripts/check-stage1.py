"""Check official Stage 1 exports against their inputs and retained measured samples."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def check_baselines(root=ROOT):
    from solver.artifacts import assess_samples,digest
    from solver.sequence import build_sequence_qubo
    from solver.stage1 import decode,exact_reference,validate
    root=Path(root)
    load=lambda p:json.loads((root/p).read_text())
    selection=load('output/stage1-selected.json');rows=[]
    for size,expected in [('2x2',4),('3x3',8)]:
        name='instance_'+size;instance=load('instances/'+name+'.json')
        official=load('schedule_'+size+'.json')
        directory=Path(selection['selected_runs'][name])
        model=load(directory/'model.json');run=load(directory/'run.json')
        saved=load(directory/'schedule.json');records=load(directory/'samples.json')
        assert official==saved and official['instance']==name
        assert model==build_sequence_qubo(instance)
        assert run['model_sha256']==digest(model) and run['instance_sha256']==digest(instance)
        assert run['accepted'] and run['method']==official['method'] and 'QAOA' in run['method']
        checked=assess_samples(instance,model,records)
        assert checked==records
        feasible=[r for r in checked if r['feasible']]
        selected=min(feasible,key=lambda r:(r['makespan'],-r['count'],r['bits']))
        assert official['schedule']==decode(model,selected['bits'])
        assert not validate(instance,official['schedule'],official['makespan'])
        assert official['makespan']==expected==exact_reference(instance)['makespan']
        raw=load(directory/'raw-counts.json')
        measured={tuple(int(v) for v in key[::-1]):count for key,count in raw.items()}
        assert measured=={tuple(r['bits']):r['count'] for r in checked}
        shots=sum(r['count'] for r in checked)
        assert shots==run['total_samples']==run['metadata']['shots']
        rows.append(dict(instance=name,makespan=expected,operations=len(official['schedule']),
            measured_shots=shots,variables=len(model['variables']),model_sha256=digest(model),
            schedule_sha256=hashlib.sha256((root/('schedule_'+size+'.json')).read_bytes()).hexdigest()))
    return dict(status='passed',rows=rows,training_runs=0,service_calls=0,
        scope='Official JSON, independent feasibility, exact reference, canonical QUBO and retained measured-sample equality; no new quantum execution.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():raise ValueError('Fresh output required')
    result=check_baselines();args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print([(r['instance'],r['makespan']) for r in result['rows']])
