"""Frozen-v12 selected-policy replay plus explicitly post-selection diagnostics."""
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import gzip,hashlib,json,multiprocessing,os
from pathlib import Path
import subprocess,time
import adaptive_evidence as evidence
import identity_audit

PHYSICAL=('operations','moves','worker_moves','events','energy','metrics','admission_history','algorithm_audit')


def read_trace(path):return json.loads(gzip.decompress(Path(path).read_bytes()))


def physical_digest(trace):return evidence.digest(evidence.canonical({key:trace.get(key) for key in PHYSICAL}))


def run(fit,output,job,workers):
    from stage2 import adaptive_recovery as a
    fit=Path(fit).resolve();output=Path(output).resolve()
    if output.exists():raise ValueError('Use a new output directory; retained evidence must not be overwritten')
    cmd=['sacct','-X','-j',job,'--parsable2','--noheader','--format=JobID,State,ExitCode,ElapsedRaw,AllocCPUS,TotalCPU,CPUTimeRAW,Partition,Account,QOS,NodeList,Start,End']
    accounting_raw=subprocess.check_output(cmd,text=True)
    records=[line.split('|') for line in accounting_raw.splitlines() if line.strip()]
    matching=[r for r in records if r[0]==job]
    if len(matching)!=1 or matching[0][1]!='COMPLETED' or matching[0][2]!='0:0':
        raise RuntimeError('Actual successful fit completion required before attestation: '+accounting_raw)
    output.mkdir(parents=True);started=time.perf_counter();sources=a.hashes()
    accounting=dict(scope='Original fit scheduler accounting; Python/package metadata below belong to post-fit collection',
        command=cmd,raw=accounting_raw,completed_job_id=job,successful_completion_verified=True,
        collector_runtime=evidence.runtime_metadata(),driver_sha256=evidence.digest(Path(__file__).read_bytes()))
    runtime_path=output/'fit-scheduler-accounting.json';runtime_path.write_text(json.dumps(accounting,indent=2)+'\n')
    (output/'postfit_diagnostic.py').write_bytes(Path(__file__).read_bytes())
    (output/'identity_audit.py').write_bytes(Path(identity_audit.__file__).read_bytes())
    sealed=output/'selected-seal'
    seal_report=evidence.seal(fit,sealed,execution_complete=True,replay=True,workers=workers,training_runtime=runtime_path)
    verified=evidence.verify_seal(sealed)
    replay=json.loads((sealed/'selected-validation-replay.json').read_bytes());checkpoint=json.loads((sealed/'original/selected-checkpoint.json').read_bytes())
    identity_rows=[];analysis=[];static_tasks=[];selected_digests={}
    for row in replay['rows']:
        path=sealed/row['trace_path'];trace=read_trace(path)
        result=identity_audit.audit_trace(trace)
        identity_rows.append(dict(context_id=row['context_id'],seed=row['seed'],valid=result['valid'],issues=result['issues'],metrics=result['metrics'],trace_sha256=row['trace_sha256']))
        selected_digests[row['context_id'],row['seed']]=physical_digest(trace)
    for c,context in enumerate(checkpoint['contexts']):
        group=[row for row in replay['rows'] if row['context_id']==c];kind=checkpoint['policies_by_context'][c]['kind']
        sequences=[tuple(step['action'] for step in row['trajectory']) for row in group]
        used=sorted({action for seq in sequences for action in seq})
        changes=[sum(x!=y for x,y in zip(seq,seq[1:])) for seq in sequences]
        item=dict(context_id=c,config=context['config'],policy_kind=kind,selected_update=checkpoint['selection'][c]['selected_update'],
            declared_selection_key=checkpoint['selection'][c]['key'],
            action_sequence_histogram={','.join(map(str,seq)):count for seq,count in Counter(sequences).items()},
            action_descriptors={str(action):a.ACTIONS[action] for action in used},
            within_episode_change_counts=changes,constant_episodes=sum(len(set(seq))==1 for seq in sequences),
            identical_constant_action_across_all_validation=bool(sequences) and len(set(sequences))==1 and len(set(sequences[0]))==1,
            static_diagnostics_role='Additional reused-VAL diagnostic after learned checkpoint selection; not unbiased final evidence or new training',
            matching_static_actions=[] if kind=='static' else used)
        analysis.append(item)
        if kind!='static':
            for action in used:
                policy=dict(kind='static',action=action);sha=evidence.digest(evidence.canonical(policy))
                for seed in range(100,116):
                    static_tasks.append(dict(context_id=c,context=context,policy=policy,policy_sha256=sha,
                        source_hashes=checkpoint['source_hashes'],interval=checkpoint['interval'],seed=seed,
                        trace_path=str(output/f'static-context{c}-action{action}-seed{seed}.json.gz')))
    if static_tasks:
        with ProcessPoolExecutor(max_workers=workers,mp_context=multiprocessing.get_context('spawn')) as pool:
            static_rows=list(pool.map(evidence._replay,static_tasks))
    else:static_rows=[]
    comparisons=[]
    for task,row in zip(static_tasks,static_rows):
        row['static_action']=task['policy']['action'];path=output/row['trace_path']
        trace=read_trace(path);identity=identity_audit.audit_trace(trace)
        row['identity_valid']=identity['valid'];row['identity_issues']=identity['issues']
        row['physical_lists_sha256']=physical_digest(trace)
        row['physical_lists_identical_to_selected']=row['physical_lists_sha256']==selected_digests[row['context_id'],row['seed']]
    for item in analysis:
        c=item['context_id']
        for action in item['matching_static_actions']:
            group=[r for r in static_rows if r['context_id']==c and r['static_action']==action]
            comparisons.append(dict(context_id=c,action=action,weights=a.ACTIONS[action],
                selection_key=evidence.selection_key(group),all_valid=all(r['valid'] and r['identity_valid'] for r in group),
                matching_selected_physical_trajectories=sum(r['physical_lists_identical_to_selected'] for r in group),
                runs=len(group),role='Post-selection matched static diagnostic on reused VAL100..115'))
    if a.hashes()!=sources:raise RuntimeError('Frozen source changed during post-fit diagnostics')
    report=dict(schema='stage2-adaptive-postfit-diagnostics.v1',fit_directory=str(fit),training_job=job,
        selected_seal_report_status=seal_report['status'],selected_seal_verification=verified,
        selected_replay_count=len(replay['rows']),selected_identity_all_valid=all(r['valid'] for r in identity_rows),
        selected_identity_rows=identity_rows,selected_behavior=analysis,static_diagnostic_runs=len(static_rows),
        static_diagnostic_comparisons=comparisons,static_rows=static_rows,
        source_hashes=sources,overlay_sha256=evidence.digest(Path(evidence.__file__).read_bytes()),
        identity_supplement_sha256=evidence.digest(Path(identity_audit.__file__).read_bytes()),
        driver_sha256=evidence.digest(Path(__file__).read_bytes()),runtime=evidence.runtime_metadata(),
        fit_costs=seal_report['original_costs'],selected_replay_rollout_cpu_seconds=seal_report['replay_rollout_cpu_seconds'],
        selected_replay_rollout_wall_seconds_sum=seal_report['replay_rollout_wall_seconds_sum'],
        static_diagnostic_rollout_cpu_seconds=sum(r['cpu_seconds'] for r in static_rows),
        static_diagnostic_rollout_wall_seconds_sum=sum(r['wall_seconds'] for r in static_rows),
        postfit_total_wall_seconds=time.perf_counter()-started,final_tapes=0,
        disclosures=['All results use reused development validation after checkpoint selection; no untouched performance claim.',
            'A network constant over these trajectories is not a proved globally static policy. Exact matched static physical traces establish equivalence on these sixteen tapes only.',
            'Additional static controls are limited to action IDs actually used by the selected policy. This is a diagnostic, not an exhaustive fresh model search.',
            'Sealed original v12 does not retain all rejected networks or original trajectories; selected replay is independently retained.'])
    (output/'postfit-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('selected_seal_report_status','selected_replay_count','selected_identity_all_valid','selected_behavior','static_diagnostic_comparisons','postfit_total_wall_seconds')},indent=2),flush=True)
    if seal_report['status']!='replayed_and_matched' or not report['selected_identity_all_valid'] or any(not r['valid'] or not r['identity_valid'] for r in static_rows):raise RuntimeError('Post-fit evidence failed; retained for diagnosis')
    return report


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--fit',required=True);p.add_argument('--output',required=True)
    p.add_argument('--training-job',required=True);p.add_argument('--workers',type=int,default=32)
    args=p.parse_args();run(args.fit,args.output,args.training_job,args.workers)
