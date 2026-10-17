"""Preserve an as-of accounting snapshot; no scheduler or factory mutation.

Updates only explicitly tracked single-job records in the supplied raw export.
Previously reconciled array allocations remain unchanged. JobIDRaw is never
used as the array identity. Local host CPU is outside this scheduler ledger.
"""
import argparse,datetime,hashlib,json
from pathlib import Path


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def snapshot(ledger_path,raw_path,report_directory,output_prefix):
    ledger_path=Path(ledger_path);raw_path=Path(raw_path);prefix=Path(output_prefix)
    summary_path=prefix.with_name(prefix.name+'-summary.json');preserved=prefix.with_name(prefix.name+'-ledger.json')
    preserved_source=prefix.with_name(prefix.name+'-source.py')
    if summary_path.exists() or preserved.exists() or preserved_source.exists():raise ValueError('Preserve prior accounting snapshots')
    ledger=json.loads(ledger_path.read_text());jobs={j['id']:j for j in ledger['jobs']}
    if len(jobs)!=len(ledger['jobs']) or any('_' in j and j.split('_')[0] in jobs for j in jobs):raise ValueError('Double-counted job/array ledger')
    captured=datetime.datetime.fromtimestamp(raw_path.stat().st_mtime,datetime.timezone.utc).isoformat()
    seen=set()
    for line in raw_path.read_text().splitlines():
        job_id,raw_id,name,state,elapsed,cpus,tres,total_cpu,exit_code=line.split('|')[:9]
        if job_id not in jobs or job_id in seen:raise ValueError('Unexpected or duplicated raw JobID: '+job_id)
        seen.add(job_id);j=jobs[job_id]
        if j.get('array') or 'array_elapsed_seconds' in j:raise ValueError('Array needs an explicit complete child reconciliation')
        j.update(state=state,reported_elapsed_seconds=int(elapsed),allocated_cpu_seconds=int(elapsed)*int(cpus),last_status_utc=captured,accounting_reference=raw_path.name,exit_code=exit_code)
    pending={'RUNNING','PENDING','SUBMITTED','PARTIAL'}
    completed=sum(j.get('allocated_cpu_seconds',0) for j in jobs.values() if j['state']=='COMPLETED')/3600
    finished=sum(j.get('allocated_cpu_seconds',0) for j in jobs.values() if j['state'] not in pending)/3600
    running=sum(j.get('allocated_cpu_seconds',0) for j in jobs.values() if j['state']=='RUNNING')/3600
    ledger.update(completed_cluster_allocated_cpu_hours=completed,finished_cluster_allocated_cpu_hours_including_failures=finished,current_reported_running_allocated_cpu_hours=running,last_accounting_snapshot=raw_path.name)
    groups=json.loads((Path(report_directory)/'all-groups.json').read_text())
    final=[jobs[str(j)] for j in range(6117508,6117518)]
    if len(groups)!=74 or not all(j['state']=='COMPLETED' for j in final):raise ValueError('Complete ten-cohort final accounting required')
    payload=json.dumps(ledger,indent=2)+'\n';preserved.write_text(payload);preserved_source.write_bytes(Path(__file__).read_bytes())
    summary=dict(schema='stage2-final-research-accounting-snapshot.v1',as_of_utc=captured,
        final_evaluation_jobs=[dict(job_id=j['id'],state=j['state'],elapsed_seconds=j['reported_elapsed_seconds'],allocated_cpus=j['cpus'],allocated_cpu_seconds=j['allocated_cpu_seconds']) for j in final],
        final_evaluation_allocated_cpu_hours=sum(j['allocated_cpu_seconds'] for j in final)/3600,
        final_evaluation_literal_episode_cpu_hours=sum(g['cost']['timings']['cpu_seconds']['literal_sum_all_executions'] for g in groups)/3600,
        final_evaluation_literal_episode_wall_hours=sum(g['cost']['timings']['wall_seconds']['literal_sum_all_executions'] for g in groups)/3600,
        research_completed_allocated_cpu_hours=completed,research_finished_allocated_cpu_hours_including_failed=finished,research_running_reported_allocated_cpu_hours=running,
        research_running_job_ids=[j['id'] for j in jobs.values() if j['state']=='RUNNING'],recorded_gpu_hours=sum(j.get('gpu_hours',0) for j in jobs.values()),physical_qpu_calls=0,veloxq_calls=0,
        local_compute_scope='Local sweeps/tests/audits/demos separately retained where measured; not a complete host-wide or agent-inference CPU meter.',
        accounting_scope='Final allocations are a SUBSET of research allocation. Episode CPU excludes startup/driver overhead. Nested planning/check/inference timers are not additive. Sequential episode wall-time sum is not campaign elapsed. Running allocation is as-of, not final. Slurm top-level TotalCPU0 is not zero actual work. GPU0h is recorded resolution, including a zero-elapsed hardware probe; no GPU training.',
        immutable_ledger_snapshot=str(preserved),inputs={str(p):sha(p) for p in (preserved,preserved_source,raw_path,Path(report_directory)/'report.json',Path(report_directory)/'all-groups.json')},analysis_source_sha256=sha(__file__))
    summary_path.write_text(json.dumps(summary,indent=2)+'\n');ledger_path.write_text(payload);return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('ledger','raw','report','output-prefix'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();s=snapshot(a.ledger,a.raw,a.report,a.output_prefix)
    print(json.dumps({k:s[k] for k in ('as_of_utc','research_finished_allocated_cpu_hours_including_failed','research_running_reported_allocated_cpu_hours','research_running_job_ids','recorded_gpu_hours')},indent=2))
