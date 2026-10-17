"""Independent retained-final-evidence/source/trace replay, without factory run."""
import argparse
from copy import deepcopy
import json
import math
from pathlib import Path
import posixpath
import time

from stage2 import final_eval as evaluator
from stage2.check import check_trace
from stage2.compare_evaluations import load_evidence,select_rows,validate_payload
from stage2.identity_audit import audit_trace
from stage2.spec import build


SELECTIONS={'strong-cheap':'strong-cheap-selection.json','legacy':'legacy-selection-draft.json',
    'quantum-stochastic':'quantum-stochastic-selection.json','quantum-deterministic':'quantum-deterministic-selection.json',
    'frontier':'frontier-selection-draft.json',**{f'mpc-{n}':f'mpc-{n}-selection.json'for n in(12,13,14,16,24)}}


def close(left,right):
    if type(left)is dict:
        return type(right)is dict and set(left)==set(right) and all(close(v,right[k])for k,v in left.items())
    if type(left)is list:
        return type(right)is list and len(left)==len(right)and all(close(a,b)for a,b in zip(left,right))
    if type(left)is float and type(right)in(int,float):return math.isclose(left,right,rel_tol=1e-9,abs_tol=1e-5)
    return left==right


def expected_method(original,manifest,bundle):
    """Reconstruct freeze's declarations, keeping remote paths as opaque text."""
    remote_base=posixpath.dirname(manifest['selection_spec']['path'])
    expected=deepcopy(original)
    for key in('checkpoint','static_teacher'):
        if expected.get(key):expected[key]=posixpath.normpath(posixpath.join(remote_base,expected[key]))
    if 'threshold_bank'in expected:
        expected['threshold_bank']=[posixpath.normpath(posixpath.join(remote_base,path))for path in expected['threshold_bank']]
    if expected['kind']in('adaptive_recovery','adaptive_modes'):
        remote=expected['checkpoint'];local=deepcopy(expected)
        local['checkpoint']=str(bundle/original['checkpoint'])
        expected=evaluator._normalize_adaptive(local);expected['checkpoint']=remote
    if expected['kind']=='recovery_routing':expected['kind']='recovery'
    if expected['kind']=='recovery_mpc':expected['backend']='recovery'
    if expected['kind']in('advanced','specialist','tooling','kitting','recovery'):
        expected['backend']=expected['kind'];expected['kind']='static'
    if expected.get('backend')in('kitting','recovery'):expected.setdefault('kit_reservation',True)
    return expected


def audit(label,directory,*,replay=True):
    started=time.perf_counter();root=Path('output/stage2-search');bundle=root/'final-frozen-bundle-v20p2'
    index=json.loads((bundle/'global-freeze-index.json').read_text())
    manifest,evaluation,reference=load_evidence(directory);validate_payload(manifest,evaluation)
    assert manifest['evaluation_role']=='final'
    selection=SELECTIONS[label]
    assert manifest['selection_spec']['sha256']==index['files'][selection]
    assert manifest['protocol']['file_sha256']==index['files']['final-heldout-protocol.json']
    protocol=json.loads((bundle/'final-heldout-protocol.json').read_text())
    assert manifest['protocol']['payload']==protocol
    spec=json.loads((bundle/selection).read_text())
    assert manifest['configs']==spec['configs']and manifest['actor_seeds']==spec['actor_seeds']
    assert manifest['trace_policy']==spec['trace_policy']
    assert manifest['methods']==[expected_method(method,manifest,bundle)for method in spec['methods']]
    snapshot='v20-final-legacy'if label=='legacy'else'v20-final-current'
    source_manifest=json.loads((root/'snapshots'/snapshot/'manifest.json').read_text())
    assert evaluator.file_hash(root/'snapshots'/snapshot/'manifest.json')==index['source_snapshots'][snapshot]['manifest_sha256']
    for name,sha in manifest['source_hashes'].items():assert source_manifest['files'][name]==sha,(name,'frozen source mismatch')
    for remote,record in manifest['artifacts'].items():
        path=bundle/'checkpoints'/Path(remote).name
        assert evaluator.file_hash(path)==record['sha256']==index['files']['checkpoints/'+path.name]
    groups=[]
    for method in manifest['methods']:
        for config in method.get('configs',manifest['configs']):
            rows=select_rows(manifest,evaluation,method['id'],config)
            groups.append(dict(method_id=method['id'],config=config,rows=len(rows),valid=len(rows)))
    reconstructed=evaluator.summarize(evaluation['rows'],manifest)
    assert close(reconstructed,evaluation['summary']),'Cached final summary differs from reconstructed rows'
    assert evaluation['missing_or_invalid']==0
    for path in('stage2/check.py','stage2/spec.py','stage2/identity_audit.py'):
        assert evaluator.file_hash(evaluator.ROOT/path)==manifest['source_hashes'][path]
    trace_rows=[]
    expected_retained=0
    for row in evaluation['rows']:
        leaf=protocol['leaves'][row['leaf']]
        required=manifest['trace_policy']=='all'or(manifest['trace_policy']=='first_per_leaf'and row['seed']==leaf['seeds'][0]and row['policy_seed']==manifest['actor_seeds'][0])
        expected_retained+=int(required)
        assert ('trace_path'in row)==required,'Trace retention differs from frozen rule'
        if not required:continue
        path=Path(directory)/'traces'/Path(row['trace_path']).name
        assert evaluator.file_hash(path)==row['trace_sha256']
        trace=json.loads(path.read_text());anchor=build(**row['config'],seed=row['seed'])
        assert evaluator.digest(anchor)==row['physical_instance_sha256']==evaluator.digest(trace['instance'])
        assert close(trace['metrics'],row['metrics'])
        assert evaluator.qubo_telemetry(trace)==row['qubo_telemetry']
        if replay:
            checked=check_trace(trace,deepcopy(anchor));identity=audit_trace(trace,anchor)
            assert checked['valid']and checked['terminal_requirements_met']and identity['valid'],(checked['issues'],identity['issues'])
            assert close(checked['metrics'],row['checker_metrics']),'Independent trace replay metrics differ'
        trace_rows.append(dict(method_id=row['method_id'],config=row['config'],seed=row['seed'],actor_seed=row['policy_seed'],
            trace_path=path.name,sha256=row['trace_sha256'],fresh_numerical_instance_sha256=row['physical_instance_sha256'],
            replayed=replay,physical_and_identity_valid=True if replay else None))
    assert len(trace_rows)==expected_retained
    return dict(schema='stage2-independent-completed-final-group-audit.v1',valid=True,cohort=label,
        evidence=reference,global_freeze_index_sha256=evaluator.file_hash(bundle/'global-freeze-index.json'),
        selected_spec_sha256=index['files'][selection],manifest_sha256=manifest['manifest_sha256'],
        source_snapshot=snapshot,frozen_methods_exactly_reconstructed=True,protocol_sha256=protocol['protocol_sha256'],
        groups=groups,rows=len(evaluation['rows']),actors=manifest['actor_seeds'],
        cached_summary_matches_reconstruction=True,retained_traces=trace_rows,
        retained_trace_count=len(trace_rows),physical_replay_count=len(trace_rows)if replay else 0,
        wall_seconds=time.perf_counter()-started,audit_source_sha256=evaluator.file_hash(__file__),
        scope='Every outcome row passes complete-source/actor/instance/independent-metric gates. All predeclared retained traces are hash-checked and optionally physically replayed; unretained executions rely on their original per-row independent checks. No factory rerun, policy tuning or substituted final tape.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cohort',choices=SELECTIONS,required=True)
    parser.add_argument('--evidence',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--no-replay',action='store_true')
    args=parser.parse_args();result=audit(args.cohort,args.evidence,replay=not args.no_replay)
    with args.output.open('x')as stream:stream.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k]for k in('cohort','rows','retained_trace_count','physical_replay_count','wall_seconds')}))
