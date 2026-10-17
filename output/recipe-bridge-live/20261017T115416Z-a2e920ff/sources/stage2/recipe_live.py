"""Fresh local whole-recipe QAOA demonstration; no SDK or network clients."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
import uuid

from .assignment_qaoa import AssignmentSector, sample
from .column_parents import generate
from .column_qubo import compile_columns
from .column_reference import solve_column_cp
from .recipe_bridge import select_columns
from .window_qubo import check_plan, digest

ROOT=Path(__file__).resolve().parents[1]
CASES=('heat-outage-32','heat-lease-32')


def fresh_recipe(case, seed, cap=3):
    if case not in CASES or type(seed) is not int or not 0<=seed<=1_000_000 or type(cap) is not int or cap not in (2,3,4):
        raise ValueError('Listed recovery case, integer seed and component cap2/3/4 required')
    began=time.perf_counter()
    stamp=datetime.now(timezone.utc)
    directory=ROOT/'output'/'recipe-bridge-live'/(stamp.strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8])
    directory.mkdir(parents=True,exist_ok=False)
    names=['recipe_live.py','recipe_bridge.py','column_parents.py','column_qubo.py',
           'column_reference.py','trajectory_qubo.py','assignment_qaoa.py','window_qubo.py']
    sources={}
    for name in names:
        path=ROOT/'stage2'/name;target=directory/'sources'/'stage2'/name
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(path.read_bytes())
        sources['stage2/'+name]=hashlib.sha256(path.read_bytes()).hexdigest()
    problem=json.loads((ROOT/'output/manufacturing-recovery-v2'/case/'problem.json').read_text())
    protocol=dict(case=case,seed=seed,cap=cap,parent_seed=17021,parent_attempts=256,parent_wanted=64,
                  parent_seconds=12,anchor_policy='first_and_incumbent',
                  seed_scope='Seed varies angle optimization and sampling; constructor seed stays fixed17021',
                  layers=2,evaluations=64,shots=512,alpha=.25,source_hashes=sources,
                  problem_sha256=digest(problem),physical_qpu_calls=0,veloxq_calls=0,
                  scope='Fresh constructive candidates, restricted whole-recipe compilation and local QAOA. No quantum advantage claim.')
    (directory/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    parents=generate(problem,attempts=256,wanted=64,seed=17021,seconds=12)
    columns=select_columns(problem,parents['parents'],cap,'first_and_incumbent')
    q=compile_columns(problem,columns)
    start=time.perf_counter();sector=AssignmentSector.build(q,max_states=1_000_000)
    preparation=time.perf_counter()-start
    row=sample(sector,seed=seed,layers=2,evaluations=64,shots=512,alpha=.25)
    if row['decoded'].get('valid'):
        assert check_plan(problem,row['decoded']['plan'])['objective']==row['decoded']['objective']
    reference=solve_column_cp(problem,columns,seconds=5,workers=1,initial_plan=parents['parents'][0])
    best=min((check_plan(problem,p) for p in parents['parents']),key=lambda x:x['objective'])
    result=dict(schema='qfactoria-fresh-recipe-run.v1',fresh=True,created_utc=stamp.isoformat(),
                protocol=protocol,result=row,reference=reference,model=q.metadata(),
                best_constructive=best,constructor_seconds=parents['wall_seconds'],
                sector_preparation_seconds=preparation,elapsed_seconds=time.perf_counter()-began,
                local_artifact=str(directory.relative_to(ROOT)),physical_qpu_calls=0,veloxq_calls=0)
    for name,value in [('problem.json',problem),('parents.json',parents),('columns.json',columns),('result.json',result)]:
        (directory/name).write_text(json.dumps(value,indent=2)+'\n')
    (directory/'circuit.qasm').write_text(row['qasm'])
    assert all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h for name,h in sources.items())
    (directory/'manifest.json').write_text(json.dumps({str(p.relative_to(directory)):hashlib.sha256(p.read_bytes()).hexdigest()
        for p in directory.rglob('*') if p.is_file()},indent=2)+'\n')
    return result
