"""Verify package bytes and independently check its retained final executions.

No controller is run and no final performance sample is added. The manifest
detects changes relative to this package; it is not an external signature.
"""
from __future__ import annotations
import argparse,gzip,hashlib,json,math,time
from pathlib import Path


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def indexed_path(root,name,files):
    root=Path(root).resolve()
    path=(root/name).resolve()
    if name not in files or not path.is_relative_to(root) or not path.is_file():raise ValueError('Unindexed or escaping package file: '+name)
    return path


def close(actual,expected):
    if isinstance(expected,dict):return isinstance(actual,dict) and actual.keys()==expected.keys() and all(close(actual[k],v) for k,v in expected.items())
    if isinstance(expected,list):return isinstance(actual,list) and len(actual)==len(expected) and all(close(a,b) for a,b in zip(actual,expected))
    if type(expected) is float:return type(actual) in (float,int) and math.isclose(actual,expected,rel_tol=1e-8,abs_tol=1e-7)
    return type(actual) is type(expected) and actual==expected


def verify(directory):
    root=Path(directory).resolve();start=time.perf_counter()
    manifest=json.loads((root/'package-manifest.json').read_text())
    if manifest.get('schema')!='stage2-portable-evidence-package.v1':raise ValueError('Unsupported evidence package')
    for name,digest in manifest['files'].items():
        path=indexed_path(root,name,manifest['files'])
        if sha(path)!=digest:raise ValueError('Changed or missing package file: '+name)
    # Imports happen after checking literal package bytes. No simulation import
    # is necessary to independently replay the physical resource records.
    from stage2.spec import build
    from stage2.check import check_trace
    from stage2.identity_audit import audit_trace
    import sys
    for module_name in ('stage2.spec','stage2.check','stage2.identity_audit'):
        module=sys.modules[module_name];name=module_name.replace('.','/')+'.py'
        expected=indexed_path(root,name,manifest['files'])
        if Path(module.__file__).resolve()!=expected or sha(module.__file__)!=manifest['files'][name]:
            raise ValueError('Verifier imported a different runtime; run python <package>/verify_package.py <package> in a fresh process')
    results=[]
    replays=json.loads((root/'retained-replay-index.json').read_text())
    if len(replays)!=manifest['replays'] or len(replays)!=24:raise ValueError('Expected exactly24 predeclared final replays')
    for row in replays:
        path=indexed_path(root,row['path'],manifest['files'])
        if sha(path)!=row['compressed_sha256']:raise ValueError('Compressed replay hash differs')
        raw=gzip.decompress(path.read_bytes())
        if hashlib.sha256(raw).hexdigest()!=row['trace_sha256']:raise ValueError('Decompressed trace changed')
        trace=json.loads(raw);instance=build(**row['config'],seed=row['seed'])
        digest=hashlib.sha256(json.dumps(instance,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        if digest!=row['physical_instance_sha256'] or trace['instance']!=instance or trace['horizon_ticks']!=instance['horizon_ticks'] or trace['tick_minutes']!=instance['tick_minutes']:raise ValueError('Fresh physical instance anchor differs')
        checked=check_trace(trace,instance);identity=audit_trace(trace,instance)
        valid=checked['valid'] and checked['terminal_requirements_met'] and identity['valid'] and close(checked['metrics'],row['checker_metrics'])
        if not valid:raise ValueError('Independent replay verification failed: '+row['path'])
        results.append(dict(method=row['method'],seed=row['seed'],valid=True,shipped=checked['metrics']['delivered_orders'],missing=checked['metrics']['unfulfilled_orders']))
    return dict(schema='stage2-portable-verification.v1',valid=True,cohort_scope=manifest['cohort_scope'],files=len(manifest['files']),replays=results,wall_seconds=time.perf_counter()-start,
        scope='File integrity plus fresh-instance physical/identity/terminal/metric checks on24 predeclared retained traces; no new solver run, no population recomputation, no secondary optimality claim or external signature')


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('directory',nargs='?',type=Path,default=Path(__file__).resolve().parent);parser.add_argument('--output',type=Path)
    args=parser.parse_args();result=verify(args.directory)
    if args.output:
        if args.output.exists():raise ValueError('Preserve prior verification output')
        args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
