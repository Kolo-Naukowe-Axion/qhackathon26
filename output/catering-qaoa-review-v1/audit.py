import sys, pathlib,json,tarfile,hashlib,collections,statistics,time
root=pathlib.Path('/tmp/axion-qaoa-review-path').read_text();root=pathlib.Path(root);sys.path.insert(0,str(root))
from catering.contracts import load_bundle
from catering.decode import decode
from catering.qubo import energy
from catering.methods.qaoa_campaign import summarize
base=root/'output/catering-methods/qaoa';plan=json.loads((base/'plan-v1.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
summary=dict(branch='iwosmu/catering-qaoa',commit='2ca4731a',training_rerun=False,bundles={},splits={})
for name,case in plan['cases'].items():
 b=load_bundle(root/case['bundle']);assert b['bundle_sha256']==case['bundle_sha256']
 summary['bundles'][name]=b['bundle_sha256']
for split in ['train','test']:
 with tarfile.open(base/'archives'/f'qaoa-{split}-v1-runs.tar.gz') as archive:
  for m in archive.getmembers():
   if not m.isfile() or not m.name.endswith('.json') or any(p.startswith('._') or p=='..' for p in pathlib.PurePosixPath(m.name).parts):continue
   target=base/m.name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(archive.extractfile(m).read())
 folder=base/(split+'-v1');manifest=json.loads((folder/'manifest.json').read_text())
 assert manifest['adapter_sha256']==sha(root/'catering/methods/qaoa.py')==plan['adapter_sha256']
 assert manifest['plan_sha256']==sha(base/'plan-v1.json')
 for name,h in manifest['files'].items():assert sha(folder/name)==h, name
 rows=json.loads((folder/'runs.json').read_text());checked=shots=stale=0
 actualrows=[]
 for row in rows:
  name=row['case'];case=plan['cases'][name];b=load_bundle(root/case['bundle'])
  directory=folder/name/f"{row['config']}-b{row['budget']}-s{row['seed']}"
  r=json.loads((directory/'result.json').read_text());t=json.loads((directory/'training.json').read_text())
  assert r['bundle_sha256']==b['bundle_sha256']
  assert r['configuration']['seed']==row['seed']
  assert len(t['trace'])==t['evaluations']==row['evaluations']==r['work']['training_objective_evaluations']
  assert t['evaluations']<=max(1,row['budget'])
  assert sum(s['count'] for s in r['samples'])==4096
  best=None;valid_shots=0
  for s in r['samples']:
   assert energy(b,s['bits'])==int(s['reported_energy'])
   d=decode(b,s['bits']);checked+=1;shots+=s['count']
   if d['valid']:
    valid_shots+=s['count'];score=tuple(d['check']['metrics'][k] for k in ['U','W','B','R'])
    best=min(best,score) if best else score
  assert list(best) if best else None == row['best_valid_tuple'] # explicit check below too
  assert (list(best) if best else None)==row['best_valid_tuple']
  assert valid_shots/4096==row['sampled_valid_fraction']
  for artifact in r['raw_artifacts']:
   if artifact['path'].endswith('/result.json') and artifact['sha256']!=sha(directory/'result.json'):stale+=1
  actualrows.append(row)
 regen=summarize(plan,actualrows,split)
 stored=json.loads((folder/'summary.json').read_text());assert regen==stored
 summary['splits'][split]=dict(runs=len(rows),manifest_files=len(manifest['files']),distinct_samples_checked=checked,shot_counts=shots,self_result_hash_stale=stale,
  frozen=[r for r in stored['table'] if r['config']=='frozen'])
 print(split,summary['splits'][split]['runs'],checked,shots,'self_hash_stale',stale,flush=True)
out=pathlib.Path('/Users/iwosmura/projects/qhackathon26/output/catering-qaoa-review-v1');out.mkdir(exist_ok=True)
(out/'verification.json').write_text(json.dumps(summary,indent=2)+'\n')
