from pathlib import Path
import sys,json,gzip,hashlib,time,concurrent.futures
sys.path.insert(0,str(Path.cwd()))
from stage2.advanced import run
from stage2.engine import Factory
from stage2.spec import build
from stage2.check import check_trace,check_paired_causality
OUT=Path('output/stage2-search/advanced-candidates-audit');OUT.mkdir(parents=True,exist_ok=True)
FILES=['stage2/advanced.py','stage2/engine.py','stage2/spec.py','stage2/check.py','stage2/dispatch.py']
def hashes():return {p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in FILES}
CONFIGS=[dict(orders=24,wip_limit=2,lease_calibration=True,mode='standard',selector='priority'),dict(orders=24,wip_limit=4,lease_calibration=True,mode='turbo',selector='priority'),dict(orders=12,wip_limit=3,lease_calibration=False,mode='eco',selector='greedy')]
VARIANTS=dict(baseline=dict(worker_calendar=False,preposition=False),advanced=dict(),free=dict(routing_free_buffers=True),eta=dict(routing_free_buffers=True,routing_estimate_finish=True),join=dict(routing_free_buffers=True,bom_priority='join'),critical=dict(routing_free_buffers=True,bom_priority='critical'),slack=dict(routing_free_buffers=True,bom_priority='slack'))
def group(task):
    config,variant=task;cfg=CONFIGS[config];weights={k:v for k,v in cfg.items() if k!='orders'};weights.update(VARIANTS[variant]);rows=[];traces=[]
    for seed in range(20,24):
        started=time.monotonic();trace=run(build(orders=cfg['orders'],seed=seed),weights);check=check_trace(trace);traces.append(trace)
        data=json.dumps(trace,separators=(',',':')).encode();name=f'c{config}-{variant}-s{seed}.json.gz'
        (OUT/name).write_bytes(gzip.compress(data,mtime=0))
        m=trace['metrics'];row=dict(config=config,variant=variant,seed=seed,weights=weights,valid=check['valid'],issues=check['issues'],shipped=m['shipped'],orders=m['orders'],tardiness=m['total_tardiness_ticks'],cost=m['total_cost'],wall_seconds=time.monotonic()-started,trace_file=name,trace_sha256=hashlib.sha256(data).hexdigest())
        rows.append(row)
    return dict(config=config,variant=variant,rows=rows,causality=check_paired_causality(traces))
if __name__=='__main__':
    before=hashes()
    for file in FILES:(OUT/Path(file).name).write_bytes(Path(file).read_bytes())
    (OUT/'audit_script.py').write_bytes(Path(__file__).read_bytes())
    groups=[];started=time.monotonic()
    with concurrent.futures.ProcessPoolExecutor(max_workers=4) as pool:
        futures=[pool.submit(group,(c,v)) for c in range(len(CONFIGS)) for v in VARIANTS]
        for future in concurrent.futures.as_completed(futures):
            g=future.result();groups.append(g)
            print(g['config'],g['variant'],[r['shipped'] for r in g['rows']],'valid',all(r['valid'] for r in g['rows']),'causal',g['causality']['valid'],flush=True)
            (OUT/'partial.json').write_text(json.dumps(groups,indent=2))
    result=dict(scope='All seeds are development/training evidence; no held-out claims',configs=CONFIGS,variants=VARIANTS,seeds=list(range(20,24)),source_before=before,source_after=hashes(),wall_seconds=time.monotonic()-started,groups=sorted(groups,key=lambda g:(g['config'],g['variant'])))
    result['source_stable']=result['source_before']==result['source_after'];(OUT/'report.json').write_text(json.dumps(result,indent=2));print('done',result['wall_seconds'],'source_stable',result['source_stable'],flush=True)
