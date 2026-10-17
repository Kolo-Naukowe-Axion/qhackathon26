"""Portable read-only audit of the frozen QAOA archives; no extraction or training."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def audit(output, full_samples=False):
    from catering.contracts import load_bundle
    from catering.decode import decode
    from catering.methods.qaoa_campaign import adapter_path, summarize
    output = Path(output)
    if output.exists():
        raise ValueError('Choose a fresh output')
    base = ROOT/'output/catering-methods/qaoa'
    plan_raw = (base/'plan-v1.json').read_bytes()
    plan = json.loads(plan_raw)
    frozen = adapter_path(plan['adapter_sha256'])
    bundles = {name: load_bundle(ROOT/case['bundle']) for name,case in plan['cases'].items()}
    for name,b in bundles.items():
        assert b['bundle_sha256'] == plan['cases'][name]['bundle_sha256']
    report = dict(schema='catering-qaoa-archive-check.v1', training_runs=0,
        service_calls=0, sample_check='fresh independent decoder' if full_samples else 'retained evaluator hashes',
        adapter_source=str(frozen.relative_to(ROOT)), adapter_sha256=plan['adapter_sha256'], splits={})
    cache = {name:{} for name in bundles}
    for split in ['train','test']:
        folder = base/(split+'-v1')
        manifest = json.loads((folder/'manifest.json').read_text())
        assert manifest['adapter_sha256'] == plan['adapter_sha256']
        assert manifest['plan_sha256'] == hashlib.sha256(plan_raw).hexdigest()
        rows = json.loads((folder/'runs.json').read_text())
        by_path = {f"{r['case']}/{r['config']}-b{r['budget']}-s{r['seed']}":r for r in rows}
        seen, found, stale = set(), {}, 0
        for name in ['runs.json','summary.json']:
            assert hashlib.sha256((folder/name).read_bytes()).hexdigest() == manifest['files'][name]
            seen.add(name)
        # Stream once. Never extract archive paths into the working tree.
        with tarfile.open(base/'archives'/f'qaoa-{split}-v1-runs.tar.gz', 'r|gz') as archive:
            for member in archive:
                path = PurePosixPath(member.name)
                if not member.isfile() or any(p.startswith('._') for p in path.parts):
                    continue
                if path.is_absolute() or '..' in path.parts or path.parts[0] != split+'-v1':
                    raise ValueError('Unexpected archive member')
                relative = str(PurePosixPath(*path.parts[1:]))
                if relative not in manifest['files']:
                    continue
                if relative in ['runs.json','summary.json']:
                    assert archive.extractfile(member).read() == (folder/relative).read_bytes()
                    continue
                assert relative not in seen
                raw = archive.extractfile(member).read()
                actual_hash = hashlib.sha256(raw).hexdigest()
                assert actual_hash == manifest['files'][relative], relative
                seen.add(relative)
                name,_,kind = relative.rpartition('/')
                row, data = by_path[name], json.loads(raw)
                checked = found.setdefault(name,{})
                if kind == 'training.json':
                    assert len(data['trace']) == data['evaluations'] == row['evaluations']
                    assert data['evaluations'] <= max(1,row['budget'])
                elif kind == 'evaluation.json':
                    valid = [s for s in data['samples'] if s['valid']]
                    valid_count = sum(s['count'] for s in valid)
                    assert valid_count/plan['shots'] == row['sampled_valid_fraction']
                    best = min((tuple(s['metrics'][k] for k in ['U','W','B','R']) for s in valid),default=None)
                    assert (list(best) if best is not None else None) == row['best_valid_tuple']
                    checked['evaluation'] = True
                elif kind == 'result.json':
                    b = bundles[row['case']]
                    assert data['bundle_sha256'] == b['bundle_sha256']
                    assert data['configuration']['seed'] == row['seed']
                    assert data['work']['training_objective_evaluations'] == row['evaluations']
                    shots = sum(s['count'] for s in data['samples'])
                    assert shots == plan['shots']
                    checked.update(shots=shots,records=len(data['samples']))
                    for artifact in data['raw_artifacts']:
                        if artifact['path'].endswith('/result.json') and artifact['sha256'] != actual_hash:
                            stale += 1
                    if full_samples:
                        valid_count, best = 0, None
                        for sample in data['samples']:
                            bits = tuple(sample['bits'])
                            if bits not in cache[row['case']]:
                                d = decode(b,list(bits))
                                cache[row['case']][bits] = (d['valid'],d['energy'],
                                    tuple(d['check']['metrics'][k] for k in ['U','W','B','R']) if d['valid'] else None)
                            valid, literal, metrics = cache[row['case']][bits]
                            assert int(literal) == int(sample['reported_energy'])
                            if valid:
                                valid_count += sample['count']
                                best = metrics if best is None else min(best,metrics)
                        assert valid_count/plan['shots'] == row['sampled_valid_fraction']
                        assert (list(best) if best is not None else None) == row['best_valid_tuple']
        assert seen == set(manifest['files']), sorted(set(manifest['files'])-seen)
        assert len(found) == len(rows) and all(r.get('evaluation') and 'shots' in r for r in found.values())
        assert summarize(plan,rows,split) == json.loads((folder/'summary.json').read_text())
        report['splits'][split] = dict(runs=len(rows),manifest_files=len(seen),
            returned_sample_records=sum(r['records'] for r in found.values()),
            shot_counts=sum(r['shots'] for r in found.values()),legacy_stale_self_hashes=stale)
        print(f"{split}: {len(rows)} runs, {len(seen)} archive file hashes verified",flush=True)
    report.update(status='passed',note='V1 stale embedded self-hashes are disclosed; immutable campaign manifests validate final archive bytes.')
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--full-samples',action='store_true',help='Also decode every raw return with the current physical checker')
    args = parser.parse_args()
    audit(args.output,args.full_samples)
