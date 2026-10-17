"""Export actual full-recipe study results for the production studio, no solves."""
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from stage2.window_qubo import check_plan,assignments,digest


def lower_bound(p):
    earliest={};ops={o['id']:o for o in p['operations']}
    while len(earliest)<len(ops):
        for oid,o in ops.items():
            if oid in earliest or not set(o['predecessors'])<=set(earliest):continue
            values=[]
            for a in assignments(p,o):
                lo=max([o['release']]+[earliest[pr]+min(p['transport_lags'][m][a['machine']]for m in ops[pr]['durations'])for pr in o['predecessors']])
                if a['start']>=lo:values.append(a['end'])
            if not values:raise ValueError('Empty precedence-relaxed domain')
            earliest[oid]=min(values)
    terminal=set(ops)-{pr for o in ops.values()for pr in o['predecessors']}
    tardy=sum(ops[i].get('weight',1)*max(0,earliest[i]-ops[i]['due'])for i in terminal)
    return dict(objective=(p['horizon']+1)*tardy+max(earliest.values()),makespan=max(earliest.values()),weighted_terminal_tardiness=tardy,
                scope='Independent precedence/unary-calendar relaxation; ignores shared resource contention. Not an optimality certificate unless it meets a checked upper bound.')


cases={};sources={}
for campaign in ['manufacturing-study-v1','manufacturing-recovery-v2']:
    folder=ROOT/'output'/campaign
    r=json.loads((folder/'report.json').read_text())
    sources[str((folder/'report.json').relative_to(ROOT))]=hashlib.sha256((folder/'report.json').read_bytes()).hexdigest()
    for row in r['rows']:
        name=row['case'];p=json.loads((folder/name/'problem.json').read_text())
        plans=[]
        if row.get('initial'):plans.append(dict(id='list',name='List heuristic · before QUBO',plan=row['initial']['plan'],check=check_plan(p,row['initial']['plan']),optimal=False))
        for key,label in [('raw_reference','Complete-model CP reference'),('pool_reference','Exact / bounded candidate-pool CP')]:
            ref=row.get(key,{})
            if ref.get('plan'):plans.append(dict(id=key,name=label,plan=ref['plan'],check=check_plan(p,ref['plan']),optimal=ref.get('optimal',False),bound=ref.get('bound'),wall_seconds=ref.get('wall_seconds')))
        assert plans and all(s['check']['valid']for s in plans)
        lb=lower_bound(p)
        for s in plans:assert lb['objective']<=s['check']['objective']
        cases[name]=dict(id=name,source=str((folder/name/'report.json').relative_to(ROOT)),problem=p,
             operations=len(p['operations']),pumps=len(p['operations'])//16,plans=plans,
             reference=row['raw_reference'],lower_bound=lb,pool=row.get('pool'),full_domain=row.get('full_domain'),
             pool_reference=row.get('pool_reference'),initializer_cost=row.get('parent_generation'),
             restriction=row.get('restriction'),quantum_executed=False,veloxq_executed=False)
full=ROOT/'output/manufacturing-full-recovery-v1/report.json'
if full.exists():
    r=json.loads(full.read_text());sources[str(full.relative_to(ROOT))]=hashlib.sha256(full.read_bytes()).hexdigest()
    for row in r['rows']:cases[row['case']]['full_domain']=row['model']
nominal=next(s for s in cases['nominal-32']['plans']if s['id']=='raw_reference')
for c in cases.values():
    if c['operations']==32:c['unchanged_nominal_plan_check']=check_plan(c['problem'],nominal['plan'])
anneal=ROOT/'output/manufacturing-anneal-pilot-v1/report.json'
pilot=json.loads(anneal.read_text())if anneal.exists()else None
if pilot:sources[str(anneal.relative_to(ROOT))]=hashlib.sha256(anneal.read_bytes()).hexdigest()
packets=ROOT/'output/manufacturing-packets-v1/report.json'
packet_report=json.loads(packets.read_text())if packets.exists()else None
if packet_report:sources[str(packets.relative_to(ROOT))]=hashlib.sha256(packets.read_bytes()).hexdigest()
result=dict(packets=packet_report,schema='qfactoria-production-studio.v1',cases=cases,source_sha256=sources,annealing_pilot=pilot,
            scope='Saved classical planning schedules of complete16-step pump recipes. Material transport is minimum lags; no AGV/buffer/power/quality/shipment simulation in this view. Larger physical-factory replay remains separate.',
            physical_qpu_calls=0,veloxq_calls=0)
(Path(__file__).parent/'data.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(cases=len(cases),source_files=len(sources))))
