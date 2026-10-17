"""One bounded parallel solve of the unchanged retained four-pump fixture."""
import hashlib
import json
import os
from pathlib import Path
import platform
import time

from stage2.reference_multi import solve
from stage2.check import check_trace

ROOT=Path(__file__).resolve().parent
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text())
def write(path,value):path.write_text(json.dumps(value,indent=2)+'\n')
def current_hashes(manifest):return {name:sha(ROOT/name)for name in manifest['payload_hashes']}

def main():
 began=time.perf_counter();cpu=time.process_time();manifest=read(ROOT/'manifest.json')
 before=current_hashes(manifest)
 assert before==manifest['payload_hashes'],'Frozen source/input/runner drift'
 assert before['stage2/reference_multi.py']=='226dced1939ee824a0e661d4112efc488be4de3286e6280e9da4e58163700efe'
 instance=read(ROOT/'instance.json');hint=read(ROOT/'hint-trace.json')
 assert hashlib.sha256(json.dumps(instance,sort_keys=True,separators=(',',':')).encode()).hexdigest()==manifest['instance_sha256']
 assert hint['instance']==instance and len(instance['orders'])==4
 checked=check_trace(hint)
 assert checked['valid']and checked['all_orders_fulfilled']and checked['terminal_requirements_met']
 assert max(checked['metrics']['delivery_ticks'].values())==1732
 assert int(os.environ['SLURM_CPUS_PER_TASK'])==16
 output=ROOT/'result';output.mkdir(exist_ok=False)
 write(output/'started.json',dict(started_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
  pid=os.getpid(),job_id=os.environ.get('SLURM_JOB_ID'),instance_sha256=manifest['instance_sha256'],payload_hashes=before))
 result=solve(instance,wall_limit=1770,deterministic_limit=1000000000,workers=16,seed=0,incumbent=hint)
 for name,key in (('cp-trace.json','trace'),('cp-schedule.json','schedule')):
  if key in result:write(output/name,result.pop(key))
 report=dict(exact=result,hint_fresh_check=checked,hint_makespan_ticks=1732,
  instance_sha256=manifest['instance_sha256'],payload_hashes=before,sources_stable_during_run=before==current_hashes(manifest),
  runtime=dict(python=platform.python_version(),wall_seconds=time.perf_counter()-began,process_cpu_seconds=time.process_time()-cpu),
  slurm={key:os.environ.get(key)for key in ('SLURM_JOB_ID','SLURM_JOB_ACCOUNT','SLURM_JOB_QOS','SLURM_JOB_PARTITION','SLURM_CPUS_PER_TASK','SLURM_MEM_PER_NODE','SLURMD_NODENAME')},
  scheduler_wall_cap_seconds=1800,cp_wall_cap_seconds=1770,search_workers=16,
  maximum_allocated_cpu_hours=8,cp_proof_resumed=False,fresh_search=True,final_tapes_used=0,
  scope='Identical frozen four-pump automatic-attendance direct-transfer reference; no flagship, physics or CP-model change',
  source_report_sha256=manifest['prior_report_sha256'])
 report['artifact_hashes']={path.name:sha(path)for path in output.iterdir()if path.is_file()}
 write(output/'report.json',report)
 print(json.dumps(dict(status=result['status'],incumbent=result['objective_ticks'],cp_bound=result['best_bound_ticks'],
  checked=result.get('validation',{}).get('valid'),wall_seconds=report['runtime']['wall_seconds'],cpu_seconds=report['runtime']['process_cpu_seconds'],
  sources_stable=report['sources_stable_during_run'])),flush=True)

if __name__=='__main__':main()
