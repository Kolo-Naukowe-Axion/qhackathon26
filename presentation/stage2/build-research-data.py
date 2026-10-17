"""Freeze existing research artifacts for the isolated browser view; no reruns."""
import hashlib
import gzip
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent/'research'
OUT.mkdir(exist_ok=True)
sources={
 'grid':'output/stage2-search/axion-results/grid-v1-6116782/summary.json',
 'protocol':'output/stage2-search/axion-results/grid-v1-6116782/protocol.json',
 'quantum':'output/stage2-search/rank-quantum-final/summary.json',
 'rank_model':'output/stage2-search/rank-probe/sat-only-final/structural-four-bit-model.json',
 'rank_sensitivity':'output/stage2-search/rank-sensitivity/report.json',
 'rank_three_model':'output/stage2-search/rank-three-final/structural/model.json',
 'rank_three_verification':'output/stage2-search/rank-three-final/structural/verification.json',
 'rank_three_quantum':'output/stage2-search/rank-three-final/qaoa/summary.json',
 'rank_three_root_audit':'output/stage2-search/rank-three-root-audit.json',
 'tooling_selection':'output/stage2-search/tooling-selection/selection.json',
 'tooling_validation':'output/stage2-search/tooling-routing-validation16/report.json',
 'multi_reference':'output/stage2-search/multi-reference-summary/report.json',
 'reference_bound_extension':'output/reference-bound-extension/report.json',
 'reference_two_hour_audit':'output/stage2-search/final-independent-audit/reference-2h-6117555/report.json',
 'reference_two_hour_seal':'output/stage2-search/reference-2h-methodology-review/final-seal.json',
 'closeout_accounting':'output/stage2-search/final-compute-0316-summary.json',
 'tooling_replay':'presentation/stage2/traces/tool-homes-train0-12.evidence.json',
 'recovery_diagnostic':'output/stage2-search/recovery-viewer-evidence/report.json',
 'later_frontier':'output/stage2-search/frontier-viewer-evidence/report.json',
 'primary_quality':'output/stage2-search/quality-material-primary-bound/report.json',
 'primary_quality_seed6':'output/stage2-search/quality-material-primary-bound/n32-H14400-seed6-certificate.json',
 'primary_quality_audit':'output/stage2-search/quality-material-independent-audit/report.json',
 'objective_mechanism':'output/stage2-search/objective-viewer-evidence/report.json',
 'large_replay':'presentation/stage2/traces/large-train0-32-240h.evidence.json',
 'reward_confirmation':'output/stage2-search/reward-confirmation-viewer-evidence/report.json',
}
for name in ['automatic','compressed','full-attendance','dispatch-restricted']:
 sources['tiny_'+name]='output/stage2-search/tiny-reference-final/'+name+'/report.json'
bundle={'schema':'stage2-research-evidence.v1','sources':{},'data':{}}
for name,relative in sources.items():
 raw=(ROOT/relative).read_bytes();data=json.loads(raw)
 bundle['sources'][name]={'path':relative,'sha256':hashlib.sha256(raw).hexdigest()}
 if name=='protocol':data={k:v for k,v in data.items() if k!='tasks'}
 bundle['data'][name]=data
audit=bundle['data']['reference_two_hour_audit'];seal=bundle['data']['reference_two_hour_seal']
assert audit['valid']and seal['valid']and seal['audited_report_sha256']==bundle['sources']['reference_two_hour_audit']['sha256']
audit_dir=ROOT/'output/stage2-search/final-independent-audit/reference-2h-6117555'
for source,name,digest in [
 (audit_dir/'report.json','reference-2h-audit.json',seal['audited_report_sha256']),
 (audit_dir/'derived-normalized-witness.json','reference-2h-normalized-witness.json',seal['derived_witness_sha256']),
]:
 raw=source.read_bytes();assert hashlib.sha256(raw).hexdigest()==digest
 (OUT/name).write_bytes(raw)
bundle['data']['reference_two_hour_downloads']={'audit':'./research/reference-2h-audit.json','derived_witness':'./research/reference-2h-normalized-witness.json',
 'audit_sha256':seal['audited_report_sha256'],'derived_witness_sha256':seal['derived_witness_sha256']}
bounds=subprocess.check_output([sys.executable,'-m','stage2.bounds','--profile','full'],cwd=ROOT)
(OUT/'capacity-bounds.json').write_bytes(bounds)
bundle['data']['bounds']=json.loads(bounds)
bundle['sources']['bounds']={'path':'presentation/stage2/research/capacity-bounds.json',
 'sha256':hashlib.sha256(bounds).hexdigest(),'generated_by':'python -m stage2.bounds --profile full',
 'source_sha256':hashlib.sha256((ROOT/'stage2/bounds.py').read_bytes()).hexdigest()}
grid=bundle['data']['grid']
assert grid['completed']==grid['requested']==sum(row['runs']for row in grid['rows'])
assert sum(row['valid']for row in grid['rows'])==grid['completed']
assert all(row['valid']and row['terminal']for group in bundle['data']['tooling_validation']['groups']for row in group['rows'])
assert hashlib.sha256((ROOT/'presentation/stage2/traces/tool-homes-train0-12.json').read_bytes()).hexdigest()==bundle['data']['tooling_replay']['trace_sha256']
primary=bundle['data']['primary_quality']
assert primary['all_primary_bounds_attained'] and len(primary['rows'])==8
horizon=bundle['data']['later_frontier']['horizon']
selected=min((row for row in horizon['groups']if row['orders']==primary['orders']and row['horizon_ticks']==primary['horizon_ticks']),
 key=lambda row:(row['mean_unfulfilled'],row['mean_tardiness_minutes'],row['mean_total_cost']))
measurements_path=next(path for path in horizon['source_sha256']if path.endswith('/measurements.jsonl'))
assert hashlib.sha256((ROOT/measurements_path).read_bytes()).hexdigest()==horizon['source_sha256'][measurements_path]
selected_rows={row['config']['seed']:row for line in (ROOT/measurements_path).read_text().splitlines()if line
 for row in [json.loads(line)]if row['policy_id']==selected['policy_id']and row['config']['orders']==primary['orders']}
for row in primary['rows']:
 trace_path=Path(row['trace_path']);raw=trace_path.read_bytes()
 assert hashlib.sha256(raw).hexdigest()==row['trace_sha256']
 trace=json.loads(gzip.decompress(raw));certificate_path=ROOT/row['certificate_path'];certificate_raw=certificate_path.read_bytes()
 assert hashlib.sha256(certificate_raw).hexdigest()==row['certificate_sha256']
 certificate=json.loads(certificate_raw)
 assert hashlib.sha256(json.dumps(trace['instance'],sort_keys=True,separators=(',',':')).encode()).hexdigest()==certificate['instance_sha256']
 assert trace['validation']['valid'] and trace['validation']['terminal_requirements_met']
 assert row['unfulfilled']==trace['metrics']['orders']-trace['metrics']['shipped']==certificate['unfulfilled_lower_bound']
 assert selected_rows[row['seed']]['metrics']['orders']-selected_rows[row['seed']]['metrics']['shipped']==row['unfulfilled']
 assert row['primary_optimum_attained'] and row['physical_valid'] and row['terminal_requirements_met']
audit=bundle['data']['primary_quality_audit']
assert audit['audited_source_sha256']==primary['source_hashes']['stage2/quality_material_bound.py']
assert audit['instance_sha256']==bundle['data']['primary_quality_seed6']['instance_sha256']
assert audit['all_adversarial_assumption_changes_rejected']
(OUT/'evidence.json').write_text(json.dumps(bundle,indent=2)+'\n')
print(json.dumps({'output':str(OUT/'evidence.json'),'training_runs':grid['completed'],'sources':len(bundle['sources'])}))
