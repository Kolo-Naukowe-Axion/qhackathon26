"""Read-only closeout consistency checks; no factory, solver or remote calls."""
from datetime import datetime,timezone
from pathlib import Path
import hashlib,json,re,subprocess,argparse

ROOT=Path.cwd();BASE=ROOT/'output/stage2-search';OUT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
docnames=('RESULTS','JUDGES_EXPLANATION','LIVE_SCRIPT','CONTROL_LAYERS');docs={n:ROOT/f'docs/STAGE2_{n}.md' for n in docnames}
links={}
for n,p in docs.items():
 bad=[]
 for t in re.findall(r'\]\(([^)]+)\)',p.read_text()):
  if '://' not in t and not (p.parent/t.split('#')[0]).resolve().exists():bad.append(t)
 assert not bad;links[n]=dict(sha256=sha(p),all_local_link_targets_exist=True)
seal=json.loads((BASE/'final-independent-audit/complete-audit-seal.json').read_text());assert seal['valid'] and seal['rows']==23552 and seal['original_retained_physical_replays']==592 and seal['method_context_groups']==74
portable=json.loads((BASE/'final-full-evidence-v2-all-trace-audits-receipt.json').read_text());assert portable['valid'] and portable['physical_replays']==592 and portable['no_pytorch_scipy_ortools_available']
source_manifest=json.loads((BASE/'snapshots/v20-final-current/manifest.json').read_text())
for n,h in source_manifest['files'].items():assert sha(ROOT/n)==h
assert len(source_manifest['files'])==40
cert=json.loads((BASE/'final-primary-certificates/selected-stretch-32/report.json').read_text());raw=sum(x['primary_attained_fraction']==1 for x in cert['rows']);assert raw==239 and abs(cert['weighted_primary_optimum_attainment']-.934375)<1e-12
allgroups=json.loads((BASE/'final-complete-report/all-groups.json').read_text());q=[x for x in allgroups if x['cohort']=='quantum-stochastic' and '-qaoa-' in x['method_id']];u=[x for x in allgroups if x['cohort']=='quantum-stochastic' and '-uniform-' in x['method_id']]
def total(gs,key):return sum(g['cost']['qubo_literal_execution_totals'].get(key,0) for g in gs)
quantum={k:total(q,k) for k in ('qaoa_calls','coupled_qaoa_calls','trivial_1bit_qaoa_calls','fallback_calls')}
assert quantum==dict(qaoa_calls=452338,coupled_qaoa_calls=174965,trivial_1bit_qaoa_calls=272854,fallback_calls=40455)
assert total(u,'fallback_calls')==39872
account=json.loads((BASE/'final-compute-0127-summary.json').read_text());assert round(account['final_evaluation_allocated_cpu_hours'],2)==70.42 and round(account['final_evaluation_literal_episode_cpu_hours'],2)==68.58 and account['recorded_gpu_hours']==account['physical_qpu_calls']==0
proof=json.loads((ROOT/'output/reference-bound-extension/report.json').read_text());assert proof['certificate']['lower_bound_ticks']==1482 and proof['minimum_checked_makespan_by_pumps']['4']==1567
serve=(ROOT/'scripts/serve.mjs').read_text();assert re.search(r'process\.env\.PORT\s*\|\|\s*4173',serve)
listener=subprocess.run(['lsof','-nP','-iTCP:4187','-sTCP:LISTEN'],capture_output=True,text=True)
assert listener.returncode==0 and '127.0.0.1:4187' in listener.stdout
live=docs['LIVE_SCRIPT'].read_text();spoken=live.split('## Spoken script')[1].split('Presenter note')[0];assert len(spoken.split())==334
inputs=['final-independent-audit/complete-audit-seal.json','final-complete-report/report.json','final-complete-report/all-groups.json','final-primary-certificates/selected-stretch-32/report.json','final-compute-0127-summary.json','final-full-evidence-v2-all-trace-audits-receipt.json']
result=dict(valid=True,as_of_utc=datetime.now(timezone.utc).isoformat(),source_sha256=sha(__file__),documents=links,input_seals={n:sha(BASE/n) for n in inputs},
 frozen40_source_files_unchanged=True,coverage=dict(original_execution_checks=23552,independent_fresh_numeric_anchors=23552,independent_retained_physical_replays=592,unretained_rows_not_freshly_replayed=22960,groups=74,clean_NumPy_only_portability_replays=592),
 primary_certificate_scope=dict(weighted_attainment=.934375,raw_attained_tapes=239,raw_tapes=256,raw_fraction=239/256,primary_only=True,secondary_gap_unknown=True,deterministic_keyed_tape_proof_requires_no_independence=True,ideal_uniform_quality_ceiling_requires_explicit_independence=True),
 quantum=quantum,uniform_fallback_calls=39872,quantum_advantage_demonstrated=False,quantum_timing_scope='CPU simulation,not physical hardware latency/noise/shotcost orcrosshostspeedup',
 proof_reference_interval=[1482,1567],proof_reference_scope='Guarded arithmetic makespan reference only; solverlower1466 and stochasticfactoryglobalgapunchanged;6117555pending',
 preview=dict(default_port=4173,observed_listening_port=4187,listener=listener.stdout,explicit_command='PORT=4187 npm run dev when port is free;otherwise use runningpreview/printedURL'),spoken_words=334,spoken_minutes_at_120_wpm=334/120,
 documentation_fixes_by_reviewer=['Judges/live clarify originalperrow23552 versus592retainedfreshreplays','Judges/live separate deterministic realized-draw proof from idealindependent-uniform probabilityassumption','Judges/live clarifydefault4173/active4187 and explicitPORT command','Live guides concurrentvisualdemonstration within334spokenwords≈2m47'],
 results_clarifications_applied_by_owner=['Change93.44%of tapes toprobability-weighted attainment93.44% (239/256raw)','Scope40,455fallbackcalls explicitlytoQAOAarms;uniform has39,872separatefallbacks','AddPORT=4187/printedURL note beforelocal4187links;default4173'],
 control_layers_material_errors_found=False,local_link_defects_found=False,no_changes_to_results_or_control_layers_by_reviewer=True,factory_runs=0,solver_calls=0,external_jobs=0,policy_changes=0,
 reproduction='PYTHONPATH=. .venv-stage2/bin/python output/stage2-search/closeout-consistency-methodology-0200/review-v2.py --output /private/tmp/new-closeout-review.json; choose a fresh output path. This datedlive-check asserts the current snapshot and4187listener, not a timeless offline server state')
parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=OUT/'report-v2.json');args=parser.parse_args()
with args.output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({k:result[k] for k in ('valid','as_of_utc','frozen40_source_files_unchanged','coverage','preview','control_layers_material_errors_found')},indent=2))
