"""Retain the selected TRAIN objective mechanism without outcome generalization."""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'output/stage2-search'
def read(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def trace(path):return json.loads(gzip.decompress(path.read_bytes()))
def prefix(t):
 return {key:[row for row in t[key]if row['tick'if key in ('events','energy')else'start']<420]
  for key in ('operations','moves','worker_moves','events','energy')}

def main():
 mechanism_path=BASE/'selector-first-divergence-training/mechanism-summary.json'
 ablation_path=BASE/'selector-reward-targeted-training/tick420-ablation.json'
 report_path=BASE/'selector-reward-targeted-training/report.json'
 mechanism=read(mechanism_path);ablation=read(ablation_path);report=read(report_path)
 checker_path=BASE/'selector-first-divergence-training/source_snapshot/stage2/check.py'
 spec=importlib.util.spec_from_file_location('objective_frozen_checker',checker_path)
 checker=importlib.util.module_from_spec(spec);sys.modules[spec.name]=checker;spec.loader.exec_module(checker)
 assert len(report['rows'])==48 and report['source_stable']
 assert all(row['valid']and not row['decode_mismatches']for row in report['rows'])
 summary=[]
 for group in report['summary']:
  rows=[row for row in report['rows']if row['policy_id']==group['policy_id']]
  assert len(rows)==group['runs']==12 and group['invalid']==0
  assert sorted(row['config']['seed']for row in rows)==group['seeds']
  assert sum(row['metrics']['shipped']for row in rows)==group['shipped']
  assert sum(row['metrics']['orders']for row in rows)==group['required']
  assert sum(row['metrics']['all_orders_fulfilled']for row in rows)==group['complete']
  assert all(row['seed_role'].startswith('TRAIN')for row in rows)
  summary.append(group)
 forks=[];example=None
 for row in mechanism['forced_results']:
  baseline_path=Path(next(item for item in mechanism['first_divergence']if item['seed']==row['seed'])['trace_paths']['exact'])
  forced_path=ROOT/row['trace_path'];baseline=trace(baseline_path);forced=trace(forced_path)
  assert hashlib.sha256(gzip.decompress(forced_path.read_bytes())).hexdigest()==row['trace_sha256']
  assert baseline['instance']==forced['instance'] and prefix(baseline)==prefix(forced)
  fresh_checks=[checker.check_trace(t)for t in (baseline,forced)]
  assert all(result['valid']and result['terminal_requirements_met']for result in fresh_checks)
  overridden=[q for q in forced['qubo_decisions']if q['result']['method']!='exact']
  assert len(overridden)==1 and overridden[0]['tick']==420
  assert all(sorted(q['result']['selected'])==sorted(q['committed'])for q in forced['qubo_decisions'])
  b=next(q for q in baseline['qubo_decisions']if q['tick']==420);f=overridden[0]
  for key in ('candidates','conflicts','capacities','offered_operations'):assert b[key]==f[key]
  if example is None:
   example=dict(tick=420,original_selected=b['result']['selected'],forced_selected=f['result']['selected'],
    candidates=[dict(candidate_id=b['candidates'][i]['id'],reward=b['candidates'][i]['reward'],operation=b['offered_operations'][i])for i in (0,7)],
    conflicts=b['conflicts'],capacities=b['capacities'],source_trace=str(baseline_path.relative_to(ROOT)),source_sha256=sha(baseline_path))
  forks.append(dict(seed=row['seed'],orders=baseline['metrics']['orders'],before_shipped=baseline['metrics']['shipped'],
   after_shipped=forced['metrics']['shipped'],before_cutoff_debt=baseline['metrics']['total_tardiness_ticks'],
   after_cutoff_debt=forced['metrics']['total_tardiness_ticks'],prefix_equal=True,override_tick=420,overrides=1,
   fresh_checks=fresh_checks,baseline_trace_path=str(baseline_path.relative_to(ROOT)),baseline_trace_sha256=sha(baseline_path),
   forced_trace_path=str(forced_path.relative_to(ROOT)),forced_trace_sha256=sha(forced_path)))
 original=next(row for row in ablation if row['policy_id']=='exact-original')
 no_batch=next(row for row in ablation if row['policy_id']=='exact-no-batch')
 assert original['conflicts']==no_batch['conflicts'] and original['capacities']==no_batch['capacities']
 assert abs(original['candidate_rewards']['C7']-no_batch['candidate_rewards']['C7']-100)<1e-9
 assert all(original['candidate_rewards'][key]==value for key,value in no_batch['candidate_rewards'].items()if key!='C7')
 out=dict(schema='stage2-objective-mechanism-evidence.v1',selection_role='Retrospective selected TRAIN failure cohort; no unbiased performance or held-out claim',
  example=example,forks=forks,targeted_summary=summary,ablation=ablation,
  physical_prefix_fields=list(prefix(baseline)),all_forced_commit_sets_match=True,
  final_tapes_used=0,trace_sha256_convention='gzip-file bytes; original report hash of decompressed JSON separately verified',
  source_hashes={str(p.relative_to(ROOT)):sha(p)for p in (mechanism_path,ablation_path,report_path,checker_path)},
  interpretation='Exact optimization of a local surrogate is not global factory optimization; one-tick forced forks are offline diagnostics, not a future-aware deployable controller')
 path=Path(__file__).with_name('report.json');path.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(dict(forks=len(forks),targeted_runs=48,physical_prefix_equal=True)))

if __name__=='__main__':main()
