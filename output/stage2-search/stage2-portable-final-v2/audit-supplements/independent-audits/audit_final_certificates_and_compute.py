"""Reconcile offline certificates and as-of accounting with completed rows."""
from collections import defaultdict
from fractions import Fraction as Q
import hashlib
import json
import math
from pathlib import Path
import time

from stage2.quality_material_bound import certificate
from stage2.spec import build

ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def near(a,b):assert math.isclose(float(a),b,rel_tol=1e-10,abs_tol=1e-8),(float(a),b)


def audit():
    began=time.perf_counter();final=read(BASE/'final-complete-report/report.json')
    paths=read(BASE/'final-complete-index.json');groups=defaultdict(list);allrows=[]
    for label,path in paths.items():
        for line in (Path(path)/'rows.jsonl').read_text().splitlines():
            row=json.loads(line);allrows.append(row);groups[label,row['method_id']].append(row)
    protocol=read(BASE/'final-frozen-bundle-v20p2/final-heldout-protocol.json')
    weights={seed:Q(*leaf['probability'])/len(leaf['seeds']) for leaf in protocol['leaves'] for seed in leaf['seeds']}
    certified=[]
    for selected in final['preselected_frontier']:
        name=selected['method_id'];folder=BASE/'final-primary-certificates'/name;r=read(folder/'report.json')
        assert r['method_id']==name and r['config']==selected['config'] and r['protocol_sha256']==final['protocol_sha256']
        assert r['secondary_optimality_gap'] is None and len(r['rows'])==256
        for path,digest in r['source_hashes'].items():assert sha(path)==digest
        byseed=defaultdict(list)
        for row in groups[selected['cohort'],name]:byseed[row['seed']].append(row)
        total_missing=Q(0);total_low=Q(0);total_gap=Q(0);total_attained=Q(0);positive=Q(0);positive_count=0;attained_positive=0
        for entry in r['rows']:
            path=folder/entry['certificate_path'];assert sha(path)==entry['certificate_sha256']
            saved=read(path);instance=build(**selected['config'],seed=entry['seed'])
            fresh=certificate(instance);assert json.loads(json.dumps(fresh))==saved
            low=fresh['unfulfilled_lower_bound'];assert entry['necessary_missing_lower_bound']==low
            originals={row['policy_seed']:row for row in byseed[entry['seed']]};actors=entry['actors']
            assert set(originals)=={a['actor_seed'] for a in actors}
            missing=Q(0);gap=Q(0);attained=Q(0)
            for actor in actors:
                original=originals[actor['actor_seed']];upper=original['checker_metrics']['unfulfilled_orders']
                assert entry['physical_instance_sha256']==fresh['instance_sha256']==original['physical_instance_sha256']
                assert entry['demand']==fresh['observed_realized_orders']==original['metrics']['orders']
                assert actor['checked_missing']==upper and actor['lower_bound']==low and upper>=low
                assert actor['unknown_primary_gap_interval']==[0,upper-low]
                assert actor['primary_optimum_attained']==(upper==low)
                missing+=Q(upper,len(actors));gap+=Q(upper-low,len(actors));attained+=Q(int(upper==low),len(actors))
            w=weights[entry['seed']];total_missing+=w*missing;total_low+=w*low;total_gap+=w*gap;total_attained+=w*attained
            positive+=w*int(low>0);positive_count+=int(low>0);attained_positive+=int(low>0 and attained==1)
        near(total_missing,r['weighted_mean_checked_missing']);near(total_missing,selected['summary']['metrics']['unfulfilled']['mean'])
        near(total_low,r['weighted_mean_necessary_missing_lower_bound']);near(total_gap,r['weighted_mean_primary_gap_upper_bound'])
        near(total_attained,r['weighted_primary_optimum_attainment']);near(positive,r['weighted_probability_nonzero_necessary_missing'])
        assert total_missing-total_low==total_gap
        certified.append(dict(method_id=name,report_sha256=sha(folder/'report.json'),tapes=256,positive_bound_tapes=positive_count,
                              attained_positive_bound_tapes=attained_positive,weighted_missing=float(total_missing),
                              weighted_lower_bound=float(total_low),weighted_primary_gap_upper_bound=float(total_gap),
                              weighted_primary_attainment=float(total_attained)))
    summary_path=BASE/'final-compute-summary-0122.json';summary=read(summary_path);ledger=read(BASE/'compute-ledger.json')
    for path,digest in summary['inputs'].items():assert sha(path)==digest
    jobs=ledger['jobs'];assert len({j['id'] for j in jobs})==len(jobs)
    # Array aggregate entries and individually recorded children cannot coexist.
    ids={j['id'] for j in jobs}
    assert all(not any(other.startswith(j['id']+'_') for other in ids) for j in jobs if '_' not in j['id'])
    for job in jobs:
        if 'array_elapsed_seconds' in job:
            assert job['allocated_cpu_seconds']==sum(job['array_elapsed_seconds'])*job.get('cpus_per_array_task',job.get('cpus'))
        elif 'reported_elapsed_seconds' in job:
            assert job.get('allocated_cpu_seconds',0)==job['reported_elapsed_seconds']*job['cpus']
    completed=sum(j.get('allocated_cpu_seconds',0) for j in jobs if j['state']=='COMPLETED')
    finished=sum(j.get('allocated_cpu_seconds',0) for j in jobs if j['state'] in ('COMPLETED','FAILED'))
    running=sum(j.get('allocated_cpu_seconds',0) for j in jobs if j['state']=='RUNNING')
    near(Q(completed,3600),summary['research_completed_allocated_cpu_hours']);near(Q(finished,3600),summary['research_finished_allocated_cpu_hours_including_failed'])
    near(Q(running,3600),summary['research_running_reported_allocated_cpu_hours'])
    near(Q(completed,3600),ledger['completed_cluster_allocated_cpu_hours'])
    near(Q(finished,3600),ledger['finished_cluster_allocated_cpu_hours_including_failures'])
    near(Q(running,3600),ledger['current_reported_running_allocated_cpu_hours'])
    raw={line.split('|')[0]:line.split('|') for line in (BASE/'accounting-20261017-0122.txt').read_text().splitlines()}
    allocation=0
    for job in summary['final_evaluation_jobs']:
        fields=raw[job['job_id']];assert fields[3]=='COMPLETED' and fields[8]=='0:0'
        assert int(fields[4])==job['elapsed_seconds'] and int(fields[5])==job['allocated_cpus']==32
        assert job['allocated_cpu_seconds']==int(fields[4])*int(fields[5])
        assert fields[6]==job['alloc_tres'] and 'gpu' not in fields[6].lower()
        allocation+=job['allocated_cpu_seconds']
    assert {j['job_id'] for j in summary['final_evaluation_jobs']}=={str(n) for n in range(6117508,6117518)}
    near(Q(allocation,3600),summary['final_evaluation_allocated_cpu_hours'])
    cpu=sum(Q(str(r['cpu_seconds'])) for r in allrows)/3600;wall=sum(Q(str(r['wall_seconds'])) for r in allrows)/3600
    near(cpu,summary['final_evaluation_literal_episode_cpu_hours']);near(wall,summary['final_evaluation_literal_episode_wall_hours'])
    assert sum(j.get('gpu_hours',0) for j in jobs)==summary['recorded_gpu_hours']==0
    assert summary['physical_qpu_calls']==summary['veloxq_calls']==0
    return dict(schema='stage2-independent-final-certificates-compute-audit.v1',valid=True,
                certificate_reports=certified,certificate_tapes_recomputed=2048,
                final_allocated_cpu_hours=float(Q(allocation,3600)),literal_episode_cpu_hours=float(cpu),
                research_completed_allocated_cpu_hours=float(Q(completed,3600)),
                finished_including_failed_allocated_cpu_hours=float(Q(finished,3600)),
                running_asof_allocated_cpu_hours=float(Q(running,3600)),
                accounting_asof_utc=summary['as_of_utc'],accounting_summary_sha256=sha(summary_path),
                source_sha256=sha(__file__),factory_simulations=0,wall_seconds=time.perf_counter()-began,
                scope='Recomputed saved necessary-bound certificates on fresh numerical instances; reconciled selected original checked outcomes and exact weighted primary intervals. Accounting uses unique ledger allocations, no array parent/child or nested-timer addition. RecordedGPUhours0 includes coarse zero-second hardware probe, not a claim no GPU was ever allocated; top-level SlurmTotalCPU0 is not measured workloadCPU0. Running totals are as-of and final allocation is a subset of research allocation. No local host-wide or agent inference meter.')


if __name__=='__main__':
    result=audit()
    with (ROOT/'complete-certificates-compute-audit.json').open('x') as stream:stream.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
