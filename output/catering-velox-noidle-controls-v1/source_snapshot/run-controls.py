from pathlib import Path
import time,hashlib
from catering.contracts import load_bundle
from catering.conditioning import eliminate_idle,rescore_result
from catering.methods.classical import solve_qubo
from catering.build_meal_release import save,result_summary
out=Path('output/catering-velox-noidle-controls-v1')
if out.exists():raise ValueError('Fresh output needed')
out.mkdir();sources={}
for name in ['catering/conditioning.py','catering/methods/classical.py']:
 p=Path(name);target=out/'source_snapshot'/name;target.parent.mkdir(parents=True,exist_ok=True)
 target.write_bytes(p.read_bytes());sources[name]=hashlib.sha256(p.read_bytes()).hexdigest()
plan=dict(widths=[512,1024,2048],seeds=[2026,2027,2028],seconds=2,restarts=4,sweeps=100,
    formulation='no-idle-deletion.v1',initializer='Seeded random raw bits',repair=False,
    veloxq_calls=0,physical_qpu_calls=0)
save(out/'experiment-plan.json',plan)
rows=[]
for n in plan['widths']:
 b=load_bundle(f'output/catering-velox-scale-v3/scale-{n}-qubo.json');v=eliminate_idle(b)
 for seed in plan['seeds']:
  start=time.monotonic();r=solve_qubo(v,dict(wall_time_limit_s=2),dict(seed=seed,restarts=4,sweeps=100))
  wall=time.monotonic()-start;r=rescore_result(b,v,r)
  save(out/f'scale-{n}-seed{seed}.json',r)
  row=dict(width=n,solver_variables=len(v['linear']),seed=seed,source_bundle_sha256=b['bundle_sha256'],sampling_bundle_sha256=v['bundle_sha256'],whole_call_s=wall,**result_summary(b,r))
  rows.append(row);print({k:row[k] for k in ['width','seed','valid_returns','best_metrics']},flush=True)
save(out/'report.json',dict(**plan,rows=rows))
save(out/'manifest.json',dict(sources=sources,files={str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file()}))
