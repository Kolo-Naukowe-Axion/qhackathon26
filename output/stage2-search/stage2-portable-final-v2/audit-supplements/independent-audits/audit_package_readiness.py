"""Read-only readiness checks for a new compact package; no factory calls."""
import gzip
import hashlib
import json
from pathlib import Path
import tarfile
import time

BASE=Path(__file__).resolve().parents[1]
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def audit():
    began=time.perf_counter();package=BASE/'stage2-portable-final-v1';descriptor_path=BASE/'stage2-portable-final-v1-descriptor.json';descriptor=read(descriptor_path)
    manifest=read(package/'package-manifest.json');verification=read(BASE/descriptor['verification_report'])
    assert verification['valid'] and verification['cohort_scope']=='complete' and len(verification['replays'])==24
    assert sha(BASE/descriptor['verification_report'])==descriptor['verification_sha256']
    assert verification['files']==len(manifest['files'])==2335
    for name,digest in manifest['files'].items():assert sha(package/name)==digest,name
    assert sha(BASE/descriptor['archive'])==descriptor['archive_sha256']
    with tarfile.open(BASE/descriptor['archive']) as stream:
        members={member.name:member for member in stream.getmembers() if member.isfile()}
        assert set(members)==set(manifest['files'])|{'package-manifest.json'}
        assert json.loads(stream.extractfile(members['package-manifest.json']).read())==manifest
        for name,digest in manifest['files'].items():assert hashlib.sha256(stream.extractfile(members[name]).read()).hexdigest()==digest
    for name,stored in (('package_final.py','packaging-source/package_final.py'),('verify_package.py','verify_package.py')):
        assert sha(Path('stage2')/name)==sha(package/stored)
    bundle=BASE/'final-frozen-bundle-v20p2';global_index=read(bundle/'global-freeze-index.json')
    assert sha(bundle/'global-freeze-index.json')=='496e56ca28b89a94a2bc86a3dcabd22bcfe8ed09b6f82355a497ac959473f44f'
    for name,digest in global_index['files'].items():assert sha(bundle/name)==digest==sha(package/'policies'/name)
    snapshot=read(BASE/'snapshots/v20-final-current/manifest.json')
    for name,digest in snapshot['files'].items():assert sha(package/name)==digest==sha(BASE/'snapshots/v20-final-current'/name)
    final=read(BASE/'final-complete-report/report.json');stats=read(BASE/'final-independent-audit/complete-statistics-audit.json')
    assert sha(BASE/'final-complete-report/report.json')==stats['report_sha256']==sha(package/'measured-results/report.json')
    assert final['cohort_scope']=='complete' and final['groups']==74 and final['executions']==23552 and final['invalid_executions']==0 and len(final['comparisons'])==41
    assert read(BASE/'final-complete-index.json')==final['inputs']
    replays=read(package/'retained-replay-index.json');assert len(replays)==24
    protocol=read(bundle/'final-heldout-protocol.json');chosen={'static-grid-12':12,'selected-stretch-32':32,'no-batch-qaoa-12':12}
    observed=set()
    for row in replays:
        assert row['method'] in chosen and row['config']['orders']==chosen[row['method']]
        assert row['seed']==protocol['leaves'][row['leaf']]['seeds'][0] and row['actor_seed']==900000
        identity=(row['method'],row['leaf']);assert identity not in observed;observed.add(identity)
        payload=gzip.decompress((package/row['path']).read_bytes());assert hashlib.sha256(payload).hexdigest()==row['trace_sha256']
    full_descriptor=read(BASE/'final-full-evidence-v2.tar.gz.descriptor.json')
    assert sha(BASE/full_descriptor['archive'])==full_descriptor['archive_sha256']
    full_receipt=read(BASE/'final-full-evidence-v2-all-trace-audits-receipt.json')
    assert full_receipt['valid'] and full_receipt['archive_sha256']==full_descriptor['archive_sha256']
    assert full_receipt['complete_original_rows']==23552 and full_receipt['physical_replays']==592 and len(full_receipt['groups'])==10
    bound=read(Path('output/reference-bound-extension/seal.json'))
    for name,digest in bound['files'].items():assert sha(Path('output/reference-bound-extension')/name)==digest
    conditional=read(BASE/'final-conditional-leaves/output-index.json')
    for name,digest in conditional['files'].items():assert sha(BASE/'final-conditional-leaves'/name)==digest
    assert bound['new_arithmetic_lower_bound']==1482 and conditional['cells']==592
    return dict(schema='stage2-compact-package-readiness-audit.v1',ready=True,critical_defects=[],
                original_portable_v1_files_verified=2335,portable_archive_members_verified=2336,
                existing_predeclared_physical_verification_count=24,new_physical_replays=0,
                frozen_current_source_files=40,complete_final_groups=74,complete_final_rows=23552,
                complete_final_contrasts=41,full_v2_prior_physical_replay_receipt=592,
                source_hashes={name:sha(Path('stage2')/name) for name in ('package_final.py','verify_package.py')},
                portable_v1_archive_sha256=descriptor['archive_sha256'],full_v2_archive_sha256=full_descriptor['archive_sha256'],
                latest_reference_proof_seal_sha256=sha(Path('output/reference-bound-extension/seal.json')),
                conditional_output_index_sha256=sha(BASE/'final-conditional-leaves/output-index.json'),
                source_sha256=sha(__file__),factory_calls=0,new_jobs=0,wall_seconds=time.perf_counter()-began,
                build_guidance=['Create compactv2 at a new path and archive; preserve portablev1/fullv2 and their receipts',
                    'Copy latest arithmetic/conditional/progress/accounting as separately scoped supplements; do not rewrite frozen policy bundle or final report',
                    'Keep pending6117555 clearly pending until actual checked result arrives',
                    'Include later full-v2-all-trace-audits receipt: earlier reproduction receipt truthfully records only72 frontier replays at its timestamp',
                    'Run new package verifier in a fresh process using the packaged runtime; this checks24 retained traces, not population statistics or external authentication',
                    'As-of accounting must include its immutable ledger snapshot; current central ledger can advance',
                    'Legacy replay needs the separate legacy source snapshot; compact current-runtime demos do not reproduce legacy algorithms',
                    'No publication, submission, QPU execution, secondary global optimum or bitwise cross-host reproducibility follows from readiness'])


if __name__=='__main__':
    result=audit()
    with (Path(__file__).with_name('package-readiness-audit.json')).open('x') as stream:stream.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
