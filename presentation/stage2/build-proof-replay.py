"""Retain one selected posthoc proof replay; never add it to final estimates."""
import gzip
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from stage2.check import check_trace
from stage2.identity_audit import audit_trace
from stage2.spec import build
from stage2.compare_evaluations import digest,file_hash,PHYSICAL_SOURCES

def main():
 root=ROOT/'output/stage2-search/final-independent-audit/nontrivial-proof-seed10020'
 report=json.loads((root/'report.json').read_text());declaration=json.loads((root/'declaration.json').read_text())
 assert all(report[k]for k in ('valid','posthoc_audit_only','final_method_unchanged','final_source_unchanged','metrics_match_original','checker_metrics_match_original','canonical_identity_valid','primary_optimum_attained'))
 assert report['declaration_sha256']==file_hash(root/'declaration.json')and report['original_row_sha256']==digest(json.loads((root/'original-row.json').read_text()))
 source=root/report['full_witness_path'];raw=source.read_bytes();assert file_hash(source)==report['full_witness_sha256']
 for name in PHYSICAL_SOURCES:assert declaration['source_hashes'][name]==file_hash(ROOT/name)
 instance=build(**declaration['config'],seed=report['seed']);assert digest(instance)==report['physical_instance_sha256']
 trace=json.loads(raw);checked=check_trace(trace,instance);identity=audit_trace(trace,instance)
 assert checked['valid']and checked['terminal_requirements_met']and identity['valid']
 assert checked['metrics']==report['independent_checker']['metrics']
 bound_path=root/'independently-reconstructed-necessary-bound.json';bound=json.loads(bound_path.read_text());assert bound['instance_sha256']==digest(instance)
 assert checked['metrics']['unfulfilled_orders']==bound['unfulfilled_lower_bound']==report['necessary_missing_lower_bound']==report['checked_missing_upper_bound']==1
 assert checked['metrics']['delivered_orders']==31 and checked['metrics']['delivered_orders']+checked['metrics']['unfulfilled_orders']==32
 evidence=next(r for r in bound['unavoidable_quality_evidence']if r['unit_id']=='P32/pump/1');assert evidence['necessary_scrap']and evidence['first_draw']<evidence['first_risk_floor']and evidence['repair_draw']<evidence['repair_risk_floor']
 out=Path(__file__).resolve().parent/'traces';name='posthoc-proof-10020-32-14400';compressed=gzip.compress(raw,mtime=0);(out/(name+'.json.gz')).write_bytes(compressed)
 sidecar=dict(schema='stage2-optional-replay-evidence.v1',label='POSTHOC AUDIT ONLY · tape 10020 · 32 required / 31 shipped · 240h',seed_role='POSTHOC AUDIT ONLY; selected after final outcomes for a nonzero certificate; excluded from 256-tape estimates and predeclared replay counts',horizon_scope='240h extra calendar time; fixed-tape primary optimum only, deadline debt/cost optimum unknown',source_path=str(source.relative_to(ROOT)),source_trace_sha256=report['full_witness_sha256'],trace_sha256=hashlib.sha256(compressed).hexdigest(),instance_sha256=digest(instance),certificate_path=str(bound_path.relative_to(ROOT)),certificate_sha256=file_hash(bound_path),fresh_independent_check=checked,checker_sha256=file_hash(ROOT/'stage2/check.py'),fresh_identity_audit=identity,metrics=trace['metrics'],operations=len(trace['operations']),moves=len(trace['moves']),activity_data_changed=False,secondary_optimality_gap=None,posthoc_audit_only=True,predeclared_first_tape=False)
 (out/(name+'.evidence.json')).write_text(json.dumps(sidecar,indent=2)+'\n')
 for suffix,source_path in [('declaration',root/'declaration.json'),('certificate',bound_path),('audit-report',root/'report.json')]:
  (out/(name+'.'+suffix+'.json')).write_bytes(source_path.read_bytes())
 sources={}
 for label,p in [('report',root/'report.json'),('declaration',root/'declaration.json'),('necessary_bound',bound_path),('original_row',root/'original-row.json'),('retained_declaration',out/(name+'.declaration.json')),('retained_certificate',out/(name+'.certificate.json')),('retained_report',out/(name+'.audit-report.json')),('sidecar',out/(name+'.evidence.json')),('exporter',Path(__file__))]:sources[label]=dict(path=str(p.relative_to(ROOT)),sha256=file_hash(p))
 index=dict(schema='stage2-posthoc-proof-replay-view.v1',posthoc_audit_only=True,excluded_from_estimates=True,predeclared_first_tape=False,seed=report['seed'],actor=report['actor_seed'],config=declaration['config'],viewer_path='./traces/'+name+'.json.gz',trace_sha256=sidecar['trace_sha256'],source_trace_sha256=report['full_witness_sha256'],declaration_viewer_path='./traces/'+name+'.declaration.json',certificate_viewer_path='./traces/'+name+'.certificate.json',report_viewer_path='./traces/'+name+'.audit-report.json',fresh_check_valid=True,identity_valid=True,orders=32,shipped=31,necessary_missing_lower_bound=1,checked_missing_upper_bound=1,secondary_optimality_gap=None,quality_evidence=evidence,sources=sources,metrics=trace['metrics'],scope=report['scope'],source_path=str(source.relative_to(ROOT)))
 (out/'posthoc-proof-replay-index.json').write_text(json.dumps(index,indent=2)+'\n');print(json.dumps(dict(orders=32,shipped=31,primary_lower=1,primary_upper=1,gzip_bytes=len(compressed),fresh_check=True,identity=True)))
if __name__=='__main__':main()
