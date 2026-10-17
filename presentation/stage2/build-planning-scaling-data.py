"""Retained component-column/reference export. Local file checks only; no solves."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'output/stage2-search'
OUT=Path(__file__).resolve().parent/'planning-data/scaling.json';hashes={}
def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb')as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()
def read(path):
 hashes[str(path.relative_to(ROOT))]=sha(path)
 return json.loads(path.read_text())
def verify(name):
 directory=BASE/name;manifest=read(directory/'manifest.json');protocol=read(directory/'protocol.json')
 for file,digest in manifest.items():assert sha(directory/file)==digest,(name,file)
 for file,digest in protocol['source_hashes'].items():assert sha(directory/'sources'/file)==digest
 summary=read(directory/'summary.json');assert summary['source_stable']
 return directory,protocol,summary

history_dir,history_protocol,history_summary=verify('component-compact-reference-mac-v1')
raw_dir,raw_protocol,raw_summary=verify('component-compact-reference-mac-v2')
columns_dir,columns_protocol,columns_summary=verify('component-columns-mac-v1')
pool_dir,pool_protocol,pool_summary=verify('component-column-references-mac-v1')
module_path=raw_dir/'sources/stage2/window_qubo.py';spec=importlib.util.spec_from_file_location('planning_scaling_frozen_checker',module_path)
checker=importlib.util.module_from_spec(spec);sys.modules[spec.name]=checker;spec.loader.exec_module(checker)
contexts=[]
for i,summary in enumerate(raw_summary['results']):
 folder=raw_dir/f'case{i}';problem=read(folder/'problem.json');report=read(folder/'report.json');parent=read(folder/'initial-plan.json')
 if isinstance(parent,dict):parent=parent.get('plan',parent.get('decoded',{}).get('plan'))
 original_path=columns_dir/f'case{i}/report.json';original=read(original_path)
 pool_path=pool_dir/f'case{i}.json';pool=read(pool_path)
 assert report['source_report_sha256']==pool['source_report_sha256']==hashes[str(original_path.relative_to(ROOT))]
 cp=report['result'];master=original['master'];reference=pool['native_pool_cp']
 old=read(history_dir/f'case{i}/report.json');old_problem=read(history_dir/f'case{i}/problem.json')
 assert checker.digest(old_problem)==checker.digest(problem)
 assert checker.digest(problem)==master['problem_sha256']==pool['master']['problem_sha256']
 assert master['pool_sha256']==pool['master']['pool_sha256']
 assert cp['check']['valid']and reference['check']['valid']and reference['optimal']
 assert pool['improvement_over_best_parent']==0 and reference['objective']==report['best_parent_objective']==original['best_parent_objective']
 plans=[]
 for label,plan,objective in [('Complete raw-cell CP v2',cp['plan'],cp['objective']),('Best heuristic parent',parent,report['best_parent_objective']),('Rigid-pool CP optimum',reference['plan'],reference['objective']),('Earlier raw-cell CP v1',old['result']['plan'],old['result']['objective'])]:
  checked=checker.check_plan(problem,plan);assert checked['valid']and checked['objective']==objective
  plans.append(dict(label=label,plan=plan,check=checked))
 contexts.append(dict(id=f'scale{i}',pumps=report['case']['jobs'],operations=report['operations'],case=report['case'],problem=problem,plans=plans,
     raw_reference={k:v for k,v in cp.items()if k!='plan'},rigid_master=master,pool_reference={k:v for k,v in reference.items()if k not in ['plan','choices']},
     best_parent_objective=report['best_parent_objective'],prior_raw_reference={k:v for k,v in old['result'].items()if k!='plan'},parent_generation={k:v for k,v in original['parent_generation'].items()if not isinstance(v,(dict,list))},
     pool_excess_objective_interval=[reference['objective']-cp['objective'],reference['objective']-cp['bound']]))
negative=[]
for name in ['component-columns-enriched-mac-v1','component-columns-flexible-mac-v1','component-columns-flexible-mac-v2']:
 directory,protocol,summary=verify(name)
 for row in summary['results']:
  ref=row.get('native_pool_cp',{});master=row.get('master',{})
  negative.append(dict(campaign=name,pumps=row['case']['jobs'],cap=row.get('cap',protocol.get('per_group_cap')),variables=master.get('variables'),
      couplers=master.get('couplers'),status=ref.get('status'),optimal=ref.get('optimal'),parent=row.get('best_parent_objective'),
      pool_objective=ref.get('objective'),improvement_over_parent=row.get('improvement_over_best_parent'),error=row.get('error')))
operation_dir,operation_protocol,operation_summary=verify('operation-columns-mac-v1')
for i,c in enumerate(contexts):
 row=read(operation_dir/f'case{i}/report.json');problem=read(operation_dir/f'case{i}/problem.json');ref=row['native_pool_cp'];master=row['master']
 assert checker.digest(problem)==checker.digest(c['problem'])==master['problem_sha256']
 assert ref['optimal']and ref['objective']==ref['bound']and ref['check']['valid']
 checked=checker.check_plan(problem,ref['plan']);assert checked['valid']and checked['objective']==ref['objective']
 c['operation_master']=master;c['operation_pool_reference']={k:v for k,v in ref.items()if k not in ['plan','choices']}
 c['operation_pool_excess_interval']=[ref['objective']-c['raw_reference']['objective'],ref['objective']-c['raw_reference']['bound']]
 c['plans'].append(dict(label='Operation-pool CP optimum',plan=ref['plan'],check=checked))
refine_dir=BASE/'component-reference128-refine-mac-v1'
refine_manifest=read(refine_dir/'manifest.json');refine_protocol=read(refine_dir/'protocol.json')
for file,digest in refine_manifest.items():assert sha(refine_dir/file)==digest
for file,digest in refine_protocol['source_hashes'].items():assert sha(refine_dir/'sources'/file)==digest
refinement=read(refine_dir/'report.json');refine_problem=read(refine_dir/'problem.json')
assert refinement['source_stable']and refinement['protocol']==refine_protocol
c=contexts[0];ref=refinement['result']
assert checker.digest(refine_problem)==checker.digest(c['problem'])==refine_protocol['problem_sha256']
assert refine_protocol['source_report_sha256']==hashes[str((raw_dir/'case0/report.json').relative_to(ROOT))]
assert ref['hint_objective']==c['raw_reference']['objective']==refine_protocol['initial_objective']
checked=checker.check_plan(c['problem'],ref['plan']);assert checked['valid']and checked['objective']==ref['objective']
assert c['raw_reference']['bound']<=ref['bound']<=ref['objective']<=c['raw_reference']['objective']
c['compact_raw_reference']=c['raw_reference'];c['raw_reference']={k:v for k,v in ref.items()if k!='plan'}
c['plans'].append(c['plans'][0]);c['plans'][0]=dict(label='Latest raw-cell CP continuation',plan=ref['plan'],check=checked)
c['pool_excess_objective_interval']=[c['pool_reference']['objective']-ref['objective'],c['pool_reference']['objective']-ref['bound']]
c['operation_pool_excess_interval']=[c['operation_pool_reference']['objective']-ref['objective'],c['operation_pool_reference']['objective']-ref['bound']]
block_dir,block_protocol,block_summary=verify('operation-column-blocks128-mac-v1')
assert block_summary['master']['pool_sha256']==contexts[0]['operation_master']['pool_sha256']
assert len(block_summary['runs'])==len(block_protocol['seeds'])*len(block_protocol['methods'])
assert all(r['raw_check']and r['physical_qpu_calls']==0 for r in block_summary['runs'])
setup=read(BASE/'window-setup-costs-mac-v1/summary.json')
for c in contexts:
 matched=[row for row in setup['rows']if row['problem_sha256']==c['rigid_master']['problem_sha256']]
 if matched:
  assert len(matched)==1
  c['same_problem_time_indexed_qubo']={key:matched[0]['qubo'][key]for key in ('variables','couplers','problem_sha256')}
bundle=dict(schema='stage2-component-scaling-view.v1',role='DEVELOPMENT / complete declared deterministic cells, not full physical factory',contexts=contexts,
    protocols=dict(raw_reference=raw_protocol,prior_raw_reference=history_protocol,rigid_columns=columns_protocol,pool_reference=pool_protocol,operation_columns=operation_protocol,operation_blocks=block_protocol),negative_pool_probes=negative,
    operation_pool_cost={k:v for k,v in operation_summary.items()if k!='results'},operation_block_probe={k:v for k,v in block_summary.items()if k not in ['native_pool_reference','native_raw_reference']},
    raw_refinement=dict(protocol=refine_protocol,**{k:v for k,v in refinement.items()if k not in ['protocol','result']}),
    campaign_cost=dict(wall_seconds=raw_summary['wall_seconds'],process_cpu_seconds=raw_summary['process_cpu_seconds'],peak_rss_bytes=raw_summary['peak_rss_bytes'],
      scope='Peak RSS belongs to the whole four-size reference campaign, not a measured per-row peak. CPU time and wall time differ under four solver workers.'),
    prior_campaign_cost={k:v for k,v in history_summary.items()if k!='results'},
    source_sha256=hashes,checker_sha256=sha(module_path),exporter_sha256=sha(__file__),factory_runs=0,solver_runs=0,quantum_runs=0)
OUT.write_text(json.dumps(bundle,indent=2)+'\n')
for path,digest in hashes.items():assert sha(ROOT/path)==digest
print(json.dumps(dict(contexts=len(contexts),plans=sum(len(c['plans'])for c in contexts),source_files=len(hashes),bytes=OUT.stat().st_size)))
