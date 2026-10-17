from pathlib import Path
import sys,json,gzip,hashlib,time
root=Path(__file__).resolve().parents[3]
frozen=root/'output/stage2-search/snapshots/v7-kitting'
sys.path.insert(0,str(frozen))
from stage2.spec import build
from stage2.kitting import run
from stage2.check import check_trace
out=Path(__file__).resolve().parent
source=json.loads((frozen/'manifest.json').read_text())
for name,expected in source['files'].items():
 if hashlib.sha256((frozen/name).read_bytes()).hexdigest()!=expected:raise RuntimeError('Frozen source changed: '+name)
tasks=json.loads((root/'output/stage2-search/strong-horizon-training-tasks.json').read_text())
rows=[];began=time.perf_counter()
for seed in range(8):
 task=next(t for t in tasks if t['config']['orders']==32 and t['config']['horizon']==14400 and t['config']['seed']==seed and '/prior16/' in t['policy_id'])
 trace=run(build(**task['config']),task['weights'],**task['solver_options'])
 checked=check_trace(trace);trace['validation']=checked
 assert checked['valid'] and checked['terminal_requirements_met'],checked
 path=out/f'n32-H14400-seed{seed}-witness.json.gz'
 with gzip.open(path,'wt') as stream:json.dump(trace,stream)
 rows.append(dict(seed=seed,task=task,trace_path=str(path),trace_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),metrics=trace['metrics'],checker=checked))
(out/'witness-report.json').write_text(json.dumps(dict(source_snapshot=source,rows=rows,wall_seconds=time.perf_counter()-began),indent=2)+'\n')
print(json.dumps([dict(seed=r['seed'],orders=r['metrics']['orders'],shipped=r['metrics']['shipped'],valid=r['checker']['valid']) for r in rows]))
