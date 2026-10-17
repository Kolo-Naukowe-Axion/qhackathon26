"""Strict paired comparisons across frozen evaluator source groups.

Remote absolute paths are opaque provenance, never dereferenced. This validates
retained evidence consistency; it does not replace physical replay or authenticate
fabricated files. Algorithm-source differences are disclosed, not hidden.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path

from .statistics import paired_report

SCHEMA='stage2-frozen-selected-policy-evaluation.v1'
PHYSICAL_SOURCES=('stage2/engine.py','stage2/spec.py','stage2/check.py','instances/stage2/metaltech_pressure.json')
METRICS=dict(missing='unfulfilled_orders',deadline_debt='terminal_deadline_debt_ticks',
             delivered_tardiness='tardiness_ticks',total_cost='total_cost',carbon_kg='carbon_kg')


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def file_hash(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def valid_hash(value):
    return isinstance(value,str) and len(value)==64 and all(char in '0123456789abcdef' for char in value)


def validate_protocol(protocol):
    payload=deepcopy(protocol);expected=payload.pop('protocol_sha256',None)
    if hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()!=expected:
        raise ValueError('Protocol digest changed')
    seeds={};mass=Fraction(0)
    for index,leaf in enumerate(protocol['leaves']):
        probability=Fraction(*leaf['probability'])
        if probability<=0 or not leaf['seeds']:raise ValueError('Positive populated leaves required')
        weight=float(probability/len(leaf['seeds']))
        if not math.isfinite(leaf['per_tape_weight']) or abs(weight-leaf['per_tape_weight'])>1e-14:
            raise ValueError('Protocol probability weight mismatch')
        for seed in leaf['seeds']:
            if type(seed) is not int or seed in seeds:raise ValueError('Unique integer tapes required')
            seeds[seed]=(index,leaf['outcomes'],weight)
        mass+=probability
    if mass!=1 or len(seeds)!=protocol['total_tapes']:raise ValueError('Protocol mass/count mismatch')
    return seeds


def _artifact_hashes(method,manifest):
    paths=[method[key] for key in ('checkpoint','static_teacher') if method.get(key)]
    paths+=method.get('threshold_bank',[])
    return {path:manifest['artifacts'][path]['sha256'] for path in paths}


def validate_payload(manifest,evaluation):
    """No imports or file checks against the execution host's absolute paths."""
    if manifest.get('schema')!=SCHEMA or manifest.get('phase')!='frozen-selection' or evaluation.get('schema')!=SCHEMA:
        raise ValueError('Frozen evaluator manifest and completed evaluation required')
    unsigned=deepcopy(manifest);sealed=unsigned.pop('manifest_sha256',None)
    if digest(unsigned)!=sealed:raise ValueError('Manifest seal mismatch')
    if evaluation.get('manifest_sha256')!=sealed:raise ValueError('Evaluation/manifest identity mismatch')
    if evaluation.get('evaluation_role')!=manifest.get('evaluation_role'):raise ValueError('Evaluation role mismatch')
    protocol=manifest['protocol']['payload'];seeds=validate_protocol(protocol)
    role=manifest.get('evaluation_role')
    if role not in ('development','final'):raise ValueError('Explicit development/final role required')
    schema='stage2-development-protocol.v1' if role=='development' else 'stage2-stratified-final-protocol.v1'
    if protocol.get('schema')!=schema:raise ValueError('Protocol schema differs from evidence role')
    if role=='development' and any(seed not in set(range(32))|set(range(100,116)) for seed in seeds):
        raise ValueError('Undeclared development tapes')
    if role=='final' and any(seed<10000 for seed in seeds):raise ValueError('Final protocol uses development tapes')
    if evaluation.get('protocol_sha256')!=protocol['protocol_sha256']:raise ValueError('Evaluation protocol mismatch')
    sources=manifest['source_hashes']
    if evaluation.get('source_hashes')!=sources:raise ValueError('Evaluation source group mismatch')
    if any(not valid_hash(sources.get(name)) for name in PHYSICAL_SOURCES):raise ValueError('Complete physical/verifier source hashes required')
    actors=manifest['actor_seeds']
    if not actors or len(set(actors))!=len(actors) or any(type(actor) is not int for actor in actors):raise ValueError('Unique declared actor seeds required')
    if len(actors)>1 and not manifest.get('actor_seed_policy'):raise ValueError('Multi-actor evidence lacks override contract; inherited fixed-seed replication is unsafe')
    methods={method['id']:method for method in manifest['methods']}
    if len(methods)!=len(manifest['methods']):raise ValueError('Duplicate method identity')
    configs=manifest['configs'];expected=set()
    for method in methods.values():
        for config in method.get('configs',configs):
            if config not in configs:raise ValueError('Method config not declared')
            for seed in seeds:
                for actor in actors:expected.add((method['id'],digest(config),seed,actor))
    rows=evaluation['rows']
    if evaluation.get('actual_rows')!=len(rows) or evaluation.get('expected_rows')!=len(expected):raise ValueError('Evaluation row-count metadata mismatch')
    observed=set()
    for row in rows:
        key=(row['method_id'],digest(row['config']),row['seed'],row['policy_seed'])
        if key not in expected or key in observed:raise ValueError('Unexpected or duplicate execution row')
        observed.add(key)
        if row.get('manifest_sha256')!=sealed or row.get('protocol_sha256')!=protocol['protocol_sha256']:
            raise ValueError('Row manifest/protocol mismatch')
        leaf,outcomes,weight=seeds[row['seed']]
        if row.get('leaf')!=leaf or row.get('leaf_outcomes')!=outcomes or row.get('tape_id')!=f"leaf-{leaf}:seed-{row['seed']}":
            raise ValueError('Row tape/leaf identity mismatch')
        if not math.isfinite(row['tape_weight']) or abs(row['tape_weight']-weight)>1e-14:raise ValueError('Row tape weight mismatch')
        if row.get('checker_sha256')!=sources['stage2/check.py']:raise ValueError('Row verifier source mismatch')
        if row.get('checkpoint_sha256')!=_artifact_hashes(methods[row['method_id']],manifest):raise ValueError('Row checkpoint identity mismatch')
        if type(row.get('valid')) is not bool:raise ValueError('Explicit row validity required')
    if observed!=expected:raise ValueError('Missing executions; never compare valid-only subsets')
    return protocol


def select_rows(manifest,evaluation,method_id,config):
    validate_payload(manifest,evaluation)
    methods={method['id']:method for method in manifest['methods']}
    if method_id not in methods or config not in methods[method_id].get('configs',manifest['configs']):
        raise ValueError('Requested method/config was not predeclared')
    rows=[row for row in evaluation['rows'] if row['method_id']==method_id and row['config']==config]
    for row in rows:
        if row['valid'] is not True or row.get('error') or row.get('issues'):
            raise ValueError('Selected group has failed/invalid execution; performance comparison suppressed')
        if row.get('terminal_requirements_met') is not True:raise ValueError('Terminal feasibility not independently recorded')
        identity_source=manifest['source_hashes'].get('stage2/identity_audit.py')
        if identity_source is not None:
            identity=row.get('identity_audit',{})
            if (identity.get('valid') is not True or identity.get('issues') or
                identity.get('provenance',{}).get('auditor_sha256')!=identity_source or
                identity.get('provenance',{}).get('instance_anchor')!='supplied_instance'):
                raise ValueError('Canonical identity supplement is missing, invalid or not anchored to its frozen auditor')
        physical=row.get('physical_instance_sha256')
        if not valid_hash(physical) or row.get('executed_instance_sha256')!=physical:
            raise ValueError('Executed numerical instance not anchored to frozen input')
        checked=row.get('checker_metrics',row.get('independently_reconstructed_metrics'))
        if not isinstance(checked,dict):raise ValueError('Full independent checker metrics required; legacy cached summaries are insufficient')
        for metric in METRICS.values():
            value=checked.get(metric)
            if type(value) not in (int,float) or not math.isfinite(value) or value<0:raise ValueError('Finite nonnegative independently checked metrics required')
        if type(checked.get('delivered_orders')) is not int or type(checked['unfulfilled_orders']) is not int:
            raise ValueError('Integer independent order counts required')
        verified=dict(orders=checked['delivered_orders']+checked['unfulfilled_orders'],shipped=checked['delivered_orders'],
            total_tardiness_ticks=checked['terminal_deadline_debt_ticks'],total_cost=checked['total_cost'],carbon_kg=checked['carbon_kg'],
            all_orders_fulfilled=checked['unfulfilled_orders']==0,terminal_soc_satisfied=True)
        if type(row.get('metrics')) is not dict:raise ValueError('Simulator outcome record missing')
        for key,value in verified.items():
            cached=row['metrics'].get(key)
            if type(value) is bool:
                agree=cached is value
            elif type(cached) in (int,float):agree=math.isclose(cached,value,rel_tol=1e-9,abs_tol=1e-5)
            else:agree=False
            if not agree:raise ValueError('Cached and independent metrics disagree: '+key)
    return rows


def compare_payloads(left_manifest,left_evaluation,left_method,right_manifest,right_evaluation,right_method,config,*,bootstrap=2000,seed=60819):
    if type(bootstrap) is not int or bootstrap<0:raise ValueError('Nonnegative integer bootstrap count required')
    left=select_rows(left_manifest,left_evaluation,left_method,config)
    right=select_rows(right_manifest,right_evaluation,right_method,config)
    lp=left_manifest['protocol']['payload'];rp=right_manifest['protocol']['payload']
    if digest(lp)!=digest(rp):raise ValueError('Cross-report comparison requires the identical predeclared protocol')
    if left_manifest['evaluation_role']!=right_manifest['evaluation_role']:raise ValueError('Development/final evidence cannot be pooled')
    changed={name:dict(left=left_manifest['source_hashes'].get(name),right=right_manifest['source_hashes'].get(name))
             for name in sorted(set(left_manifest['source_hashes'])|set(right_manifest['source_hashes']))
             if left_manifest['source_hashes'].get(name)!=right_manifest['source_hashes'].get(name)}
    forbidden=set(changed)&set(PHYSICAL_SOURCES)
    if 'stage2/identity_audit.py' in changed:forbidden.add('stage2/identity_audit.py')
    if forbidden:raise ValueError('Physical/verifier source groups differ: '+','.join(sorted(forbidden)))
    def instances(rows):
        answer={}
        for row in rows:
            current=(row['physical_instance_sha256'],row['checker_metrics']['delivered_orders']+row['checker_metrics']['unfulfilled_orders'])
            if row['seed'] in answer and answer[row['seed']]!=current:raise ValueError('Actor replicas have different physical instances or demand')
            answer[row['seed']]=current
        return answer
    # Normalize the accepted alternate full-metric field on copies, never inputs.
    left=deepcopy(left);right=deepcopy(right)
    for row in left+right:row.setdefault('checker_metrics',row.get('independently_reconstructed_metrics'))
    if instances(left)!=instances(right):raise ValueError('Per-tape physical instances or mandatory demand differ')
    comparisons={name:paired_report(left,right,lp,lambda row,key=key:row['checker_metrics'][key],bootstrap,seed)
                 for name,key in METRICS.items()}
    return dict(schema='stage2-cross-source-paired-evidence.v1',evaluation_role=left_manifest['evaluation_role'],config=config,
        left=dict(method_id=left_method,manifest_sha256=left_manifest['manifest_sha256'],actor_seeds=left_manifest['actor_seeds'],
            method=next(method for method in left_manifest['methods'] if method['id']==left_method),
            freeze_runtime=left_manifest.get('runtime'),execution_runtime=left_evaluation.get('runtime')),
        right=dict(method_id=right_method,manifest_sha256=right_manifest['manifest_sha256'],actor_seeds=right_manifest['actor_seeds'],
            method=next(method for method in right_manifest['methods'] if method['id']==right_method),
            freeze_runtime=right_manifest.get('runtime'),execution_runtime=right_evaluation.get('runtime')),
        protocol_sha256=lp['protocol_sha256'],physical_sources={name:left_manifest['source_hashes'][name] for name in PHYSICAL_SOURCES},
        supplemental_verifier_sources={name:left_manifest['source_hashes'][name] for name in ('stage2/identity_audit.py',) if name in left_manifest['source_hashes']},
        algorithm_source_differences=changed,metrics=comparisons,
        execution_runtime_equal=left_evaluation.get('runtime')==right_evaluation.get('runtime'),
        freeze_execution_runtime_drift=dict(left=left_manifest.get('runtime')!=left_evaluation.get('runtime'),right=right_manifest.get('runtime')!=right_evaluation.get('runtime')),
        direction='Right minus left; negative favors right for all reported losses',
        cost_scope='Training/teacher/planning and inference costs remain per-manifest provenance; no wall-time speedup metric or cross-hardware normalization',
        limitation='Consistency gate over retained evaluator evidence, not new physical replay/authentication; fixed observed actor cohorts, empirical tape-cluster bootstrap; intervals are pointwise, not multiplicity-corrected; no universal policy/global-gap claim')


def load_evidence(path):
    directory=Path(path).resolve();directory=directory.parent if directory.is_file() else directory
    files={name:directory/name for name in ('manifest.json','evaluation.json','rows.jsonl')}
    manifest=json.loads(files['manifest.json'].read_text());evaluation=json.loads(files['evaluation.json'].read_text())
    logged=[json.loads(line) for line in files['rows.jsonl'].read_text().splitlines() if line.strip()]
    if sorted(digest(row) for row in logged)!=sorted(digest(row) for row in evaluation['rows']):raise ValueError('rows.jsonl and evaluation.json disagree')
    evidence=dict(directory=str(directory),files={name:dict(path=str(path),sha256=file_hash(path)) for name,path in files.items()},
        remote_paths_scope='Stored absolute checkpoint/selection/trace paths are opaque provenance; remote files are not opened')
    return manifest,evaluation,evidence


def compare(left,left_method,right,right_method,config,*,bootstrap=2000,seed=60819):
    lm,le,lp=load_evidence(left);rm,re,rp=load_evidence(right)
    result=compare_payloads(lm,le,left_method,rm,re,right_method,config,bootstrap=bootstrap,seed=seed)
    result['source_evidence']=dict(left=lp,right=rp)
    result['aggregator_sha256']=file_hash(__file__)
    result['statistics_sha256']=file_hash(Path(__file__).with_name('statistics.py'))
    return result


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--left',type=Path,required=True);parser.add_argument('--left-method',required=True)
    parser.add_argument('--right',type=Path,required=True);parser.add_argument('--right-method',required=True)
    parser.add_argument('--config',required=True,help='Explicit JSON orders/horizon/profile object')
    parser.add_argument('--bootstrap',type=int,default=2000);parser.add_argument('--seed',type=int,default=60819)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args(argv)
    result=compare(args.left,args.left_method,args.right,args.right_method,json.loads(args.config),bootstrap=args.bootstrap,seed=args.seed)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x') as stream:stream.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(environment_tapes=result['metrics']['missing']['environment_tapes'],role=result['evaluation_role'],output=str(args.output))))


if __name__=='__main__':main()
