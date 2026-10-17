from copy import deepcopy
import gzip,hashlib,json
from pathlib import Path
from stage2.identity_audit import audit_trace
from stage2.check import check_trace
from stage2.spec import build
out=Path(__file__).parent
paths=sorted(Path('output/stage2-search/adaptive-recovery-independent-audit').glob('static-equivalence*.json.gz'))+sorted(Path('output/stage2-search/quality-material-primary-bound').glob('*-witness.json.gz'))+[Path('output/stage2-search/checked-qaoa-8/trace.json')]+sorted(Path('output/stage2-search/tiny-reference-final').glob('*/*-trace.json'))
rows=[]
for path in paths:
 payload=path.read_bytes();raw=gzip.decompress(payload) if path.suffix=='.gz' else payload;trace=json.loads(raw)
 if 'tiny-reference-final' in str(path):instance=deepcopy(trace['instance']);anchor='retained explicit tiny instance, not flagship build'
 else:instance=build(len(trace['instance']['orders']),trace['horizon_ticks'],trace['instance']['seed'],trace['instance'].get('profile','full'));anchor='fresh spec.build'
 physical=check_trace(trace,instance);identity=audit_trace(trace,instance)
 assert physical['valid'] and identity['valid'],(path,physical['issues'][:2],identity['issues'][:2])
 rows.append(dict(path=str(path.resolve()),stored_payload_sha256=hashlib.sha256(payload).hexdigest(),uncompressed_trace_sha256=hashlib.sha256(raw).hexdigest(),anchor=anchor,physical_valid=physical['valid'],identity=identity))
def rename(value,old,new):
 if isinstance(value,str):return value.replace(old,new)
 if isinstance(value,list):return [rename(v,old,new) for v in value]
 if isinstance(value,dict):return {rename(k,old,new):rename(v,old,new) for k,v in value.items()}
 return value
basepath=Path('output/stage2-search/adaptive-recovery-independent-audit/static-equivalence-n12-seed0-actor0.json.gz');trace=json.loads(gzip.decompress(basepath.read_bytes()));instance=deepcopy(trace['instance'])
for suffix in range(2,100):
 uid=f'P01/pump/{suffix}';draw=int.from_bytes(hashlib.sha256(f"{instance['seed']}:quality:{uid}:0".encode()).digest()[:8],'big')/2**64
 if draw>.025:break
corrupted=rename(trace,'P01/pump/1',uid)
for event in corrupted['events']:
 if event.get('type')=='qa_result' and event.get('unit_id')==uid:event['keyed_uniform']=draw
legacy=check_trace(corrupted,instance);supplement=audit_trace(corrupted,instance)
assert legacy['valid'] and not supplement['valid']
payload=json.dumps(corrupted,separators=(',',':')).encode();target=out/'adversarial-renamed-pump-legacy-accepted.json.gz';target.write_bytes(gzip.compress(payload,mtime=0))
report=dict(schema='canonical-identity-audit-evidence.v1',normal_traces=len(rows),all_normal_pass=True,rows=rows,
 adversarial=dict(input_path=str(basepath),renamed_from='P01/pump/1',renamed_to=uid,qa_uniform_recomputed=draw,legacy_physical_checker=legacy,supplement=supplement,trace_path=str(target),trace_sha256=hashlib.sha256(payload).hexdigest()),
 frozen_source_sha256={name:hashlib.sha256(Path('stage2',name).read_bytes()).hexdigest() for name in ('identity_audit.py','check.py','engine.py','spec.py')})
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(normal_traces=len(rows),all_normal_pass=True,adversarial_legacy_valid=legacy['valid'],adversarial_supplement_valid=supplement['valid'],adversarial_issues=supplement['issues'],sources=report['frozen_source_sha256']),indent=2))
