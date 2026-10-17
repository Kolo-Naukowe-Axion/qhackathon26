"""Extract saved DEVELOPMENT planning schedules; no solve, training or factory run."""
import gc
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent/'planning-data'
BASE=ROOT/'output/stage2-search'
sources={}

def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb')as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()

def read(path):
 path=Path(path);sources[str(path.relative_to(ROOT))]=sha(path)
 with path.open()as f:return json.load(f)

def verified(directory):
 manifest=read(directory/'manifest.json')
 for name,digest in manifest.items():
  assert sha(directory/name)==digest,(directory,name)
 protocol=read(directory/'protocol.json')
 for name,digest in protocol['source_hashes'].items():assert sha(directory/'sources'/name)==digest
 return protocol

campaign=BASE/'window-pump-campaign-mac-v1'
protocol=verified(campaign)
trajectory=BASE/'trajectory-master-mac-v2'
trajectory_protocol=verified(trajectory)
frozen=campaign/'sources/stage2/window_qubo.py'
spec=importlib.util.spec_from_file_location('frozen_planning_view_check',frozen)
check=importlib.util.module_from_spec(spec);sys.modules[spec.name]=check;spec.loader.exec_module(check)
cases=[]

def schedule(problem,label,plan,**metadata):
 checked=check.check_plan(problem,plan)
 return dict(label=label,plan=plan,check=checked,**metadata)

for i in range(4):
 directory=campaign/f'case{i}';r=read(directory/'report.json');p=read(directory/'problem.json')
 assert r['problem_sha256']==check.digest(p)
 cp=r['native_cp'];assert cp['check']['valid']
 plans=[schedule(p,'Native CP reference',cp['plan'],kind='cp',status=cp['status'],wall_seconds=cp['wall_seconds'])]
 initial=r['constructive']
 if initial['valid']:plans.append(schedule(p,'Classical initializer',initial['decoded']['plan'],kind='initializer',wall_seconds=initial['wall_seconds']))
 else:assert not r['methods']
 methods=[]
 for run in r['methods']:
  label=f"{run['method']} · seed {run['seed']}"
  saved=schedule(p,label,run['decoded']['plan'],kind='local',method=run['method'],seed=run['seed'],wall_seconds=run['wall_seconds'],process_cpu_seconds=run['process_cpu_seconds'])
  assert saved['check']['valid']==run['decoded']['valid']
  assert saved['check'].get('objective')==run['decoded'].get('objective')
  history=run.get('history',[])
  saved['local_calls']=len(history)
  saved['max_simulated_qubits']=max((h['free_bits']for h in history if h.get('quantum_algorithm_simulated')),default=0)
  saved['max_original_free_bits']=max((h.get('original_free_bits',h.get('free_bits',0))for h in history),default=0)
  saved['accepted_improvements']=sum(h.get('incumbent_energy_after',0)<h.get('incumbent_energy_before',0)for h in history)
  methods.append({k:v for k,v in saved.items()if k not in ['plan','check']})
  plans.append(saved)
 tr=read(trajectory/f'case{i}/report.json')
 assert tr['source_report_sha256']==sources[str((directory/'report.json').relative_to(ROOT))]
 master=None
 if 'master'in tr:
  columns=read(trajectory/f'case{i}/columns.json');assert check.digest(columns)==tr['master']['pool_sha256']
  for run in tr['quantum_runs']:
   plans.append(schedule(p,f"Trajectory {run['method']} p{run['layers']} · seed {run['seed']}",run['decoded']['plan'],kind='trajectory',
       method=run['method'],layers=run['layers'],seed=run['seed'],wall_seconds=run['wall_seconds'],process_cpu_seconds=run['process_cpu_seconds'],
       exact_hit_probability=run['exact_hit_probability'],sampled_exact_hits=run['sampled_exact_hits'],shots=run['shots'],qubits=run['free_bits']))
  master=dict(tr['master'],restricted_exact_objective=tr['restricted_exact_objective'],gap_to_cp_incumbent=tr['gap_to_full_cp_incumbent'],
      gap_to_cp_lower_bound=tr['gap_to_full_cp_bound'],parent_wall_seconds=tr['parent_wall_seconds'],parent_attempts=len(tr['parent_history']),
      checked_pattern_selections=tr['all_pattern_selections_checked'])
 domains=[check.assignments(p,op)for op in p['operations']]
 raw_assignment=sum(map(len,domains));raw_makespan=len({a['end']for d in domains for a in d})
 q=r['qubo'];red=q['reduction'];assert raw_assignment==red['before']and red['after']==q['assignment_variables']
 cases.append(dict(id=f'case{i}',pumps=r['case'][0],horizon=r['case'][1],grid=r['case'][2],problem=p,plans=plans,
     native_cp={k:v for k,v in cp.items()if k!='plan'},raw=dict(assignment_bits=raw_assignment,makespan_bits=raw_makespan,total_bits=raw_assignment+raw_makespan),
     support_pruned=dict(assignment_bits=q['assignment_variables'],makespan_bits=q['makespan_variables'],total_bits=q['variables'],couplers=q['couplers'],
       pair_checks=red['pair_checks'],pruning_wall_seconds=red['wall_seconds'],compile_seconds=r['compile_seconds'],removed=len(red['removed']),
       objective_used=red['objective_used'],incumbent_used=red['incumbent_used'],scope=red['scope']),
     initializer_valid=initial['valid'],initializer_attempts=len(initial.get('attempts',[])),methods=methods,trajectory=master,
     trajectory_error=tr.get('error'),parent_count=tr['parent_count']))
 del r,tr;gc.collect()

audit_dir=BASE/'window-circuit-audit-mac-v1';audit=read(audit_dir/'report.json')
assert audit['valid']and audit['circuits']==len(audit['rows'])
for j,row in enumerate(audit['rows']):
 ci=next(i for i,c in enumerate(protocol['cases'])if c==row['case'])
 path=audit_dir/f"case{ci}-{row['method']}-{row['block_index']}.qasm"
 assert sha(path)==row['qasm_sha256']and row['valid']
 audit['rows'][j]=dict(row,qasm_file=path.name)
integration_dir=BASE/'window-integration-mac-v1';integration_protocol=verified(integration_dir)
integration=read(integration_dir/'summary.json')
integration_rows=[]
for row in integration['rows']:
 assert row['valid']and row['physical_check']['valid']and row['identity_check']['valid']
 integration_rows.append(dict(seed=row['seed'],method=row['method'],valid=row['valid'],orders=row['metrics']['orders'],shipped=row['metrics']['shipped'],
    cutoff_deadline_debt=row['metrics']['total_tardiness_ticks'],wall_seconds=row['wall_seconds']))
setup_dir=BASE/'window-setup-costs-mac-v1';setup_protocol=verified(setup_dir);setup=read(setup_dir/'summary.json');assert setup['source_stable']
setup_rows=[dict(case=row['case'],variables=row['qubo']['variables'],couplers=row['qubo']['couplers'],
    cp_status=row['native_cp']['status'],cp_objective=row['native_cp']['objective'],cp_bound=row['native_cp']['bound'],
    check_valid=row['native_cp']['check']['valid'],compile_wall_seconds=row['compile_wall_seconds'])for row in setup['rows']]
assert all(r['check_valid']for r in setup_rows)
fine_dir=BASE/'window-fine-grid-mac-v1';fine_protocol=verified(fine_dir);fine=read(fine_dir/'summary.json')
assert fine['source_stable']
fine_rows=[]
for i,row in enumerate(fine['rows']):
 p=read(fine_dir/f'case{i}/problem.json');cp=row['native_cp']
 assert check.digest(p)==row['problem_sha256']and check.check_plan(p,cp['plan'])['valid']and cp['optimal']
 fine_rows.append(dict(case=row['case'],unary_assignment_bits_before_support=row['unary_assignment_bits_before_support'],
     cp={k:v for k,v in cp.items()if k!='plan'},qubo_built=False))
validation_dir=BASE/'window-soft-validation-mac-v1';validation_protocol=verified(validation_dir);validation=read(validation_dir/'summary.json')
assert validation['source_stable']and len(validation['rows'])==48
validation_rows=[]
for row in validation['rows']:
 assert row['valid']and row['physical_check']['valid']and row['identity_check']['valid']
 validation_rows.append(dict(seed=row['seed'],method=row['method'],orders=row['metrics']['orders'],shipped=row['metrics']['shipped'],
     cutoff_deadline_debt=row['metrics']['total_tardiness_ticks'],instance_sha256=row['instance_sha256'],valid=True))
validation_groups=[]
for method in validation_protocol['methods']:
 rs=[r for r in validation_rows if r['method']==method]
 assert sorted(r['seed']for r in rs)==validation_protocol['seeds']
 validation_groups.append(dict(method=method,environments=len(rs),valid=len(rs),mean_missing=math.fsum(r['orders']-r['shipped']for r in rs)/len(rs),
     mean_cutoff_debt=math.fsum(r['cutoff_deadline_debt']for r in rs)/len(rs)))
for seed in validation_protocol['seeds']:
 rs=[r for r in validation_rows if r['seed']==seed]
 assert len({r['instance_sha256']for r in rs})==1
 a,b=[next(r for r in rs if r['method']==method)for method in ('constructive','compressed_qaoa')]
 assert all(a[key]==b[key]for key in ('orders','shipped','cutoff_deadline_debt'))
mixer_dir=BASE/'trajectory-mixer-mac-v1';mixer_protocol=verified(mixer_dir)
mixer_audit_dir=BASE/'trajectory-circuit-audit-mac-v1';mixer_audit=read(mixer_audit_dir/'report.json')
assert mixer_audit['valid']and mixer_audit['circuits']==36
mixer_cases=[]
for i in range(3):
 report_path=mixer_dir/f'case{i}/report.json';report=read(report_path);c=cases[i]
 assert report['master']['pool_sha256']==c['trajectory']['pool_sha256']and report['master']['problem_sha256']==check.digest(c['problem'])
 results=[]
 for row in report['results']:
  assert row['physical_qpu_calls']==0 and row['shots']==mixer_protocol['shots']
  if row['decoded'].get('plan'):
   physical=check.check_plan(c['problem'],row['decoded']['plan'])
   if row['decoded']['valid']:assert physical['valid']
  else:assert not row['decoded']['valid']
  if row['energy']==row['conditional_exact_energy']:assert row['decoded']['valid']
  if row['label']in ('qaoa_xy','uniform_onehot'):assert row['makespan_invariant_leakage']<1e-14
  results.append({k:row[k]for k in ('label','layers','seed','shots','energy','conditional_exact_energy','exact_hit_probability','zero_penalty_probability',
      'makespan_invariant_leakage','angle_evaluations','sampled_exact_hits','wall_seconds','process_cpu_seconds','bits')if k in row}|dict(decoded_valid=row['decoded']['valid']))
  if row['label']in ('qaoa_x','qaoa_xy'):
   audited=next(a for a in mixer_audit['rows']if a['case']==f'case{i}'and a['method']==row['label']and a['layers']==row['layers']and a['seed']==row['seed'])
   assert audited['source_report_sha256']==sources[str(report_path.relative_to(ROOT))]and audited['valid']
 mixer_cases.append(dict(case_id=c['id'],master=report['master'],results=results))
for row in mixer_audit['rows']:
 name=f"{row['case']}-{row['method']}-p{row['layers']}-seed{row['seed']}.qasm"
 assert sha(mixer_audit_dir/name)==row['qasm_sha256'];row['qasm_file']=name
bundle=dict(schema='stage2-planning-development-view.v1',role='DEVELOPMENT / deterministic planning cell, not complete factory scheduling',cases=cases,
    protocol=protocol,trajectory_protocol=trajectory_protocol,circuit_audit=audit,
    integration=dict(protocol=integration_protocol,rows=integration_rows),setup_costs=dict(protocol=setup_protocol,rows=setup_rows,wall_seconds=setup['wall_seconds'],peak_rss_bytes=setup['peak_rss_bytes']),
    fine_grid=dict(protocol=fine_protocol,rows=fine_rows,wall_seconds=fine['wall_seconds'],peak_rss_bytes=fine['peak_rss_bytes']),
    soft_validation=dict(protocol=validation_protocol,rows=validation_rows,groups=validation_groups),
    mixer=dict(protocol=mixer_protocol,cases=mixer_cases,audit=mixer_audit),
    source_sha256=sources,exporter_sha256=sha(__file__),factory_runs=0,solver_runs=0,physical_qpu_calls=0)
OUT.mkdir(exist_ok=True)
(OUT/'evidence.json').write_text(json.dumps(bundle,indent=2)+'\n')
for row in audit['rows']:
 path=audit_dir/row['qasm_file'];(OUT/path.name).write_bytes(path.read_bytes())
for row in mixer_audit['rows']:
 path=mixer_audit_dir/row['qasm_file'];(OUT/path.name).write_bytes(path.read_bytes())
for path,digest in sources.items():assert sha(ROOT/path)==digest
assert sha(ROOT/'presentation/stage2/research/final-evidence.json')=='6a66d36b2ea032b773a2b550d8773c13a0c4ea3f1fab0ef3565894853746fd60'
print(json.dumps(dict(cases=len(cases),plans=sum(len(c['plans'])for c in cases),sources=len(sources),bytes=(OUT/'evidence.json').stat().st_size)))
