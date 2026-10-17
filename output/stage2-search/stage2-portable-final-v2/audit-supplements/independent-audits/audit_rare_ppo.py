"""Two declared posthoc schedule replays, preserving original remote artifacts."""
import argparse
from copy import deepcopy
import json
import math
from pathlib import Path
import time

from stage2 import final_eval as f
from stage2.check import check_trace
from stage2.identity_audit import audit_trace
from stage2.spec import build

NAMES=('ppo6-2026-16','static-matched18-16')
REMOTE='/home/iwosmu/qh26-stage2-20261016/results/postfreeze-rare-ppo-10062'


def close(a,b):
    if type(a)is dict:return type(b)is dict and set(a)==set(b)and all(close(v,b[k])for k,v in a.items())
    if type(a)is list:return type(b)is list and len(a)==len(b)and all(close(x,y)for x,y in zip(a,b))
    if type(a)is float:return type(b)in(int,float)and math.isclose(a,b,rel_tol=1e-9,abs_tol=1e-5)
    return a==b


def write(folder,name,value):
    with (folder/name).open('x')as stream:stream.write(json.dumps(value,indent=2)+'\n')


def prepare(folder):
    from stage2.compare_evaluations import load_evidence,select_rows
    root=Path('output/stage2-search');evidence=root/'final-downloaded/final-strong-cheap-6117508'
    m,e,reference=load_evidence(evidence);config=dict(orders=16,horizon=5760,profile='full')
    groups=[select_rows(m,e,name,config)for name in NAMES]
    maps=[{r['seed']:r for r in rows}for rows in groups]
    mismatches=sorted(seed for seed in maps[0]if not close(maps[0][seed]['metrics'],maps[1][seed]['metrics']))
    assert mismatches and mismatches[0]==10062
    assert all(maps[0][seed]['checker_metrics']['unfulfilled_orders']==maps[1][seed]['checker_metrics']['unfulfilled_orders']for seed in maps[0])
    tasks=f.tasks(m,Path(REMOTE));folder.mkdir(exist_ok=False);items=[]
    for name,mapping in zip(NAMES,maps):
        row=mapping[10062];task=next(t for t in tasks if t['method_id']==name and t['seed']==10062 and t['policy_seed']==900000)
        original=deepcopy(task);task.update(save_trace=True,trace_path=REMOTE+'/'+name+'-audit-witness.json')
        assert {k:v for k,v in task.items()if k not in('save_trace','trace_path')}=={k:v for k,v in original.items()if k not in('save_trace','trace_path')}
        write(folder,name+'-original-row.json',row);write(folder,name+'-task.json',task)
        items.append(dict(method_id=name,original_row_sha256=f.digest(row),original_task_sha256=f.digest(original),audit_task_sha256=f.digest(task)))
    declaration=dict(schema='stage2-posthoc-rare-ppo-declaration.v1',declared_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
        criterion='First ascending final seed where frozenPPO6-2026-16 and matched static18-16 full metrics differ at1e-9/1e-5 tolerance',
        seed=10062,actor_seed=900000,config=config,full_metric_mismatch_seeds=mismatches,
        missing_equal_all_256=True,comparisons=items,evidence=reference,
        global_index_sha256=f.file_hash(root/'final-frozen-bundle-v20p2/global-freeze-index.json'),
        source_hashes=m['source_hashes'],audit_source_sha256=f.file_hash(__file__),
        execution='Exactly2 originalf._execute tasks on frozenAxion runtime; onlysave_trace andtrace_path differ; no alternatepolicy/path/seed retry',
        scope='Posthoc diagnostic illustration only, excluded from all256-tape estimates and predeclared retainedtrace counts; no source/hyperparameter/policy tuning')
    write(folder,'declaration.json',declaration);return declaration


def first_diff(left,right):
    result=[]
    for key in('operations','moves','worker_moves','events','energy'):
        a=left[key];b=right[key]
        for index in range(max(len(a),len(b))):
            x=a[index]if index<len(a)else None;y=b[index]if index<len(b)else None
            if x!=y:
                ticks=[r.get('start',r.get('tick',r.get('pickup_tick',0)))for r in(x,y)if r is not None]
                result.append(dict(collection=key,index=index,tick=min(ticks),ppo=x,static=y));break
    return sorted(result,key=lambda item:(item['tick'],item['collection']))


def execute(folder):
    declaration=json.loads((folder/'declaration.json').read_text());assert f.file_hash(__file__)==declaration['audit_source_sha256']
    assert f.source_hashes()==declaration['source_hashes'];traces={};outcomes=[];started=time.perf_counter()
    for item in declaration['comparisons']:
        name=item['method_id'];task=json.loads((folder/(name+'-task.json')).read_text());original=json.loads((folder/(name+'-original-row.json')).read_text())
        assert f.digest(task)==item['audit_task_sha256']and f.digest(original)==item['original_row_sha256']
        row=f._execute(task);write(folder,name+'-audit-row.json',row)
        if not row['valid']or row.get('error'):raise ValueError('Replay failed; preserve evidence and stop without substitute')
        assert close(row['metrics'],original['metrics'])and close(row['checker_metrics'],original['checker_metrics'])
        trace=json.loads(Path(row['trace_path']).read_text());anchor=build(**row['config'],seed=10062)
        assert f.digest(anchor)==row['physical_instance_sha256']==original['physical_instance_sha256']
        checked=check_trace(trace,deepcopy(anchor));identity=audit_trace(trace,anchor)
        assert checked['valid']and checked['terminal_requirements_met']and identity['valid']and close(checked['metrics'],original['checker_metrics'])
        macro=[dict(tick=d['tick'],action_id=d['action_id'],weights=d['weights'])for d in trace['decisions']if d['tick']%720==0]
        inference=[]
        if name.startswith('ppo'):
            _,controller,_=f._controller(task['method'],task['config'],900000)
            for d in trace['decisions']:
                answer=controller(deepcopy(d['observation']));assert answer['action_id']==d['action_id']
                assert all(d['weights'][key]==value for key,value in answer['weights'].items())
            inference=controller.trajectory
        write(folder,name+'-macro-inference.json',dict(macros=macro,trajectory=inference))
        traces[name]=trace;outcomes.append(dict(method_id=name,valid=True,metrics_match_original=True,
            metrics=row['metrics'],checker_metrics=row['checker_metrics'],trace_path=Path(row['trace_path']).name,
            trace_sha256=row['trace_sha256'],macro_actions=macro,canonical_identity=identity))
    divergence=first_diff(traces[NAMES[0]],traces[NAMES[1]])
    result=dict(schema='stage2-posthoc-rare-ppo-result.v1',valid=True,posthoc_audit_only=True,
        declaration_sha256=f.file_hash(folder/'declaration.json'),seed=10062,actor_seed=900000,
        outcomes=outcomes,first_divergences=divergence,first_physical_divergence=divergence[0]if divergence else None,
        exactly_two_factory_replays=True,final_source_unchanged=f.source_hashes()==declaration['source_hashes'],
        wall_seconds=time.perf_counter()-started,audit_source_sha256=f.file_hash(__file__),scope=declaration['scope'])
    write(folder,'report.json',result);return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mode',choices=('declare','execute'));parser.add_argument('--folder',type=Path,required=True);args=parser.parse_args()
    result=prepare(args.folder)if args.mode=='declare'else execute(args.folder)
    print(json.dumps({k:v for k,v in result.items()if k not in('outcomes','source_hashes','first_divergences','first_physical_divergence')},indent=2))
