"""Compact only a completed strict final_report; retain campaign partialness."""
import argparse
from datetime import datetime,timezone
from fractions import Fraction
import json
import math
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from stage2.compare_evaluations import load_evidence,select_rows,file_hash,digest
from stage2.final_eval import summarize

def same(left,right):
 if isinstance(left,dict):return isinstance(right,dict)and left.keys()==right.keys()and all(same(left[k],right[k])for k in left)
 if isinstance(left,list):return isinstance(right,list)and len(left)==len(right)and all(same(a,b)for a,b in zip(left,right))
 if isinstance(left,float):return type(right)in(int,float)and math.isclose(left,right,rel_tol=1e-12,abs_tol=1e-9)
 return type(left)is type(right)and left==right

def main():
 p=argparse.ArgumentParser();p.add_argument('--report',type=Path,required=True);p.add_argument('--accounting',type=Path);a=p.parse_args();directory=a.report.resolve()
 report_path=directory/'report.json';report=json.loads(report_path.read_text())
 assert report['schema']=='stage2-final-evidence-report.v1' and report['invalid_executions']==0
 groups=json.loads((directory/'all-groups.json').read_text());assert len(groups)==report['groups']
 sources={};manifests={};evaluations={};evaluation_hashes={};protocol=None
 def source(key,path):
  path=Path(path).resolve();sources[key]=dict(path=str(path.relative_to(ROOT)),sha256=file_hash(path))
 source('strict_final_report',report_path);source('all_groups',directory/'all-groups.json');source('frontier',directory/'preselected-frontier.json');source('exporter',__file__)
 for cohort,path in report['inputs'].items():
  m,e,ref=load_evidence(path);assert m['evaluation_role']=='final' and e['missing_or_invalid']==0 and e['expected_rows']==e['actual_rows']
  manifests[cohort]=m;evaluations[cohort]=e;evaluation_hashes[cohort]=file_hash(Path(path)/'evaluation.json')
  if protocol is None:protocol=m['protocol']['payload']
  assert protocol==m['protocol']['payload']
  rebuilt=summarize(e['rows'],m)
  for group in [g for g in groups if g['cohort']==cohort]:
   select_rows(m,e,group['method_id'],group['config'])
   computed=next(g for g in rebuilt if g['method_id']==group['method_id']and g['config']==group['config'])
   assert same(computed,group['summary']),'Reconstructed weighted summary differs'
  for name,item in ref['files'].items():source(cohort+'_'+name,item['path'])
 assert protocol['total_tapes']==256 and len(protocol['leaves'])==8
 selected={(g['cohort'],g['method_id'],digest(g['config']))for g in report['preselected_frontier']};assert len(selected)==8
 compact=[]
 for group in groups:
  cohort=group['cohort'];m=manifests[cohort];e=evaluations[cohort];s=group['summary'];sg=digest(m['source_hashes'])
  compact.append(dict(id=f'{cohort}:{group["method_id"]}:{group["config"]["orders"]}',cohort=cohort,method_id=group['method_id'],label=group['method_id'],config=group['config'],
   manifest_sha256=m['manifest_sha256'],evaluation_sha256=evaluation_hashes[cohort],source_group_sha256=sg,
   source_group_label=cohort+' / '+sg[:12],runtime_label=json.dumps(e['runtime'],sort_keys=True),actor_seeds=m['actor_seeds'],expected_rows=s['expected_rows'],actual_rows=s['rows'],
   environment_tapes=s['unique_environment_tapes'],invalid=s['invalid'],audit_passed=True,selected_frontier=(cohort,group['method_id'],digest(group['config']))in selected,
   probability_all_orders_fulfilled=s['probability_all_orders_fulfilled'],metrics=s['metrics'],cost=group['cost']))
 for group in compact:
  if group['selected_frontier']:
   measured=next(g for g in report['preselected_frontier']if g['cohort']==group['cohort']and g['method_id']==group['method_id']and g['config']==group['config'])
   group['exploratory_frontier_intervals']=measured['exploratory_frontier_intervals']
   path=ROOT/'output/stage2-search/final-primary-certificates'/group['method_id']/'report.json'
   if path.exists():
    cert=json.loads(path.read_text());assert cert['evaluation_role']=='final'and cert['protocol_sha256']==protocol['protocol_sha256']and cert['method_id']==group['method_id']and cert['config']==group['config']and cert['environment_tapes']==256
    assert abs(cert['weighted_mean_checked_missing']-group['metrics']['unfulfilled']['mean'])<1e-10
    source('primary_certificate_'+group['method_id'],path)
    group['primary_certificate']={k:v for k,v in cert.items()if k not in ('rows','source_evidence','source_hashes')}
 primary=[];paired=[]
 for contrast in report['comparisons']:
  path=directory/contrast['path'];source(contrast['id'],path);comparison=json.loads(path.read_text())
  assert same(comparison['metrics']['missing'],contrast['missing'])and same(comparison['metrics']['deadline_debt'],contrast['deadline_debt'])
  paired.append(contrast)
  if not contrast['primary_quantum']:continue
  interval=comparison['predeclared_primary_missing_interval'];assert interval==contrast['primary_interval']
  primary.append(dict(id=contrast['id'],label=contrast['left_method']+' → '+contrast['right_method'],metric='missing orders',predeclared=True,interval=interval))
 assert len(primary)==2
 q=[g for g in groups if g['cohort']=='quantum-stochastic'];assert q
 maxima=lambda key:max(g['cost']['qubo_maxima'].get(key,0)for g in q)
 assert all(g['cost']['qubo_literal_execution_totals']['physical_quantum_calls']==0 and g['cost']['qubo_literal_execution_totals']['simulated_over_5bit_calls']==0 for g in q)
 qscope=dict(max_simulated_qubits=maxima('max_actual_simulated_quantum_bits'),max_encoded_variables=maxima('max_total_bits'),
  classical_fallback_calls=sum(g['cost']['qubo_literal_execution_totals']['qaoa_oversize_classical_fallback_calls']for g in q),
  scope='Maxima and fallbacks refer to the completed stochastic comparison cohort; QAOA-named controllers include declared classical fallback. Other cohorts retain their own telemetry.')
 replays_path=Path(__file__).resolve().parent/'traces/final-first-replay-index.json';replays=json.loads(replays_path.read_text());source('predeclared_replays',replays_path)
 for row in replays:source('replay'+str(row['config']['orders'])+'_sidecar',ROOT/row['evidence_path'])
 annotations=[]
 proof_path=ROOT/'output/stage2-search/final-independent-audit/postfreeze-rare-ppo-10062/report.json'
 if proof_path.exists():
  proof=json.loads(proof_path.read_text());assert proof['valid']and proof['posthoc_audit_only']and proof['final_source_unchanged']and proof['exactly_two_factory_replays']
  m=manifests['strong-cheap'];e=evaluations['strong-cheap'];config=dict(orders=16,horizon=5760,profile='full')
  ppo=select_rows(m,e,'ppo6-2026-16',config);static=select_rows(m,e,'static-matched18-16',config)
  assert len(ppo)==len(static)==256
  assert {(r['seed'],r['policy_seed']):r['checker_metrics']['unfulfilled_orders']for r in ppo}=={(r['seed'],r['policy_seed']):r['checker_metrics']['unfulfilled_orders']for r in static}
  outcomes={r['method_id']:r for r in proof['outcomes']};p=outcomes['ppo6-2026-16'];b=outcomes['static-matched18-16']
  for outcome,originals in [(p,ppo),(b,static)]:
   assert outcome['valid']and outcome['metrics_match_original']
   original=next(r for r in originals if r['seed']==proof['seed']and r['policy_seed']==proof['actor_seed'])
   for key in ('unfulfilled_orders','terminal_deadline_debt_ticks','total_cost'):assert math.isclose(outcome['checker_metrics'][key],original['checker_metrics'][key],abs_tol=1e-5)
  actions=[]
  for decision in p['macro_actions']:
   action=decision['action_id'].split('-')[-1]
   if not actions or actions[-1]!=action:actions.append(action)
  source('posthoc_rare_ppo',proof_path)
  annotations.append(dict(method_id='ppo6-2026-16',scope_label='FINAL 256-TAPE PRIMARY COMPARISON / SEPARATE POSTHOC BEHAVIOR DIAGNOSTIC',
   primary_observation='At 16 orders, PPO and the matched static controller have identical missing-order outcomes on all 256 final environment tapes. This does not make their full behavior identical.',
   behavior_observation=f"In the selected posthoc tape {proof['seed']}, PPO changes actions {' → '.join(actions)}. Both controllers leave {p['checker_metrics']['unfulfilled_orders']} orders missing, but PPO cutoff debt is {p['checker_metrics']['terminal_deadline_debt_ticks']} versus {b['checker_metrics']['terminal_deadline_debt_ticks']} minutes, and model cost {p['checker_metrics']['total_cost']:.2f} versus {b['checker_metrics']['total_cost']:.2f}. The learned policy is not globally constant.",
   limit='This two-replay posthoc illustration is excluded from all 256-tape estimates and predeclared replay counts. It does not select or change a final policy; it shows rare different decisions with worse secondary outcomes on this tape.'))
 proof_view=None
 proof_view_path=Path(__file__).resolve().parent/'traces/posthoc-proof-replay-index.json'
 if proof_view_path.exists():
  proof_view=json.loads(proof_view_path.read_text());assert proof_view['posthoc_audit_only']and proof_view['excluded_from_estimates']and not proof_view['predeclared_first_tape']and proof_view['fresh_check_valid']and proof_view['identity_valid']
  assert proof_view['orders']==32 and proof_view['shipped']==31 and proof_view['necessary_missing_lower_bound']==proof_view['checked_missing_upper_bound']==1
  source('posthoc_proof_replay',proof_view_path)
  for name,record in proof_view['sources'].items():assert file_hash(ROOT/record['path'])==record['sha256'];source('posthoc_proof_'+name,ROOT/record['path'])
 cost=dict(measured_cpu_seconds=sum(e['measured_cpu_seconds']for e in evaluations.values()),allocated_cpu_hours=None,training_cpu_hours=None,gpu_hours=None,
  unmeasured_worker_failures=sum(e['unmeasured_worker_failures']for e in evaluations.values()),scope='Completed cohorts only, literal process CPU across all retained executions. Simulation includes MPC futures and local optimization; nested timers are not added again. Allocated scheduler and shared training costs await a separate ledger; missing values are not zero.')
 if a.accounting:
  accounting_path=a.accounting.resolve();accounting=json.loads(accounting_path.read_text());assert accounting['schema']=='stage2-final-research-accounting-snapshot.v1'
  assert accounting['inputs'][str(report_path.relative_to(ROOT))]==file_hash(report_path)
  assert abs(accounting['final_evaluation_literal_episode_cpu_hours']-cost['measured_cpu_seconds']/3600)<1e-8
  jobs=accounting['final_evaluation_jobs'];assert len(jobs)==10 and all(j['state']=='COMPLETED'and j['exit_code']=='0:0'and j['allocated_cpu_seconds']==j['allocated_cpus']*j['elapsed_seconds']for j in jobs)
  assert abs(sum(j['allocated_cpu_seconds']for j in jobs)/3600-accounting['final_evaluation_allocated_cpu_hours'])<1e-10
  for name,expected in accounting['inputs'].items():
   candidate=ROOT/name
   if name.endswith('/compute-ledger.json'):
    preserved=ROOT/'output/stage2-search/final-independent-audit/accounting-0122-ledger-snapshot.json'
    archived=Path(__file__).resolve().parent/'research'/('cost-ledger-'+accounting_path.stem+'.json')
    candidate=next((p for p in (preserved,archived,candidate)if p.is_file()and file_hash(p)==expected),candidate)
    assert file_hash(candidate)==expected,name
    # Preserve old as-of bytes even after the ongoing central ledger changes.
    archived.write_bytes(candidate.read_bytes());source('accounting_ledger_snapshot',archived)
   else:
    assert file_hash(candidate)==expected,name
    source('accounting_input_'+Path(name).stem,candidate)
  source('reconciled_accounting',accounting_path)
  cost.update(allocated_cpu_hours=accounting['final_evaluation_allocated_cpu_hours'],gpu_hours=accounting['recorded_gpu_hours'],research_accounting=accounting,
   scope='Final evaluation literal process CPU and allocated scheduler time are separate measurements. The final allocation is a subset of research allocation, never added twice; nested planning/check/inference timers are not additive. Shared training cost is not isolated as a separate metered total.')
 conditional=None
 conditional_root=ROOT/'output/stage2-search/final-conditional-leaves';conditional_path=conditional_root/'selected-and-mpc.json'
 if conditional_path.exists():
  conditional_source=json.loads(conditional_path.read_text());assert conditional_source['report_sha256']==file_hash(conditional_root/'report.json')
  conditional_groups=[g for g in conditional_source['groups']if g['method_id']in {'cem6-2026-16','mpc-2future-16','cem6-2026-24','selected-stretch-32'}];assert len(conditional_groups)==4
  for g in conditional_groups:
   assert g['published_overall_means_recovered']and len(g['leaves'])==8 and len(g['actor_seeds'])==1
   measured=next(x for x in compact if x['cohort']==g['cohort']and x['method_id']==g['method_id']and x['config']==g['config']);assert g['source_manifest_sha256']==measured['manifest_sha256']
   for i,l in enumerate(g['leaves']):
    assert l['environment_tapes']==32 and l['leaf_index']==i and l['true_probability']==protocol['leaves'][i]['probability']and l['outcomes']==protocol['leaves'][i]['outcomes']
    assert sorted(t['seed']for t in l['all_fulfilled_by_tape'])==sorted(protocol['leaves'][i]['seeds'])
   for key in g['exact_reweighted_means']:
    exact=sum(Fraction(*l['true_probability'])*Fraction(*l['exact_conditional_means'][key])for l in g['leaves']);assert exact==Fraction(*g['exact_reweighted_means'][key])
   assert math.isclose(g['true_probability_reweighted_means']['missing_orders'],measured['metrics']['unfulfilled']['mean'],abs_tol=1e-10)
  for name in ('report.json','selected-and-mpc.json','output-index.json'):source('conditional_'+Path(name).stem,conditional_root/name)
  conditional=dict(schema='stage2-final-conditional-view.v1',source_files_verified=True,no_new_factory_runs=True,groups=conditional_groups,scope=conditional_source['interpretation'])
 data=dict(schema='stage2-final-view.v1',status=report['cohort_scope'],completed_cohorts_verified=True,evaluation_role='final',source_files_verified=True,
  source_report_artifact_modified_utc=datetime.fromtimestamp(report_path.stat().st_mtime,timezone.utc).isoformat(),source_report_path=str(report_path.relative_to(ROOT)),
  completed_cohorts=sorted(report['inputs']),missing_cohorts=report['missing_cohorts'],sources=sources,protocol=protocol,groups=compact,primary_contrasts=primary,paired_contrasts=paired,method_annotations=annotations,proof_replay=proof_view,conditional_leaves=conditional,quantum_scope=qscope,cost_ledger=cost,replays=replays,
  audit_scope='Every retained group passes strict frozen manifest/rows/independent-metrics consistency checks; the two linked first-predeclared replays additionally receive fresh physical checks. Original reports retain all rows, costs and provenance.')
 out=Path(__file__).resolve().parent/'research/final-evidence.json';out.write_text(json.dumps(data,indent=2)+'\n');print(json.dumps(dict(output=str(out),groups=len(compact),cohort_scope=data['status'],sources=len(sources))))
if __name__=='__main__':main()
