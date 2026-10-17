"""Run over the existing SSH channel after termination; emit an audit archive."""
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import time

ROOT=Path('/home/iwosmu/qh26-stage2-20261016/experiments/multi-reference-parallel-20261017T0000')
JOB='6117466'
fields=['JobID','State','ExitCode','AllocCPUS','ElapsedRaw','TotalCPU','CPUTimeRAW','MaxRSS','ReqMem','Start','End','NodeList','Account','QOS','Partition']
result=subprocess.run(['sacct','-j',JOB,'--parsable2','--noheader','--units=K','--format='+','.join(fields)],text=True,capture_output=True,check=True)
rows=[dict(zip(fields,line.split('|')))for line in result.stdout.splitlines()if line]
job=next(row for row in rows if row['JobID']==JOB)
if job['State']in ('RUNNING','PENDING','CONFIGURING','COMPLETING'):raise SystemExit('Job is not finished; no collection performed')
status=dict(job_id=JOB,collected_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),remote_directory=str(ROOT),
 accounting_fields=fields,accounting_rows=rows,accounting_raw=result.stdout,accounting_stderr=result.stderr,
 report_present=(ROOT/'result/report.json').exists())
files=[ROOT/name for name in ('manifest.json','job.sbatch','run.py','instance.json','hint-trace.json')]
files+=sorted((ROOT/'stage2').glob('*.py'))+sorted((ROOT/'result').glob('*.json'))+sorted(ROOT.glob('slurm-*'))
with tarfile.open(fileobj=sys.stdout.buffer,mode='w|gz')as archive:
 raw=(json.dumps(status,indent=2)+'\n').encode();member=tarfile.TarInfo('collection-status.json');member.size=len(raw);archive.addfile(member,io.BytesIO(raw))
 for path in files:
  if path.is_file():archive.add(path,arcname=str(path.relative_to(ROOT)))
