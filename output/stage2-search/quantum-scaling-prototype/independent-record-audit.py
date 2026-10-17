import hashlib,json,math
from pathlib import Path
from stage2.qubo import build_qubo,exact_reference
out=Path(__file__).parent;references={};checked=0
for bits,core in ((11,6),(19,13),(23,14)):
 data=json.loads((out/'inputs'/f'pool-total{bits}-core{core}.json').read_text());q=build_qubo(data['candidates'],data['conflicts'],data['capacities'])
 reference=exact_reference(q);references[str(bits)]=reference
 for p in (1,2):
  for seed in range(3):
   r=json.loads((out/f'pool{bits}-p{p}-seed{seed}.json').read_text())
   assert r['reference']['reward']==reference['reward']
   assert r['qubo']['variables']==bits and r['qubo']['core_variables']==core
   assert r['optimization']['evaluations']==32
   assert not r['quantum_executed'] and r['quantum_algorithm_simulated']
   assert r['source_sha256']['quantum_scaling.py']==hashlib.sha256((out/'source'/'quantum_scaling.py').read_bytes()).hexdigest()
   for control in (r,r['uniform']):
    assert sum(control['raw_counts'].values())==1024
    assert len(control['samples'])==len(control['raw_counts'])
    for sample in control['samples']:
     mask=int(sample['bitstring'],2);bits_array=[(mask>>i)&1 for i in range(q.size)];chosen=[i for i in range(core) if bits_array[i]]
     assert bits_array==sample['bits'] and chosen==sample['indices']
     assert sample['feasible']==q.feasible(chosen)
     assert math.isclose(sample['energy'],q.energy(bits_array),rel_tol=0,abs_tol=1e-8)
     assert sample['count']==control['raw_counts'][sample['bitstring']]
    chosen=[i for i,c in enumerate(q.candidates) if c.id in control['selected']]
    assert q.feasible(chosen) and control['feasible']
    if not control['repaired']:
     best=max((row for row in control['samples'] if row['feasible']),key=lambda row:(row['reward'],-row['energy'],row['count'],-row['state']))
     assert control['selected']==[q.candidates[i].id for i in best['indices']]
   checked+=1
report=dict(checked_runs=checked,scalar_core_exact_references=references,all_sample_energies_and_feasibility_replayed=True,selection_and_control_counts_checked=True,frozen_source_matches=True,no_physical_quantum_calls=True)
(out/'independent-record-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
