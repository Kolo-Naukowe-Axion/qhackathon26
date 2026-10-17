"""Reporting-only full final-evidence archive; never executes a factory/solver.

Payload paths preserve the repository layout. Every payload file is SHA256
indexed; a separate descriptor pins the manifest itself and compressed archive.
Checksums detect corruption, not external authorship or authenticity.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import time

ROOT=Path(__file__).resolve().parents[1]
PREFIX=Path('output/stage2-search')
MANIFEST='FINAL_EVIDENCE_MANIFEST.json'

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def encoded(value):return (json.dumps(value,indent=2)+'\n').encode()

def collect(root):
    base=root/PREFIX;index=json.loads((base/'final-complete-index.json').read_text());paths={}
    def add(path):
        path=Path(path)
        if path.is_symlink() or not path.is_file():raise ValueError('Regular nonsymlink evidence file required: '+str(path))
        rel=path.relative_to(root).as_posix()
        if any(x in path.parts for x in ('__pycache__','.git','.venv')) or path.suffix=='.pyc':return
        paths[rel]=path
    def tree(path):
        for p in sorted(Path(path).rglob('*')):
            if p.is_file() or p.is_symlink():add(p)
    snapshot=base/'snapshots/v20-final-current';current=json.loads((snapshot/'manifest.json').read_text())
    if len(current['files'])!=40:raise ValueError('Expected exact40-file frozen runtime')
    for name,h in current['files'].items():
        if sha(root/name)!=h:raise ValueError('Current frozen source drift: '+name)
        add(root/name)
    for name in ('stage2/final_report.py','stage2/full_evidence_archive.py','LICENSE'):add(root/name)
    if len(index)!=10:raise ValueError('All ten complete cohorts required')
    relative={}
    for label,p in index.items():
        source=Path(p)
        # The original index is retained verbatim; the new one is portable.
        if not source.is_relative_to(root):raise ValueError('Unexpected evidence outside authorized repository')
        rel=source.relative_to(root);relative[label]=rel.as_posix();tree(source)
    for name in ('final-frozen-bundle-v20p2','final-complete-report','final-independent-audit','final-primary-certificates'):
        tree(base/name)
    add(base/'final-complete-index.json');add(base/'final-frozen-bundle-v20p2.tar.gz')
    for name in ('v20-final-current','v20-final-legacy'):
        tree(base/'snapshots'/name);add(base/'snapshots'/(name+'.tar.gz'))
    compact=base/'axion-oracle-audit-v21p1-submission/compact-supplement'
    if compact.exists():tree(compact)
    return paths,relative,current

README="""# Full private Stage2 final evidence

This is an evidence/reproduction archive, not a newly selected policy, deployed
site, commit or publication. Run commands from this extracted directory. Python
3.12+ is required (including the pinned NumPy package); the tested runtime is recorded in the external verification
receipt. Aggregation and physical replay need NumPy only, not torch, SciPy,
OR-Tools, a GPU or quantum hardware. Installation needs a package index/cache;
after NumPy is available all reproduction below works offline.

    python -m pip install -r requirements-final-evidence.txt
    python -m stage2.full_evidence_archive verify --root .
    python -m stage2.final_report --index output/stage2-search/final-full-evidence-index-relative.json --output reproduced-final-report --bootstrap 2000
    python -m stage2.full_evidence_archive compare-report --output reproduced-final-report
    python -m stage2.full_evidence_archive audit-all --output reproduced-trace-audits

The last command invokes the unchanged audit_completed_group.py for all10
cohorts:592 predeclared retained traces. It reconstructs frozen selection and
source declarations, fresh numerical instances, and anchored physical/identity
checks. It never runs a factory or solver. For one cohort:

    PYTHONPATH=. python output/stage2-search/final-independent-audit/audit_completed_group.py --cohort frontier --evidence output/stage2-search/final-downloaded/final-frontier-6117515 --output reproduced-frontier-audit.json

Set PYTHONPATH=. if invoking that standalone script directly. The helper sets it
for you. Outputs must be new paths; never overwrite original evidence.

The root40 files exactly match v20-final-current. Both original40-file snapshot
trees and archives remain unchanged, including the separately frozen legacy
runtime. The current runtime is used for reporting and the common physical
checker; it is not presented as a rerun of the legacy policy implementation.
The original global bundle/index,10 untrimmed cohorts, complete original report,
original absolute index, and a NEW relative reproduction index are included.
Remote/original absolute paths embedded in manifests are opaque provenance;
the reproduction commands resolve actual input files through the relative index.

All23,552 final rows remain present, including all nested actors. The41 original
contrasts can be recomputed. Only the two predeclared n12 quantum missing-order
contrasts have the named primary family correction; others are exploratory.
592 predeclared traces are distinct from three separately declared posthoc
diagnostic traces under final-independent-audit. Those posthoc traces and the
separately labeled TRAIN-only neighborhood compact supplement never become new
samples in the original final estimates or substitutes for predeclared traces.

FINAL_EVIDENCE_MANIFEST.json hashes every payload file. Its own bytes and the
archive are pinned in the separate external descriptor, avoiding a circular
self-checksum. Hashes are not an external signature or proof of authorship.
The compact TRAIN supplement explicitly omits its large raw grid; the10 FINAL
cohorts in this archive are complete and untrimmed. MIT license is included.
"""

class HashReader:
    def __init__(self,file):self.file=file;self.hash=hashlib.sha256()
    def read(self,n=-1):
        b=self.file.read(n);self.hash.update(b);return b

def build(output,root=ROOT):
    began=time.perf_counter();root=Path(root).resolve();output=Path(output).resolve()
    if output.exists() or output.with_suffix(output.suffix+'.descriptor.json').exists():raise FileExistsError(output)
    output.parent.mkdir(parents=True,exist_ok=True)
    paths,relative,current=collect(root)
    generated={'README_FINAL_EVIDENCE.md':README.encode(),'requirements-final-evidence.txt':b'numpy==2.5.4\n',
        (PREFIX/'final-full-evidence-index-relative.json').as_posix():encoded(relative)}
    records={}
    with tarfile.open(output,'w:gz',compresslevel=3) as tar:
        for name,path in sorted(paths.items()):
            before=path.stat();info=tarfile.TarInfo(name);info.size=before.st_size;info.mode=0o644;info.mtime=int(before.st_mtime)
            with path.open('rb') as stream:
                reader=HashReader(stream);tar.addfile(info,reader)
            after=path.stat()
            if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):raise RuntimeError('Evidence changed while streaming: '+name)
            records[name]=dict(sha256=reader.hash.hexdigest(),bytes=before.st_size)
        for name,data in sorted(generated.items()):
            if name in records:raise ValueError('Generated path collision')
            info=tarfile.TarInfo(name);info.size=len(data);info.mode=0o644;tar.addfile(info,io.BytesIO(data));records[name]=dict(sha256=hashlib.sha256(data).hexdigest(),bytes=len(data))
        manifest=dict(schema='stage2-full-final-evidence.v1',role='Private evidence/reproduction only,not new selection or publication',
            files=records,frozen_current_files=current['files'],cohorts=relative,
            final_rows=23552,predeclared_retained_traces=592,posthoc_diagnostic_traces=3,contrasts=41,
            manifest_self_hash='Pinned by external archive descriptor; no circular self-hash',
            source_scope='Root40=current frozen runtime; legacy snapshot preserved separately; helper/reporting sources outside sealed40')
        payload=encoded(manifest);info=tarfile.TarInfo(MANIFEST);info.size=len(payload);info.mode=0o644;tar.addfile(info,io.BytesIO(payload))
    descriptor=dict(schema='stage2-full-final-evidence-archive-descriptor.v1',archive=output.name,archive_bytes=output.stat().st_size,
        archive_sha256=sha(output),manifest_member=MANIFEST,manifest_sha256=hashlib.sha256(payload).hexdigest(),
        payload_members=len(records),total_members=len(records)+1,payload_uncompressed_bytes=sum(r['bytes'] for r in records.values()),
        build_wall_seconds=time.perf_counter()-began,helper_sha256=sha(root/'stage2/full_evidence_archive.py'),
        authenticity='Local integrity metadata,not external signature; no upload or publication performed')
    output.with_suffix(output.suffix+'.descriptor.json').write_bytes(encoded(descriptor));return descriptor

def verify(root,descriptor=None):
    began=time.perf_counter();root=Path(root).resolve();p=root/MANIFEST;manifest=json.loads(p.read_text())
    if descriptor:
        d=json.loads(Path(descriptor).read_text())
        if sha(p)!=d['manifest_sha256']:raise ValueError('Manifest external seal mismatch')
    for name,r in manifest['files'].items():
        rel=Path(name)
        if rel.is_absolute() or '..' in rel.parts:raise ValueError('Unsafe member path')
        f=root/rel
        if f.is_symlink() or not f.is_file() or f.stat().st_size!=r['bytes'] or sha(f)!=r['sha256']:raise ValueError('Payload mismatch: '+name)
    return dict(valid=True,members_verified=len(manifest['files']),manifest_sha256=sha(p),wall_seconds=time.perf_counter()-began,
        external_manifest_seal_checked=descriptor is not None)

def repack(source,output,root=ROOT):
    """Preserve v1 science byte-for-byte while repairing packaging text/helper."""
    began=time.perf_counter();source=Path(source).resolve();output=Path(output).resolve()
    if output.exists() or output.with_suffix(output.suffix+'.descriptor.json').exists():raise FileExistsError(output)
    parent=json.loads(source.with_suffix(source.suffix+'.descriptor.json').read_text())
    if sha(source)!=parent['archive_sha256']:raise ValueError('Parent archive seal mismatch')
    replacements={'README_FINAL_EVIDENCE.md':README.encode(),'stage2/full_evidence_archive.py':(Path(root)/'stage2/full_evidence_archive.py').read_bytes()}
    records={};changes={};manifest=None
    with tarfile.open(source,'r:gz') as old,tarfile.open(output,'w:gz',compresslevel=3) as new:
        for member in old:
            if not member.isfile() or Path(member.name).is_absolute() or '..' in Path(member.name).parts:raise ValueError('Unsafe parent member')
            with old.extractfile(member) as stream:
                if member.name==MANIFEST:
                    payload=stream.read()
                    if hashlib.sha256(payload).hexdigest()!=parent['manifest_sha256']:raise ValueError('Parent manifest seal mismatch')
                    manifest=json.loads(payload);continue
                if member.name in replacements:
                    original=stream.read();data=replacements[member.name];h=hashlib.sha256(original).hexdigest()
                    changes[member.name]=dict(old_sha256=h,new_sha256=hashlib.sha256(data).hexdigest())
                    member.size=len(data);new.addfile(member,io.BytesIO(data));records[member.name]=dict(sha256=hashlib.sha256(data).hexdigest(),bytes=len(data))
                else:
                    reader=HashReader(stream);new.addfile(member,reader);records[member.name]=dict(sha256=reader.hash.hexdigest(),bytes=member.size)
        if manifest is None or set(manifest['files'])!=set(records):raise ValueError('Parent payload membership mismatch')
        for name,r in records.items():
            expected=manifest['files'][name]
            if name in changes:
                if expected['sha256']!=changes[name]['old_sha256']:raise ValueError('Parent replacement seal mismatch')
            elif r!=expected:raise ValueError('Scientific payload changed: '+name)
        manifest['files']=records;manifest['packaging_revision']=dict(parent_manifest_sha256=parent['manifest_sha256'],
            reason='Python>=3.12 NumPy requirement and explicit standalone PYTHONPATH command; scientific payloads byte-identical',changed_payloads=changes)
        payload=encoded(manifest);info=tarfile.TarInfo(MANIFEST);info.size=len(payload);info.mode=0o644;new.addfile(info,io.BytesIO(payload))
    descriptor=dict(schema='stage2-full-final-evidence-archive-descriptor.v1',archive=output.name,archive_bytes=output.stat().st_size,
        archive_sha256=sha(output),manifest_member=MANIFEST,manifest_sha256=hashlib.sha256(payload).hexdigest(),
        payload_members=len(records),total_members=len(records)+1,payload_uncompressed_bytes=sum(r['bytes'] for r in records.values()),
        build_wall_seconds=time.perf_counter()-began,helper_sha256=sha(Path(root)/'stage2/full_evidence_archive.py'),
        parent_archive_sha256=parent['archive_sha256'],scientific_payloads_byte_identical=True,changed_payloads=changes,
        authenticity='Local integrity metadata,not external signature; no upload or publication performed')
    output.with_suffix(output.suffix+'.descriptor.json').write_bytes(encoded(descriptor));return descriptor

def compare_report(output,root=ROOT):
    original=root/PREFIX/'final-complete-report';output=Path(output)
    def clean(x):
        if isinstance(x,dict):return {k:clean(v) for k,v in x.items() if k!='source_evidence'}
        if isinstance(x,list):return [clean(v) for v in x]
        return x
    for name in ('all-groups.json','preselected-frontier.json'):
        if clean(json.loads((original/name).read_text()))!=clean(json.loads((output/name).read_text())):raise ValueError('Recomputed numeric payload mismatch: '+name)
    old=json.loads((original/'report.json').read_text());new=json.loads((output/'report.json').read_text())
    for r in (old,new):r.pop('inputs');r.pop('wall_seconds')
    if clean(old)!=clean(new):raise ValueError('Recomputed final report mismatch')
    files=sorted((original/'comparisons').glob('*.json'))
    if len(files)!=41:raise ValueError('Expected original41contrasts')
    for p in files:
        if clean(json.loads(p.read_text()))!=clean(json.loads((output/'comparisons'/p.name).read_text())):raise ValueError('Contrast numeric payload mismatch: '+p.name)
    return dict(valid=True,groups=74,rows=23552,contrasts=41,scope='Original numeric/statistical payloads exact; local evidence paths and aggregation elapsed time excluded')

def audit_all(output,root=ROOT):
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=False);root=Path(root).resolve()
    index=json.loads((root/PREFIX/'final-full-evidence-index-relative.json').read_text());env=dict(os.environ,PYTHONPATH=str(root))
    helper=root/PREFIX/'final-independent-audit/audit_completed_group.py';results=[]
    for label,path in index.items():
        destination=output/(label+'.json')
        subprocess.run([sys.executable,str(helper),'--cohort',label,'--evidence',path,'--output',str(destination)],cwd=root,env=env,check=True)
        results.append(json.loads(destination.read_text()))
    total=sum(r['physical_replay_count'] for r in results)
    if total!=592 or any(not r['valid'] for r in results):raise ValueError('Expected592valid predeclared trace audits')
    receipt=dict(valid=True,cohorts=10,physical_replays=total,no_factory_or_solver_runs=True)
    (output/'receipt.json').write_bytes(encoded(receipt));return receipt

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='action',required=True)
    b=sub.add_parser('build');b.add_argument('--output',type=Path,required=True)
    r=sub.add_parser('repack');r.add_argument('--source',type=Path,required=True);r.add_argument('--output',type=Path,required=True)
    v=sub.add_parser('verify');v.add_argument('--root',type=Path,default=ROOT);v.add_argument('--descriptor',type=Path)
    c=sub.add_parser('compare-report');c.add_argument('--output',type=Path,required=True)
    a=sub.add_parser('audit-all');a.add_argument('--output',type=Path,required=True)
    x=p.parse_args()
    if x.action=='build':result=build(x.output)
    elif x.action=='repack':result=repack(x.source,x.output)
    elif x.action=='verify':result=verify(x.root,x.descriptor)
    elif x.action=='compare-report':result=compare_report(x.output)
    else:result=audit_all(x.output)
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
