"""Seal all ten independently audited final cohorts without factory execution."""
import importlib.util
import json
from pathlib import Path
import time

from stage2 import final_eval as f

ROOT = Path(__file__).resolve().parent


def seal():
    started = time.perf_counter()
    index_path = ROOT.parent / 'final-complete-index.json'
    paths = json.loads(index_path.read_text())
    assert set(paths) == {'legacy', 'frontier', 'strong-cheap', 'quantum-stochastic',
                          'quantum-deterministic', 'mpc-12', 'mpc-13', 'mpc-14', 'mpc-16', 'mpc-24'}
    anchor_path = ROOT / 'complete-all-row-anchors.json'
    anchor = json.loads(anchor_path.read_text())
    assert anchor['valid'] and anchor['rows_verified'] == 23552
    assert anchor['distinct_configuration_tapes'] == 2048
    assert anchor['input_index_sha256'] == f.file_hash(index_path)
    entries = []
    for name, path in paths.items():
        evidence = Path(path).resolve()
        report_path = ROOT / (name + '-report.json')
        report = json.loads(report_path.read_text())
        assert report['valid'] and report['cohort'] == name
        assert Path(report['evidence']['directory']).resolve() == evidence
        for filename, item in report['evidence']['files'].items():
            assert f.file_hash(evidence / filename) == item['sha256']
        assert report['rows'] == anchor['cohort_rows'][name]
        assert report['retained_trace_count'] == report['physical_replay_count']
        assert report['retained_trace_count'] == len(report['retained_traces'])
        identities = set()
        for item in report['retained_traces']:
            assert item['replayed'] and item['physical_and_identity_valid']
            assert f.file_hash(evidence / 'traces' / item['trace_path']) == item['sha256']
            identity = (item['method_id'], f.digest(item['config']), item['seed'], item['actor_seed'])
            assert identity not in identities
            identities.add(identity)
        assert all(group['rows'] == group['valid'] for group in report['groups'])
        entries.append(dict(cohort=name, path=report_path.name, sha256=f.file_hash(report_path),
                            rows=report['rows'], groups=len(report['groups']),
                            original_retained_physical_replays=report['physical_replay_count']))
    assert sum(item['rows'] for item in entries) == 23552
    assert sum(item['groups'] for item in entries) == 74
    assert sum(item['original_retained_physical_replays'] for item in entries) == 592
    spec = importlib.util.spec_from_file_location('postfreeze_bundle_audit', ROOT / 'audit_bundle.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    bundle = module.audit()
    assert bundle['valid']
    assert bundle['global_index_sha256'] == '496e56ca28b89a94a2bc86a3dcabd22bcfe8ed09b6f82355a497ac959473f44f'
    assert all(json.loads((ROOT / (name + '-report.json')).read_text())['global_freeze_index_sha256'] == bundle['global_index_sha256'] for name in paths)
    assert all(json.loads((ROOT / (name + '-report.json')).read_text())['protocol_sha256'] == anchor['protocol_sha256'] for name in paths)
    return dict(schema='stage2-independent-complete-final-audits-seal.v1', valid=True,
                sealed_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                global_freeze_index_sha256=bundle['global_index_sha256'],
                protocol_sha256=anchor['protocol_sha256'], cohorts=entries,
                rows=23552, method_context_groups=74, original_retained_physical_replays=592,
                independent_environment_tapes_per_context=256, distinct_configuration_tapes=2048,
                evidence_index=dict(path=str(index_path), sha256=f.file_hash(index_path)),
                full_row_anchor_audit=dict(path=anchor_path.name, sha256=f.file_hash(anchor_path)),
                repeated_bundle_source_archive_seal_audit=bundle,
                extra_posthoc_proof_and_two_diagnostic_replays_excluded=True,
                pending=[], factory_simulations=0, wall_seconds=time.perf_counter()-started,
                seal_source_sha256=f.file_hash(__file__),
                limitations=['Integrity seal relative to recorded digests, not an external authenticated signature',
                             'All original executions were independently checked by the frozen evaluator; this audit physically replays only the592 predeclared retained traces',
                             'Actor replicas and methods are paired on the same256 environment tapes per context',
                             'No secondary global optimum or quantum advantage follows from physical validity',
                             'No upload, public-source publication or administrative submission is performed'])


if __name__ == '__main__':
    result = seal()
    with (ROOT / 'complete-audit-seal.json').open('x') as stream:
        stream.write(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: value for key, value in result.items()
                      if key not in ('cohorts', 'repeated_bundle_source_archive_seal_audit')}, indent=2))
