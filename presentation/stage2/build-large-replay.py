"""Copy one explicitly optional compressed replay; preserve original trace bytes."""
import gzip
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from stage2.check import check_trace

def sha(raw):return hashlib.sha256(raw).hexdigest()
def main():
 source=ROOT/'output/stage2-search/quality-material-primary-bound/n32-H14400-seed0-witness.json.gz'
 cohort=ROOT/'output/stage2-search/quality-material-primary-bound/report.json'
 row=next(row for row in json.loads(cohort.read_text())['rows']if row['seed']==0)
 raw=source.read_bytes();assert sha(raw)==row['trace_sha256']
 trace=json.loads(gzip.decompress(raw));checked=check_trace(trace)
 assert checked['valid']and checked['terminal_requirements_met']and checked['all_orders_fulfilled']
 assert trace['horizon_ticks']==14400 and trace['metrics']['shipped']==trace['metrics']['orders']==34
 cert_path=ROOT/row['certificate_path'];cert_raw=cert_path.read_bytes();certificate=json.loads(cert_raw)
 assert sha(cert_raw)==row['certificate_sha256']
 assert sha(json.dumps(trace['instance'],sort_keys=True,separators=(',',':')).encode())==certificate['instance_sha256']
 out=Path(__file__).resolve().parent/'traces';out.mkdir(exist_ok=True)
 target=out/'large-train0-32-240h.json.gz';target.write_bytes(raw)
 evidence=dict(schema='stage2-optional-replay-evidence.v1',label='TRAIN 0 · 32 initial + 2 urgent orders · 240h',
  seed_role='TRAIN; fixed realized tape, not held-out performance',horizon_scope='240h = 10 days; extra calendar time, not a 96-hour solution or algorithmic speedup',
  source_path=str(source.relative_to(ROOT)),trace_sha256=sha(raw),trace_sha256_convention='Original gzip-file bytes',compressed_bytes=len(raw),
  decompressed_bytes=len(gzip.decompress(raw)),instance_sha256=certificate['instance_sha256'],
  certificate_path=row['certificate_path'],certificate_sha256=sha(cert_raw),certificate=certificate,
  cohort_path=str(cohort.relative_to(ROOT)),cohort_sha256=sha(cohort.read_bytes()),
  fresh_independent_check=checked,checker_sha256=sha((ROOT/'stage2/check.py').read_bytes()),
  metrics=trace['metrics'],operations=len(trace['operations']),moves=len(trace['moves']),
  activity_data_changed=False,secondary_optimality_gap=None,
  loading='Optional 194KB gzip asset; fetched/decompressed only when explicitly selected')
 (out/'large-train0-32-240h.evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
 print(json.dumps(dict(compressed_bytes=len(raw),operations=len(trace['operations']),moves=len(trace['moves']),valid=checked['valid'],
  shipped=trace['metrics']['shipped'],total_tardiness_ticks=trace['metrics']['total_tardiness_ticks'],total_cost=trace['metrics']['total_cost'])))

if __name__=='__main__':main()
