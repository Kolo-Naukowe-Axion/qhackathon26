"""One declared posthoc proof illustration; never part of final estimates."""
import argparse
from copy import deepcopy
import json
import math
from pathlib import Path
import time

from stage2 import final_eval as f
from stage2.check import check_trace
from stage2.compare_evaluations import load_evidence,select_rows
from stage2.identity_audit import audit_trace
from stage2.quality_material_bound import certificate
from stage2.spec import build

ROOT=Path('output/stage2-search')
EVIDENCE=ROOT/'final-downloaded/final-frontier-6117515'
PROOFS=ROOT/'final-primary-certificates/selected-stretch-32'
OUTPUT=ROOT/'final-independent-audit/nontrivial-proof-seed10020'


def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':')).encode()


def write(name,value):
    path=OUTPUT/name
    with path.open('x')as stream:stream.write(json.dumps(value,indent=2)+'\n')


def close(left,right):
    if type(left)is dict:return type(right)is dict and set(left)==set(right)and all(close(v,right[k])for k,v in left.items())
    if type(left)is list:return type(right)is list and len(left)==len(right)and all(close(x,y)for x,y in zip(left,right))
    if type(left)is float:return type(right)in(int,float)and math.isclose(left,right,rel_tol=1e-9,abs_tol=1e-5)
    return left==right


def prepare():
    manifest,evaluation,reference=load_evidence(EVIDENCE)
    config=dict(orders=32,horizon=14400,profile='full')
    rows=select_rows(manifest,evaluation,'selected-stretch-32',config)
    report=json.loads((PROOFS/'report.json').read_text())
    choices=sorted(r['seed']for r in report['rows']if r['necessary_missing_lower_bound']>0 and any(
        a['actor_seed']==900000 and a['primary_optimum_attained']for a in r['actors']))
    if not choices or choices[0]!=10020:raise ValueError('Declared first-ascending illustration seed does not match completed evidence')
    original=next(r for r in rows if r['seed']==10020 and r['policy_seed']==900000)
    if 'trace_path'in original:raise ValueError('This illustration was expected outside original predeclared retained traces')
    if f.source_hashes()!=manifest['source_hashes']:raise ValueError('Current runtime differs from frozen final source')
    tasks=f.tasks(manifest,OUTPUT)
    task=next(t for t in tasks if t['method_id']=='selected-stretch-32'and t['seed']==10020 and t['policy_seed']==900000)
    modified=deepcopy(task);modified.update(save_trace=True,trace_path=str((OUTPUT/'audit-only-witness.json').resolve()))
    assert {k:v for k,v in modified.items()if k not in('save_trace','trace_path')}=={k:v for k,v in task.items()if k not in('save_trace','trace_path')}
    proof=next(r for r in report['rows']if r['seed']==10020)
    proof_path=PROOFS/proof['certificate_path']
    assert f.file_hash(proof_path)==proof['certificate_sha256']
    OUTPUT.mkdir(exist_ok=False)
    write('original-row.json',original);write('original-task.json',task);write('audit-only-task.json',modified)
    declaration=dict(schema='stage2-posthoc-proof-witness-declaration.v1',
        declared_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
        selection_rule='First ascending final seed with positive necessary missing lower bound attained by frozen selected-stretch-32 actor900000',
        selected_seed=10020,actor_seed=900000,method_id='selected-stretch-32',config=config,
        realized_missing=original['checker_metrics']['unfulfilled_orders'],necessary_lower_bound=proof['necessary_missing_lower_bound'],
        original_row_sha256=f.digest(original),original_task_sha256=f.digest(task),audit_only_task_sha256=f.digest(modified),
        original_evidence=reference,original_manifest_sha256=manifest['manifest_sha256'],
        original_physical_instance_sha256=original['physical_instance_sha256'],
        original_certificate=dict(path=str(proof_path),sha256=f.file_hash(proof_path)),
        global_freeze_index_sha256=f.file_hash(ROOT/'final-frozen-bundle-v20p2/global-freeze-index.json'),
        source_hashes=manifest['source_hashes'],audit_source_sha256=f.file_hash(__file__),
        comparison_tolerance=dict(relative=1e-9,absolute=1e-5),
        execution_plan='Exactly one f._execute call from original f.tasks; only save_trace and trace_path changed. No retry or substitute seed.',
        estimate_scope='Posthoc audit-only proof illustration, excluded from original256-tape estimates and original predeclared retained-trace counts; no tuning or new policy selection')
    write('declaration.json',declaration)
    return declaration


def execute():
    declaration=json.loads((OUTPUT/'declaration.json').read_text())
    assert f.file_hash(__file__)==declaration['audit_source_sha256']
    original=json.loads((OUTPUT/'original-row.json').read_text());task=json.loads((OUTPUT/'audit-only-task.json').read_text())
    assert f.digest(original)==declaration['original_row_sha256']and f.digest(task)==declaration['audit_only_task_sha256']
    assert f.source_hashes()==declaration['source_hashes']
    started=time.perf_counter()
    row=f._execute(task)
    write('audit-only-row.json',row)
    if not row['valid']or row.get('error'):raise ValueError('Audit-only replay invalid; evidence retained, no alternate seed')
    assert row['physical_instance_sha256']==declaration['original_physical_instance_sha256']==row['executed_instance_sha256']
    assert close(row['metrics'],original['metrics'])and close(row['checker_metrics'],original['checker_metrics'])
    trace=json.loads(Path(row['trace_path']).read_text());anchor=build(**declaration['config'],seed=10020)
    checked=check_trace(trace,deepcopy(anchor));identity=audit_trace(trace,anchor)
    assert checked['valid']and checked['terminal_requirements_met']and identity['valid']
    assert close(checked['metrics'],original['checker_metrics'])
    bound=certificate(anchor)
    expected=json.loads(Path(declaration['original_certificate']['path']).read_text())
    assert f.digest(bound)==f.digest(expected)
    upper=checked['metrics']['unfulfilled_orders'];lower=bound['unfulfilled_lower_bound']
    assert upper==lower==1
    write('independently-reconstructed-necessary-bound.json',bound)
    result=dict(schema='stage2-posthoc-proof-witness-result.v1',valid=True,posthoc_audit_only=True,
        declaration_sha256=f.file_hash(OUTPUT/'declaration.json'),original_row_sha256=declaration['original_row_sha256'],
        final_method_unchanged=True,final_source_unchanged=f.source_hashes()==declaration['source_hashes'],
        metrics_match_original=True,checker_metrics_match_original=True,canonical_identity_valid=True,
        actual_factory_replays=1,physical_instance_sha256=f.digest(anchor),
        seed=10020,actor_seed=900000,method_id='selected-stretch-32',
        full_witness_path=Path(row['trace_path']).name,full_witness_sha256=row['trace_sha256'],
        realized_orders=bound['observed_realized_orders'],checked_deliveries=checked['metrics']['delivered_orders'],
        necessary_missing_lower_bound=lower,checked_missing_upper_bound=upper,primary_optimum_attained=True,
        unknown_primary_gap_interval=[0,0],secondary_optimality_gap=None,
        independent_checker=checked,canonical_identity=identity,
        wall_seconds=time.perf_counter()-started,audit_source_sha256=f.file_hash(__file__),
        scope=declaration['estimate_scope'])
    write('report.json',result)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mode',choices=('declare','execute'));args=parser.parse_args()
    result=prepare()if args.mode=='declare'else execute()
    print(json.dumps({k:v for k,v in result.items()if k not in('source_hashes','independent_checker','canonical_identity')},indent=2))
