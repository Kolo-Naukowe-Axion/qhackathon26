"""Read-only verification of the globally frozen final policy bundle.

No factory simulation or policy selection is performed.
"""
from copy import deepcopy
import json
from pathlib import Path
import tarfile
import time

from stage2 import final_eval as evaluator


def audit():
    root=Path('output/stage2-search')
    bundle=root/'final-frozen-bundle-v20p2'
    index=json.loads((bundle/'global-freeze-index.json').read_text())
    submission=json.loads((root/'final-v20p2-submission.json').read_text())
    index_sha=evaluator.file_hash(bundle/'global-freeze-index.json')
    assert submission['global_freeze_index_sha256']==index_sha
    for name,expected in index['files'].items():
        assert evaluator.file_hash(bundle/name)==expected,name
    assert {str(p.relative_to(bundle))for p in bundle.rglob('*')if p.is_file()}==set(index['files'])|{'global-freeze-index.json'}
    snapshots={}
    for name,expected in index['source_snapshots'].items():
        folder=root/'snapshots'/name
        manifest=json.loads((folder/'manifest.json').read_text())
        assert evaluator.file_hash(folder/'manifest.json')==expected['manifest_sha256']
        for path,digest in manifest['files'].items():assert evaluator.file_hash(folder/path)==digest,path
        archive=folder.with_suffix('.tar.gz')
        assert evaluator.file_hash(archive)==expected['archive_sha256']
        with tarfile.open(archive) as stream:
            files={entry.name:stream.extractfile(entry).read()for entry in stream.getmembers()if entry.isfile()}
        assert set(files)==set(manifest['files'])|{'manifest.json'}
        for path,data in files.items():assert data==(folder/path).read_bytes(),path
        snapshots[name]=dict(files=len(manifest['files']),source_hashes=manifest['files'],
            manifest_sha256=expected['manifest_sha256'],archive_sha256=expected['archive_sha256'],archive_matches_directory=True)
    current=snapshots['v20-final-current']['source_hashes'];legacy=snapshots['v20-final-legacy']['source_hashes']
    physical=('stage2/engine.py','stage2/spec.py','stage2/check.py','stage2/identity_audit.py','instances/stage2/metaltech_pressure.json')
    assert all(current[path]==legacy[path]for path in physical)
    protocol=json.loads((bundle/'final-heldout-protocol.json').read_text())
    evaluator.validate_protocol(protocol)
    evaluator.validate_model_protocol(protocol,[dict(orders=12,horizon=5760,profile='full'),dict(orders=32,horizon=14400,profile='full')])
    assert protocol['total_tapes']==256 and len(protocol['leaves'])==8
    assert all(len(leaf['seeds'])==32 for leaf in protocol['leaves'])
    assert protocol['protocol_sha256']==index['protocol_payload_sha256']
    plan=json.loads((bundle/'predeclared-analysis-plan-v3.json').read_text())
    assert plan['protocol']['file_sha256']==evaluator.file_hash(bundle/'final-heldout-protocol.json')
    assert plan['protocol']['protocol_payload_sha256']==protocol['protocol_sha256']
    assert plan['created_utc']<index['frozen_utc']<submission['submitted_utc']
    quantum=[]
    for name,actors,count in [('quantum-deterministic-selection.json',[900000],6),('quantum-stochastic-selection.json',[900000,900001,900002],9)]:
        spec=json.loads((bundle/name).read_text());assert spec['actor_seeds']==actors and len(spec['methods'])==count
        quantum.extend(spec['methods'])
        for method in spec['methods']:
            provenance=method['selection_provenance']
            assert 'template_task_id'in provenance and 'task_id'not in provenance
            assert provenance['declared_override']['selector']==method['weights']['selector']
            assert provenance['cost_reference']=='compute-ledger.json'
            assert method['maintenance_outage_guard']is True and method['reward_mode']=='no-batch'
            assert method['kit_reservation']==(method['configs'][0]['orders']!=24)
    for orders in(12,16,24):
        methods=[m for m in quantum if m['configs'][0]['orders']==orders]
        assert len(methods)==5
        stripped=[]
        for method in methods:
            value=deepcopy(method);value.pop('id');value.pop('selection_provenance');value['weights'].pop('selector');stripped.append(value)
        assert all(value==stripped[0]for value in stripped)
    cheap=json.loads((bundle/'strong-cheap-selection.json').read_text())
    selected=json.loads((bundle/'selected-incumbent-map.json').read_text())
    assert {n:item['method_id']for n,item in selected['core'].items()}=={'12':'static-grid-12','16':'cem6-2026-16','24':'cem6-2026-24'}
    for n,item in selected['core'].items():
        methods=[m for m in cheap['methods']if m['id']==item['method_id']]
        assert len(methods)==1 and methods[0]['configs']==[dict(orders=int(n),horizon=5760,profile='full')]
    for orders,scenarios in((12,4),(13,2),(14,2),(16,2),(24,4)):
        spec=json.loads((bundle/f'mpc-{orders}-selection.json').read_text())
        assert spec['actor_seeds']==[900000] and len(spec['methods'])==1
        method=spec['methods'][0];options=method['mpc']
        assert method['maintenance_outage_guard']is True and options['physical_check_futures']is True
        assert options['risk_weight']==.25 and options['seed']==27491 and options['scenarios']==scenarios and options['interval']==1440
    ledger=json.loads((bundle/'compute-ledger.json').read_text())
    assert ledger['schema']=='stage2-compute-ledger.v1'
    assert len(submission['jobs'])==10
    assert all(job['gpus']==0 and job['cpus']==32 for job in submission['jobs'].values())
    return dict(schema='stage2-independent-global-final-seal-audit.v1',valid=True,
        audited_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),bundle=str(bundle),
        global_index_sha256=index_sha,globally_indexed_files=len(index['files']),source_snapshots=snapshots,
        physical_and_identity_source_groups_equal=True,protocol_file_sha256=evaluator.file_hash(bundle/'final-heldout-protocol.json'),
        protocol_payload_sha256=protocol['protocol_sha256'],tapes=256,exogenous_leaves=8,
        plan_frozen_before_submission=True,quantum_template_override_provenance_fixed=True,
        quantum_outer_controls_exactly_equal_except_selector=True,quantum_stochastic_actors=[900000,900001,900002],
        selected_incumbents=selected['core'],compute_ledger_materialized=True,
        ledger_scope='Immutable pre-final accounting snapshot; includes partial/running jobs asof earlier timestamps. Final accounting must be a separate sidecar, not a rewrite.',
        physical_or_future_quality_outcomes_read=False,factory_simulations_executed=0,
        audit_source_sha256=evaluator.file_hash(__file__),
        scope='Local global-bundle/source/archive/plan/selection/launch integrity; remote job completion and retained final result replay audited separately')


if __name__=='__main__':
    result=audit()
    output=Path(__file__).with_name('bundle-report.json')
    with output.open('x')as stream:stream.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items()if k!='source_snapshots'},indent=2))
