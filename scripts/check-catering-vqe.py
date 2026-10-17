"""Independently recheck retained five-case VQE exports; never optimize or call services."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def audit(output):
    from catering.contracts import load_bundle
    from catering.run import evaluate
    output = Path(output)
    if output.exists():
        raise ValueError("Choose a fresh audit output")
    rows, sources = [], {}
    for case in ['cell', 'S0', 'S1', 'S2', 'S3']:
        base = ROOT / 'output/catering-methods/vqe/method-results' / case
        bundle_base = ROOT / ('output/catering-complete-cell-v3' if case == 'cell'
                              else f'output/catering-foundation-v3/{case}')
        bundle_path = bundle_base / 'quantum-qubo.json'
        bundle = load_bundle(bundle_path)
        result_path = base / 'result.json'
        result = json.loads(result_path.read_text())
        manifest = json.loads((base / 'artifacts.json').read_text())
        assert hashlib.sha256(result_path.read_bytes()).hexdigest() == manifest['files']['result.json']
        with tempfile.TemporaryDirectory() as tmp:
            checked = evaluate(bundle_path, result_path, Path(tmp) / 'evaluation.json')
            assert json.loads((Path(tmp) / 'evaluation.json').read_text()) == json.loads((base / 'evaluation.json').read_text())
        valid = [r for r in checked if r['valid']]
        assert valid
        best = min(valid, key=lambda r: tuple(r['check']['metrics'][k] for k in ['U', 'W', 'B', 'R']))
        ref = json.loads((bundle_base / ('reference-sector.json' if case == 'cell'
                                        else 'quantum-sector-reference.json')).read_text())
        reference_metrics = (ref.get('ground') or ref)['check']['metrics']
        assert best['check']['metrics'] == reference_metrics
        shots = sum(s['count'] for s in result['samples'])
        assert shots == 1024
        rows.append(dict(case=case, bundle_sha256=bundle['bundle_sha256'],
            sample_records=len(checked), shots=shots, valid_shots=sum(s['count'] for s in valid),
            best=best['check']['metrics'], work=result['work'],
            configuration=result['configuration'], exact_distribution=result['exact_distribution']))
        for path in [bundle_path, result_path, base/'evaluation.json', base/'artifacts.json']:
            sources[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    prior = json.loads((ROOT/'output/catering-methods/vqe/integration-v1/verification.json').read_text())
    receipt = dict(schema_version='catering-vqe-integration.v2', status='passed',
        source_commit='a3ce2135', checked_results=rows, source_files=sources,
        held_out_reported=prior['held_out_reported'], training_runs=0,
        physical_qpu_calls=0, veloxq_calls=0,
        limitations=[
            'All 5120 retained shot counts rechecked; exact probabilities are reported simulator diagnostics, not replayed without angles.',
            'E5 per-seed parameters/raw samples are absent; heldout CSV aggregates are reported evidence.',
            'Original circuit counts use an unvalidated two-shift heuristic; simulator adjoint work differs from QAOA work.',
            'Old integration-v1 remains historical; the teammate supplied a fresh cell export in the current five-case release.'])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True)+'\n')
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    r = audit(args.output)
    print(f"Checked {len(r['checked_results'])} exports, {sum(x['shots'] for x in r['checked_results'])} shots; no training/services.")
