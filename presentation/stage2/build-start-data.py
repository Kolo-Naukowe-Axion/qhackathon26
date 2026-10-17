"""Small explanatory snapshot from retained evidence. No solver or factory calls."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent;sources={}
def read(name):
 p=ROOT/name;sources[name]=hashlib.sha256(p.read_bytes()).hexdigest();return json.loads(p.read_text())
f=read('presentation/stage2/research/final-evidence.json');s=read('presentation/stage2/planning-data/scaling.json')
assert f['status']=='complete'and f['completed_cohorts_verified']
selected=[]
for method in ['static-grid-12','cem6-2026-16','cem6-2026-24','selected-stretch-32']:
 g=next(g for g in f['groups']if g['method_id']==method and g['selected_frontier'])
 assert g['invalid']==0 and g['environment_tapes']==256 and g['audit_passed']
 selected.append(dict(method=method,orders=g['config']['orders'],horizon_hours=g['config']['horizon']/60,all_shipped=g['probability_all_orders_fulfilled'],mean_missing=g['metrics']['unfulfilled']['mean'],deadline_debt=g['metrics']['total_tardiness_ticks']['mean'],cpu_seconds=g['cost']['timings']['cpu_seconds']['weighted_actor_mean_environment'],environments=256))
mpc=[]
for method in ['mpc-4future-12','mpc-2future-16','mpc-4future-24']:
 g=next(g for g in f['groups']if g['method_id']==method)
 assert g['invalid']==0 and g['environment_tapes']==256
 mpc.append(dict(method=method,orders=g['config']['orders'],mean_missing=g['metrics']['unfulfilled']['mean'],all_shipped=g['probability_all_orders_fulfilled'],cpu_seconds=g['cost']['timings']['cpu_seconds']['weighted_actor_mean_environment']))
sector=read('output/stage2-search/operation-sector-blocks32-long-mac-v1/summary.json');assert sector['source_stable']and len(sector['runs'])==12
assert all(r['raw_check']and r['physical_qpu_calls']==0 for r in sector['runs'])
q=[r for r in sector['runs']if r['method']=='qaoa_xy'];proposal=[r for r in sector['runs']if r['method']=='proposal_only']
assert {(r['seed'],r['energy'])for r in q}=={(r['seed'],r['energy'])for r in proposal}
planning=[]
for c in sorted(s['contexts'],key=lambda c:c['operations']):
 planning.append(dict(operations=c['operations'],pumps=c['pumps'],grid=c['case']['grid'],horizon_minutes=c['case']['horizon'],status=c['raw_reference']['status'],lower=c['raw_reference']['bound'],upper=c['raw_reference']['objective'],pool_bits=c['operation_master']['variables'],pool_objective=c['operation_pool_reference']['objective']))
c=next(c for c in s['contexts']if c['operations']==32)
assert c['same_problem_time_indexed_qubo']['problem_sha256']==sector['master']['problem_sha256']
recipes=[dict(id=o['id'].replace('P01/',''),process=next(iter(o['durations'])) .rstrip('12'),predecessors=[p.replace('P01/','')for p in o['predecessors']],attendance=o['attendance'])for o in c['problem']['operations']if o['id'].startswith('P01/')]
a=read('instances/instance_2x2.json');b=read('instances/instance_3x3.json')
for name in ['docs/STAGE2_RESULTS.md','docs/SOLUTION_QUALITY.md','docs/STAGE2_PLANNING_CORE.md','stage2/README.md']:
 p=ROOT/name;sources[name]=hashlib.sha256(p.read_bytes()).hexdigest()
data=dict(schema='stage2-start-guide.v1',role='Explanation of retained evidence; no new results',stage1=dict(A=a,B=b),selected_classical=selected,mpc=mpc,quantum_scope=f['quantum_scope'],primary_contrasts=f['primary_contrasts'],planning=planning,recipe=recipes,sector=dict(max_qubits=max(r['qubits_max']for r in q),qaoa_end=[r['energy']for r in q],proposal_end=[r['energy']for r in proposal],initial=sector['best_parent_objective'],reference=sector['native_raw_reference']['objective'],physical_qpu_calls=0),source_sha256=sources,no_factory_runs=True,no_solver_runs=True)
(HERE/'start-data.json').write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps(dict(bytes=(HERE/'start-data.json').stat().st_size,sources=len(sources))))
