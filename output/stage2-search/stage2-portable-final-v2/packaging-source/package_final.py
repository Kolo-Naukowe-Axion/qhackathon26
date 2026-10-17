"""Portable selected-policy source and predeclared final replays, never a rerun.

Copies a frozen source directory, sealed policies and exactly the first retained
actor/tape per leaf for the preselected12/32 and matched QAOA12 demonstrations.
All original cohort evidence remains separately indexed; this smaller package
never replaces complete evaluation logs or permits selecting nicer final tapes.
"""
from __future__ import annotations
import argparse,gzip,hashlib,json,shutil,tarfile
from pathlib import Path
from .compare_evaluations import load_evidence,select_rows,file_hash


def copy_supplements(index,output):
    """Copy explicitly labeled audits without counting them as evaluation replays."""
    declaration=json.loads(Path(index).read_text());evidence=[]
    for name,item in declaration.items():
        if not name or Path(name).name!=name or name in ('.','..'):
            raise ValueError('Supplement labels must be single safe path components')
        origin=Path(item['path']).resolve();scope=item['scope']
        if not scope.strip():raise ValueError('Supplement needs an explicit interpretation scope')
        files=[origin] if origin.is_file() else sorted(p for p in origin.rglob('*') if p.is_file())
        if not files:raise ValueError('Empty audit supplement: '+name)
        copied=[]
        for p in files:
            if p.is_symlink() or not p.resolve().is_relative_to(origin if origin.is_dir() else origin.parent):
                raise ValueError('Audit supplements may not escape their declared source')
            relative=p.relative_to(origin) if origin.is_dir() else Path(p.name)
            target=Path(output)/'audit-supplements'/name/relative;target.parent.mkdir(parents=True,exist_ok=True)
            before=file_hash(p);shutil.copy2(p,target)
            if file_hash(target)!=before or file_hash(p)!=before:raise ValueError('Audit supplement changed while copying')
            copied.append(dict(path=str(target.relative_to(output)),sha256=before))
        evidence.append(dict(label=name,source=str(origin),scope=scope,files=copied))
    (Path(output)/'audit-supplement-index.json').write_text(json.dumps(evidence,indent=2)+'\n')
    return evidence


def package(index,source,bundle,report,output,*,allow_partial=False,supplements=None):
    paths=json.loads(Path(index).read_text());output=Path(output).resolve();output.mkdir(parents=True,exist_ok=False)
    source=Path(source).resolve();manifest=json.loads((source/'manifest.json').read_text())
    bundle=Path(bundle).resolve();seal=json.loads((bundle/'global-freeze-index.json').read_text())
    for name,sha in seal['files'].items():
        if file_hash(bundle/name)!=sha:raise ValueError('Changed globally frozen policy bundle: '+name)
    if file_hash(source/'manifest.json')!=seal['source_snapshots']['v20-final-current']['manifest_sha256']:
        raise ValueError('Portable current runtime differs from globally frozen selection')
    protocol=json.loads((bundle/'final-heldout-protocol.json').read_text())
    if protocol['total_tapes']!=256 or len(protocol['leaves'])!=8:raise ValueError('Declared complete 256-tape final protocol required')
    aggregation=json.loads((Path(report)/'report.json').read_text())
    if aggregation.get('schema')!='stage2-final-evidence-report.v1' or aggregation.get('protocol_sha256')!=protocol['protocol_sha256']:
        raise ValueError('Measured report does not match this frozen final protocol')
    if {k:str(Path(v).resolve()) for k,v in aggregation['inputs'].items()}!={k:str(Path(v).resolve()) for k,v in paths.items()}:
        raise ValueError('Measured report inputs differ from the supplied complete-cohort index')
    if aggregation['cohort_scope']!='complete' and not allow_partial:
        raise ValueError('Partial measured report requires explicit allow_partial packaging')
    for name,sha in manifest['files'].items():
        if file_hash(source/name)!=sha:raise ValueError('Changed source snapshot: '+name)
        target=output/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source/name,target)
    shutil.copy2(source/'manifest.json',output/'source-snapshot-manifest.json')
    shutil.copytree(bundle,output/'policies')
    shutil.copytree(report,output/'measured-results')
    (output/'packaging-source').mkdir()
    shutil.copy2(__file__,output/'packaging-source/package_final.py')
    shutil.copy2(Path(__file__).with_name('verify_package.py'),output/'verify_package.py')
    for name in ('requirements-inference.txt',):
        shutil.copy2(Path(__file__).parent/name,output/'stage2'/name)
    for name in ('LICENSE',):shutil.copy2(Path(__file__).resolve().parents[1]/name,output/name)
    retained=[];directory=output/'retained-replays';directory.mkdir()
    choices=(('strong-cheap','static-grid-12',dict(orders=12,horizon=5760,profile='full')),
             ('frontier','selected-stretch-32',dict(orders=32,horizon=14400,profile='full')),
             ('quantum-stochastic','no-batch-qaoa-12',dict(orders=12,horizon=5760,profile='full')))
    for label,method,config in choices:
        origin=Path(paths[label]).resolve();m,e,reference=load_evidence(origin);rows=select_rows(m,e,method,config)
        if m['evaluation_role']!='final' or m['protocol']['payload']!=protocol:
            raise ValueError('Replay is not from the globally frozen final protocol')
        for li,leaf in enumerate(m['protocol']['payload']['leaves']):
            chosen=[r for r in rows if r['seed']==leaf['seeds'][0] and r['policy_seed']==m['actor_seeds'][0]]
            if len(chosen)!=1 or 'trace_path' not in chosen[0]:raise ValueError('Predeclared first trace missing')
            row=chosen[0];p=origin/'traces'/Path(row['trace_path']).name;data=p.read_bytes()
            if hashlib.sha256(data).hexdigest()!=row['trace_sha256']:raise ValueError('Changed measured trace')
            target=directory/f'{method}-leaf{li}-seed{row["seed"]}.json.gz';target.write_bytes(gzip.compress(data,mtime=0))
            retained.append(dict(method=method,config=config,leaf=li,seed=row['seed'],actor_seed=row['policy_seed'],path=str(target.relative_to(output)),trace_sha256=row['trace_sha256'],compressed_sha256=file_hash(target),source_evidence=reference,
                physical_instance_sha256=row['physical_instance_sha256'],checker_metrics=row['checker_metrics'],
                selection_rule='First tape in protocol leaf, first declared actor; fixed before outcomes'))
    (output/'retained-replay-index.json').write_text(json.dumps(retained,indent=2)+'\n')
    supplemental=copy_supplements(supplements,output) if supplements else []
    readme='''# Frozen Stage2 evidence package

This is the pre-outcome selected policy/source bundle and measured result summaries.
The complete cohort manifests/evaluations/JSONL remain at the indexed source paths;
this smaller package retains all eight predeclared leaf replays for each of three
presentations. No prettier final tapes were selected. Read the result report for
uncertainty, failures, compute costs and proof scope. No quantum advantage or
physical-QPU execution is claimed.

Use Python3.12+ from this folder. Static and small QAOA execution use the standard
library; saved learned policy loading additionally needs NumPy2.5.4:

    python verify_package.py .
    python -m pip install -r stage2/requirements-inference.txt

Fresh development demo, all physical rules enabled (output must be new):

    python -m stage2.selected_run --selection policies/strong-cheap-selection.json --method static-grid-12 --orders 12 --seed 0 --output demo-static
    python -m stage2.selected_run --selection policies/strong-cheap-selection.json --method cem6-2026-16 --orders 16 --seed 0 --output demo-learned
    python -m stage2.selected_run --selection policies/quantum-stochastic-selection.json --method no-batch-qaoa-12 --orders 12 --seed 0 --output demo-qaoa

These are development replays, not new held-out estimates. The convenience command
rejects final seeds. Actual final comparisons used256 tapes with true leaf
probabilities and actors nested within tapes. Factory clock minutes differ from
execution wall time. QAOA samples only small fixed local dispatch pools; larger
ones use recorded classical fallback. Read retained-replay-index.json for exact
measured final replay hashes and frozen source provenance.

Verify all package files against package-manifest.json. The original global policy
freeze under policies/ remains unchanged. Local sources are copied from the frozen
current-dispatch runtime; legacy comparison summaries retain their separate source
identity. Replaying the legacy policies requires the separately indexed legacy
snapshot, not substituting this runtime. No upload, publication or deployment is
performed by packaging.

If present, audit-supplement-index.json labels separate offline certificates,
accounting and diagnostic evidence. Any posthoc witness or fresh development run
there is excluded from the256-tape estimates and the24 predeclared presentation
replays. Their presence never changes the sealed selection or policy scores.
'''
    if aggregation['cohort_scope']!='complete':
        readme='**PARTIAL provisional result package: some predeclared cohorts are still pending.**\n\n'+readme
    (output/'README.md').write_text(readme)
    files={str(p.relative_to(output)):file_hash(p) for p in sorted(output.rglob('*')) if p.is_file()}
    (output/'package-manifest.json').write_text(json.dumps(dict(schema='stage2-portable-evidence-package.v1',cohort_scope=aggregation['cohort_scope'],files=files,source_index_path=str(Path(index).resolve()),source_index_sha256=file_hash(index),packaging_sources={str(Path(__file__).name):file_hash(__file__),'requirements-inference.txt':file_hash(output/'stage2/requirements-inference.txt'),'LICENSE':file_hash(output/'LICENSE')},replays=len(retained),supplement_labels=[x['label'] for x in supplemental],scope='Selected sources and predeclared replays; full untrimmed experimental cohorts separately indexed; audit supplements separately scoped'),indent=2)+'\n')
    archive=output.with_suffix('.tar.gz')
    if archive.exists():raise ValueError('Preserve existing package archive')
    with tarfile.open(archive,'w:gz') as t:
        for p in sorted(output.rglob('*')):
            if p.is_file():t.add(p,arcname=str(p.relative_to(output)),recursive=False)
    return dict(path=str(output),archive=str(archive),archive_sha256=file_hash(archive),files=len(files)+1,replays=len(retained))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('index','source','bundle','report','output'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--allow-partial',action='store_true')
    p.add_argument('--supplements',type=Path,help='JSON mapping safe labels to path and interpretation scope')
    a=p.parse_args();print(json.dumps(package(a.index,a.source,a.bundle,a.report,a.output,allow_partial=a.allow_partial,supplements=a.supplements),indent=2))


if __name__=='__main__':main()
