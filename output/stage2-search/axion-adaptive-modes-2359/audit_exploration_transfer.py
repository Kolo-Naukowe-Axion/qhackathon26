"""Read-only hash/link audit of transferred complete18-action fit archives."""
from pathlib import Path
import gzip
import hashlib
import json
import sys


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':')).encode()


def audit(path):
    path=Path(path)
    artifact=json.loads((path/'selected-checkpoint.json').read_bytes())
    rows=[json.loads(line) for line in (path/'episodes.jsonl').read_text().splitlines()]
    policies=list((path/'policies').glob('*.json'))
    for file in policies:
        assert sha(canonical(json.loads(file.read_bytes())))==file.stem
    for row in rows:
        assert (path/'policies'/(row['policy_sha256']+'.json')).is_file()
        assert row['seed'] in (range(100,116) if row['phase']=='VALIDATION' else range(32))
    validation=[]
    sweeps=list(path.glob('validation-sweep*.jsonl'))
    for file in sweeps:
        batch=[json.loads(line) for line in file.read_text().splitlines()]
        assert len(batch)==48
        assert {(row['context_id'],row['seed']) for row in batch}=={(c,s) for c in range(3) for s in range(100,116)}
        for row in batch:
            assert sha(canonical(row['trajectory']))==row['trajectory_sha256']
            payload=(path/'validation-traces'/Path(row['trace_path']).name).read_bytes()
            assert sha(payload)==row['trace_gzip_sha256']
            raw=gzip.decompress(payload)
            assert sha(raw)==row['trace_sha256']
            assert json.loads(raw)['metrics']==row['metrics']
            assert row['valid']
        validation.extend(batch)
    assert len(sweeps)==artifact['validation_sweeps']
    assert len(validation)==artifact['validation_episodes']
    assert len(rows)==artifact['fit_episodes']+len(validation)
    assert sum(row['phase']=='VALIDATION' for row in rows)==len(validation)
    for name,expected in artifact['source_hashes'].items():
        assert sha((path/'source_snapshot'/name).read_bytes())==expected
    for policy,expected in zip(artifact['policies_by_context'],artifact['selected_policy_sha256'],strict=True):
        assert sha(canonical(policy))==expected
    return dict(valid=True,fit=path.name,source_hashes=artifact['source_hashes'],
        audit_source_sha256=sha(Path(__file__).read_bytes()),policies_verified=len(policies),
        all_logged_policy_links_verified=len(rows),
        all_validation_trajectories_full_traces_and_metrics_verified=len(validation),
        validation_sweeps=len(sweeps),original_remote_paths_resolved_locally_by_validated_basename=True,
        scope='Integrity/link/metric audit of every archived validation trace; not a second physical replay of every exploration episode',
        final_tapes=0)


if __name__=='__main__':
    result=audit(sys.argv[1])
    Path(sys.argv[2]).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
