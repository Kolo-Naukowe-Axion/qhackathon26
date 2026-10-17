"""Post-fit integrity seal and deterministic selected-policy validation replay.

Standalone overlay: execute this file with PYTHONPATH pointing to the frozen
v12 source root. It never trains, changes source files, or executes final tapes.
The current runtime is evidence-collection runtime, not retroactive fit metadata.
"""
from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from copy import deepcopy
import gzip
import hashlib
import importlib.metadata
import json
import math
import multiprocessing
import os
from pathlib import Path, PurePosixPath
import platform
import socket
import sys
import time
import traceback


def digest(data):return hashlib.sha256(data).hexdigest()


def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':')).encode()


def runtime_metadata():
    packages={}
    for name in ('numpy','torch','scipy'):
        try:packages[name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:packages[name]=None
    try:affinity=sorted(os.sched_getaffinity(0))
    except (AttributeError,OSError):affinity=None
    return dict(scope='Post-fit seal/replay process; not a reconstruction of original training runtime',
        hostname=socket.gethostname(),platform=platform.platform(),machine=platform.machine(),
        python=platform.python_version(),executable=sys.executable,packages=packages,
        logical_cpu_count=os.cpu_count(),cpu_affinity=affinity,
        allocation={key:os.environ.get(key) for key in ('SLURM_JOB_ID','SLURM_ARRAY_JOB_ID','SLURM_ARRAY_TASK_ID',
            'SLURM_JOB_PARTITION','SLURM_CPUS_PER_TASK','SLURM_CPUS_ON_NODE','SLURM_JOB_NUM_NODES')},
        thread_environment={key:os.environ.get(key) for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS',
            'MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS','CUDA_VISIBLE_DEVICES')})


def _safe_snapshot_path(root,name):
    path=PurePosixPath(name)
    if path.is_absolute() or '..' in path.parts:raise ValueError('Unsafe source snapshot path')
    result=(root/str(path)).resolve()
    if not result.is_relative_to(root.resolve()):raise ValueError('Snapshot source escapes run directory')
    return result


def inspect_run(directory):
    """Read original records without mutation; reject incomplete/inconsistent logs."""
    directory=Path(directory).resolve();blobs={}
    for name in ('selected-checkpoint.json','episodes.jsonl','protocol.json'):
        blobs[name]=(directory/name).read_bytes()
    checkpoint=json.loads(blobs['selected-checkpoint.json']);protocol=json.loads(blobs['protocol.json'])
    rows=[json.loads(line) for line in blobs['episodes.jsonl'].splitlines() if line.strip()]
    if checkpoint.get('schema')!='stage2-adaptive-recovery-policy.v1':raise ValueError('Expected v1 adaptive policy artifact')
    for key in ('method','source_hashes','contexts','actions','train_seeds','validation_seeds','seed','workers','requested_wall_seconds'):
        if checkpoint.get(key)!=protocol.get(key):raise ValueError('Checkpoint/protocol mismatch: '+key)
    if checkpoint.get('final_tapes')!=0 or protocol.get('final_tapes')!=0:
        raise ValueError('This evidence utility prohibits final tapes')
    if checkpoint.get('train_seeds')!=list(range(32)) or checkpoint.get('validation_seeds')!=list(range(100,116)):
        raise ValueError('Expected declared TRAIN0..31 and VALIDATION100..115 only')
    contexts=checkpoint['contexts'];n=len(contexts)
    if not n or len(checkpoint['policies_by_context'])!=n or len(checkpoint['selection'])!=n:
        raise ValueError('One selected policy/key per context required')
    if checkpoint['configs']!=[c['config'] for c in contexts]:raise ValueError('Context/config mismatch')
    if checkpoint.get('interval')!=protocol.get('interval_minutes'):raise ValueError('Macro interval mismatch')
    fit=validation=0
    for row in rows:
        if type(row.get('context_id')) is not int or not 0<=row['context_id']<n:raise ValueError('Invalid context index')
        if row['phase'].startswith('TRAIN'):
            if row['seed'] not in range(32):raise ValueError('Fit seed outside TRAIN')
            fit+=1
        elif row['phase']=='VALIDATION':
            if row['seed'] not in range(100,116) or row['actor_seed']!=0:raise ValueError('Validation seed/actor contract mismatch')
            validation+=1
        else:raise ValueError('Unknown episode phase')
        for key in ('wall_seconds','cpu_seconds'):
            if not math.isfinite(row.get(key,-1)) or row.get(key,-1)<0:raise ValueError('Missing/nonfinite rollout timing')
    if fit!=checkpoint['fit_episodes'] or validation!=checkpoint['validation_episodes']:
        raise ValueError('Episode counters do not match checkpoint (run may still be writing)')
    val_rows=[r for r in rows if r['phase']=='VALIDATION']
    if len(val_rows)<16*n or len(val_rows)%(16*n):raise ValueError('Incomplete validation sweep')
    for start in range(0,len(val_rows),16*n):
        sweep=val_rows[start:start+16*n]
        if {(r['context_id'],r['seed']) for r in sweep}!={(c,s) for c in range(n) for s in range(100,116)}:
            raise ValueError('Validation sweep has duplicate/missing context tapes')
    sources={}
    for name,expected in checkpoint['source_hashes'].items():
        payload=_safe_snapshot_path(directory/'source_snapshot',name).read_bytes()
        if digest(payload)!=expected:raise ValueError('Original source snapshot digest mismatch: '+name)
        sources[name]=payload
    # Catch concurrent append/replacement even when the first counters happened to agree.
    if any((directory/name).read_bytes()!=payload for name,payload in blobs.items()):
        raise ValueError('Original run changed while reading; seal only after completion')
    return dict(directory=directory,checkpoint=checkpoint,protocol=protocol,rows=rows,blobs=blobs,sources=sources,
        baseline_validation=[r for r in val_rows[:16*n]],
        costs=dict(fit_rollouts=fit,validation_rollouts=validation,total_rollouts=len(rows),
            summed_rollout_cpu_seconds=sum(r['cpu_seconds'] for r in rows),
            summed_rollout_wall_seconds=sum(r['wall_seconds'] for r in rows),
            fit_rollout_cpu_seconds=sum(r['cpu_seconds'] for r in rows if r['phase'].startswith('TRAIN')),
            validation_rollout_cpu_seconds=sum(r['cpu_seconds'] for r in rows if r['phase']=='VALIDATION'),
            original_actual_wall_seconds=checkpoint['actual_wall_seconds'],requested_wall_seconds=checkpoint['requested_wall_seconds'],
            scope='Worker rollout CPU/wall, including source guards/checking; learner, orchestration and prior costs are not isolated. v12 summary simulation_cpu_seconds is ignored.'))


def selection_key(rows):
    return [sum(not r['valid'] for r in rows),sum(r['metrics']['orders']-r['metrics']['shipped'] for r in rows),
        sum(r['metrics']['total_tardiness_ticks'] for r in rows),sum(r['metrics']['total_cost'] for r in rows)]


def keys_agree(left,right):
    return left[:3]==right[:3] and math.isclose(left[3],right[3],rel_tol=1e-12,abs_tol=1e-8)


def _replay(task):
    started=time.perf_counter();cpu=time.process_time()
    row={k:task[k] for k in ('context_id','seed','policy_sha256')}
    try:
        from stage2 import adaptive_recovery as a
        from stage2.check import check_trace
        from stage2.spec import build
        if a.hashes()!=task['source_hashes']:raise RuntimeError('Frozen runtime source differs from sealed fit source')
        if task['seed'] not in range(100,116):raise ValueError('Only declared validation replay is permitted')
        context=task['context'];instance=build(**context['config'],seed=task['seed']);expected=deepcopy(instance)
        controller=a.Controller(task['policy'],context['weights'],0,True,task['interval'])
        trace=a.run(instance,context['weights'],controller,**context['solver_options'])
        checked=check_trace(trace,expected);metrics=trace['metrics'];cm=checked['metrics']
        numerical_instance_match=digest(canonical(trace['instance']))==digest(canonical(expected))
        reconciliation=(metrics['shipped']==cm['delivered_orders'] and
            metrics['orders']-metrics['shipped']==cm['unfulfilled_orders'] and
            metrics['total_tardiness_ticks']==cm['terminal_deadline_debt_ticks'] and
            all(math.isclose(metrics[key],cm[key],rel_tol=1e-12,abs_tol=1e-8)
                for key in ('total_cost','grid_kwh','energy_cost','investment_cost','carbon_kg','terminal_soc')))
        valid=checked['valid'] and checked['terminal_requirements_met'] and numerical_instance_match and reconciliation
        payload=json.dumps(trace,separators=(',',':')).encode();path=Path(task['trace_path'])
        with path.open('xb') as target:target.write(gzip.compress(payload,mtime=0))
        row.update(valid=valid,issues=checked['issues'],terminal_requirements_met=checked['terminal_requirements_met'],
            numerical_instance_match=numerical_instance_match,metric_reconciliation=reconciliation,
            physical_instance_sha256=digest(canonical(expected)),metrics=metrics,checker_metrics=cm,
            trajectory=controller.trajectory,trace_path=path.name,trace_sha256=digest(payload),
            trace_gzip_sha256=digest(path.read_bytes()))
        if a.hashes()!=task['source_hashes']:raise RuntimeError('Frozen source changed during replay')
    except Exception as exc:
        row.update(valid=False,error=dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc()))
    row.update(wall_seconds=time.perf_counter()-started,cpu_seconds=time.process_time()-cpu)
    return row


def seal(directory,output,*,execution_complete=False,replay=False,workers=1,training_runtime=None):
    """Archive a completed v12 fit; optionally replay every selected VAL context.

    Original files are never overwritten. This is a hash-sealed, read-only file
    archive, not an authenticated signature or OS-immutable filesystem object.
    """
    if not execution_complete:raise ValueError('Explicit completed-run attestation required')
    if not isinstance(workers,int) or workers<1:raise ValueError('Positive replay worker count required')
    inspected=inspect_run(directory);artifact=inspected['checkpoint'];output=Path(output).resolve()
    if output.exists():raise ValueError('Use a new evidence directory; earlier seals are preserved')
    output.mkdir(parents=True);started=time.perf_counter();cpu=time.process_time()
    def write(name,data):
        path=output/name;path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as target:target.write(data)
    write('overlay/adaptive_evidence.py',Path(__file__).read_bytes())
    for name,payload in inspected['blobs'].items():write('original/'+name,payload)
    for name,payload in inspected['sources'].items():write('original/source_snapshot/'+name,payload)
    policies=[]
    for c,policy in enumerate(artifact['policies_by_context']):
        payload=canonical(policy);sha=digest(payload);name=f'policies/context{c}-{sha}.json'
        write(name,payload+b'\n');policies.append(dict(context_id=c,policy_sha256=sha,path=name,kind=policy['kind']))
    supplied_training_runtime=None
    if training_runtime is not None:
        path=Path(training_runtime);payload=path.read_bytes();json.loads(payload)
        write('supplied-training-runtime.json',payload)
        supplied_training_runtime=dict(path=str(path.resolve()),sha256=digest(payload),
            scope='Caller-supplied original execution evidence; not independently authenticated')
    replay_rows=[];comparisons=[]
    if replay:
        tasks=[dict(context_id=c,context=context,policy=artifact['policies_by_context'][c],policy_sha256=policies[c]['policy_sha256'],
            source_hashes=artifact['source_hashes'],interval=artifact['interval'],seed=seed,
            trace_path=str(output/f'trace-context{c}-seed{seed}.json.gz'))
            for c,context in enumerate(artifact['contexts']) for seed in range(100,116)]
        if workers==1:replay_rows=[_replay(task) for task in tasks]
        else:
            with ProcessPoolExecutor(max_workers=workers,mp_context=multiprocessing.get_context('spawn')) as pool:
                replay_rows=list(pool.map(_replay,tasks))
        for c in range(len(artifact['contexts'])):
            rows=[r for r in replay_rows if r['context_id']==c];complete=all('metrics' in r for r in rows)
            actual=selection_key(rows) if complete else None;declared=artifact['selection'][c]['key']
            baseline=selection_key([r for r in inspected['baseline_validation'] if r['context_id']==c])
            comparisons.append(dict(context_id=c,declared_selection_key=declared,replayed_selection_key=actual,
                key_exactly_equal=actual==declared,key_agrees_with_cost_tolerance=complete and keys_agree(actual,declared),
                baseline_logged_key=baseline,declared_no_worse_than_static_baseline=tuple(declared)<=tuple(baseline),
                all_selected_replays_independently_valid=all(r['valid'] for r in rows)))
        write('selected-validation-replay.json',json.dumps(dict(rows=replay_rows,comparisons=comparisons),indent=2).encode()+b'\n')
    status='sealed_without_replay' if not replay else ('replayed_and_matched' if all(c['key_agrees_with_cost_tolerance'] and
        c['all_selected_replays_independently_valid'] and c['declared_no_worse_than_static_baseline'] for c in comparisons) else 'replay_mismatch')
    report=dict(schema='stage2-adaptive-evidence.v1',status=status,original_directory=str(inspected['directory']),
        execution_complete_attested=True,selected_policies=policies,source_hashes=artifact['source_hashes'],
        overlay_sha256=digest(Path(__file__).read_bytes()),runtime=runtime_metadata(),training_runtime_evidence=supplied_training_runtime,
        original_costs=inspected['costs'],replay_workers=workers if replay else 0,
        replay_count=len(replay_rows),replay_rollout_cpu_seconds=sum(r['cpu_seconds'] for r in replay_rows),
        replay_rollout_wall_seconds_sum=sum(r['wall_seconds'] for r in replay_rows),
        collection_wall_seconds=time.perf_counter()-started,collection_parent_cpu_seconds=time.process_time()-cpu,
        comparisons=comparisons,final_tapes=0,
        prior_provenance='Strong priors are conservatively DEVELOPMENT-selected, including earlier validation-informed iteration; adaptive fit uses TRAIN only and selection uses reused VAL.',
        disclosures=['v12 rejected challenger network blobs and original trajectories/full traces were not archived. This seal does not reconstruct the full exploration path.',
            'Only selected-policy VAL replay is independently retained here; reused validation is model selection, not untouched performance evidence.',
            'CEM preliminary top-seven filtering averages returns over unequal observed TRAIN subsets; finalists and static incumbent are reranked on common TRAIN0..7 before VAL.',
            'Actual wall budget is soft; initialization and complete batches/rerank/validation may overrun the requested duration.',
            'Undiscounted shaping telescopes to a bounded scalar training surrogate. Validation key is lexicographic; action changes are descriptive, not a schedule-stability penalty.',
            'Worker simulation CPU excludes unisolated learner/orchestration/prior work; current runtime describes this evidence collection, not retrospectively the fit.',
            'Hashes ensure consistency, not trusted authorship or authenticity. Read-only files may still be replaced by their owner; verify the seal after transfer.'])
    write('report.json',json.dumps(report,indent=2).encode()+b'\n')
    manifest={str(path.relative_to(output)):digest(path.read_bytes()) for path in sorted(output.rglob('*')) if path.is_file()}
    seal_data=dict(schema='stage2-adaptive-evidence-seal.v1',files=manifest);seal_data['seal_sha256']=digest(canonical(seal_data))
    write('manifest.json',json.dumps(seal_data,indent=2).encode()+b'\n')
    for path in output.rglob('*'):
        if path.is_file():path.chmod(0o444)
    return report


def verify_seal(directory):
    directory=Path(directory).resolve();data=json.loads((directory/'manifest.json').read_bytes());expected=data.pop('seal_sha256')
    if digest(canonical(data))!=expected:raise ValueError('Manifest seal digest mismatch')
    actual={str(p.relative_to(directory)) for p in directory.rglob('*') if p.is_file() and str(p.relative_to(directory))!='manifest.json'}
    if actual!=set(data['files']):raise ValueError('Archive file set changed')
    for name,sha in data['files'].items():
        if digest(_safe_snapshot_path(directory,name).read_bytes())!=sha:raise ValueError('Archived file digest mismatch: '+name)
    return dict(valid=True,seal_sha256=expected,files=len(actual))


def main():
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('run',type=Path);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--execution-complete',action='store_true');p.add_argument('--replay',action='store_true')
    p.add_argument('--workers',type=int,default=1);p.add_argument('--training-runtime',type=Path)
    a=p.parse_args();report=seal(a.run,a.output,execution_complete=a.execution_complete,replay=a.replay,workers=a.workers,training_runtime=a.training_runtime)
    print(json.dumps(report,indent=2));return int(report['status']=='replay_mismatch')


if __name__=='__main__':raise SystemExit(main())
