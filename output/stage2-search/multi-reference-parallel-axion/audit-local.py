"""Independently recheck a collected parallel result and retain actual cost."""
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from stage2.check import check_trace

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text())
def cpu_seconds(value):
 if not value:return None
 days=0
 if '-'in value:day,value=value.split('-',1);days=int(day)
 parts=[float(x)for x in value.split(':')]
 return days*86400+sum(value*60**index for index,value in enumerate(reversed(parts)))

def main():
 base=Path(__file__).resolve().parent;collected=base/'collected';status=read(collected/'collection-status.json')
 submission=read(base/'submission.json');manifest=read(collected/'manifest.json')
 assert sha(collected/'manifest.json')==submission['payload_manifest_sha256']
 assert all(sha(collected/name)==digest for name,digest in manifest['payload_hashes'].items())
 job=next(row for row in status['accounting_rows']if row['JobID']==submission['job_id'])
 cpus=int(job['AllocCPUS']);elapsed=int(job['ElapsedRaw']);assert cpus in (0,16)
 cost=dict(allocated_cpus=cpus,scheduler_elapsed_seconds=elapsed,allocated_cpu_hours=cpus*elapsed/3600,
  slurm_total_cpu_seconds=cpu_seconds(job['TotalCPU']),slurm_CPUTimeRAW=int(job['CPUTimeRAW']),
  reported_MaxRSS_by_step={row['JobID']:row['MaxRSS']for row in status['accounting_rows']},gpu_hours=0,
  scheduler_requested_cap_seconds=1800,budget_overrun_seconds=max(0,elapsed-1800),
  scope='Actual Slurm allocation and measured process CPU; not an apples-to-apples hardware speedup benchmark')
 outcome=dict(job_id=submission['job_id'],slurm_state=job['State'],slurm_exit_code=job['ExitCode'],cost=cost,
  instance_sha256=manifest['instance_sha256'],frozen_reference_sha256=manifest['payload_hashes']['stage2/reference_multi.py'],
  collection_archive_sha256=sha(base/'collected.tar.gz'),report_present=status['report_present'])
 if status['report_present']:
  report=read(collected/'result/report.json');instance=read(collected/'instance.json')
  assert report['sources_stable_during_run']and report['payload_hashes']==manifest['payload_hashes']
  assert report['instance_sha256']==manifest['instance_sha256']
  assert hashlib.sha256(json.dumps(instance,sort_keys=True,separators=(',',':')).encode()).hexdigest()==manifest['instance_sha256']
  for name,digest in report['artifact_hashes'].items():assert sha(collected/'result'/name)==digest
  exact=report['exact'];assert exact['search_workers']==16 and exact['solver_version']=='9.15.6755'
  assert exact['wall_limit_seconds']==1770 and exact['deterministic_limit']==1000000000
  outcome.update(cp_status=exact['status'],incumbent_ticks=exact['objective_ticks'],cp_lower_bound_ticks=exact['best_bound_ticks'],
   optimal=exact['optimal'],solver_wall_seconds=exact['solver_wall_seconds'],process_cpu_seconds=report['runtime']['process_cpu_seconds'])
  outcome.update(prior_certified_interval=[1480,1732],improved_cp_lower_bound=exact['best_bound_ticks']>1400,
   improved_best_lower_bound=exact['best_bound_ticks']>1480,
   improved_checked_upper_bound=exact['objective_ticks']is not None and exact['objective_ticks']<1732,
   conflicts_with_prior_analytic_bound=exact['objective_ticks']is not None and exact['objective_ticks']<1480)
  trace_path=collected/'result/cp-trace.json'
  if trace_path.exists():
   trace=read(trace_path);assert trace['instance']==instance
   fresh=check_trace(trace);assert fresh['valid']and fresh['all_orders_fulfilled']and fresh['terminal_requirements_met']
   assert max(fresh['metrics']['delivery_ticks'].values())==exact['objective_ticks']
   outcome.update(fresh_independent_check=fresh,checker_sha256=sha(ROOT/'stage2/check.py'),trace_sha256=sha(trace_path),valid_complete=True)
 write=base/'independent-audit.json';write.write_text(json.dumps(outcome,indent=2)+'\n');print(json.dumps(outcome))

if __name__=='__main__':main()
