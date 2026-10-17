from copy import deepcopy
import gzip,hashlib,json,math,time
from pathlib import Path
from stage2 import adaptive_recovery as a
from stage2 import sequential as seq
from stage2.recovery_routing import run
from stage2.spec import build
from stage2.check import check_trace
out=Path(__file__).parent;contexts=json.loads(Path('output/stage2-search/adaptive-recovery-contexts.json').read_text());sources=a.hashes();rows=[]
for context,actor in zip(contexts,(0,17,91)):
 t=time.perf_counter();instance=build(**context['config'],seed=0)
 action=next(i for i,w in enumerate(a.ACTIONS) if all(context['weights'].get(k)==v for k,v in w.items()))
 direct=run(instance,dict(context['weights'],policy_seed=actor),**context['solver_options'])
 controller=a.Controller(dict(kind='static',action=action),context['weights'],actor,True)
 actual=run(instance,context['weights'],controller,**context['solver_options'])
 keys=('operations','moves','worker_moves','events','energy','metrics','admission_history','algorithm_audit')
 matching={k:direct.get(k)==actual.get(k) for k in keys};assert all(matching.values()),matching
 checked=check_trace(actual,deepcopy(instance));assert checked['valid'] and checked['terminal_requirements_met']
 assert [r['tick'] for r in controller.trajectory]==list(range(0,5760,720))
 assert all(r['action']==action for r in controller.trajectory)
 assert sum(seq.trajectory_rewards([r['potential'] for r in controller.trajectory],-7.25))==-7.25
 payload=json.dumps(actual,separators=(',',':')).encode();path=out/f"static-equivalence-n{context['config']['orders']}-seed0-actor{actor}.json.gz";path.write_bytes(gzip.compress(payload,mtime=0))
 rows.append(dict(config=context['config'],actor_seed=actor,environment_seed=0,action=action,physical_and_algorithm_lists_equal=matching,macro_ticks=[r['tick'] for r in controller.trajectory],metrics=actual['metrics'],checker_valid=checked['valid'],terminal=checked['terminal_requirements_met'],trace_path=str(path),trace_sha256=hashlib.sha256(payload).hexdigest(),wall_seconds=time.perf_counter()-t))
assert a.hashes()==sources
(out/'direct-smoke.json').write_text(json.dumps(dict(source_hashes=sources,rows=rows),indent=2)+'\n');print(json.dumps(rows,indent=2))
