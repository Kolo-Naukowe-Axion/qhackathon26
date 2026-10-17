"""Bounded sensitivity diagnostic, not a generic four-bit/scaling benchmark."""
import copy
import hashlib
import json
from pathlib import Path
import random
import sys
import time
import traceback

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from stage2.rank_probe import structural_probe,independent_grid_score

OUT=Path(__file__).resolve().parent
baseline=json.loads((ROOT/'instances/instance_3x3.json').read_text())
source=(ROOT/'stage2/rank_probe.py').read_bytes()
(OUT/'rank_probe-source.py').write_bytes(source)
cases=[('official',copy.deepcopy(baseline),h)for h in (7,8,9,10,12)]
rng=random.Random(2026)
for case in range(8):
 instance=copy.deepcopy(baseline)
 for job in instance['jobs']:
  for operation in job['operations']:operation['duration']=rng.randint(1,4)
 durations=[[op['duration']for op in job['operations']]for job in instance['jobs']]
 lower=max(max(map(sum,durations)),max(sum(row[m]for row in durations)for m in range(3)))
 for extra in (0,1,3):cases.append((f'random-{case}',copy.deepcopy(instance),lower+extra))
results=[]
for index,(family,instance,horizon)in enumerate(cases):
 started=time.perf_counter();directory=OUT/f'case-{index:02}';directory.mkdir(exist_ok=False)
 (directory/'instance.json').write_text(json.dumps(instance,indent=2)+'\n')
 row=dict(index=index,family=family,horizon=horizon,durations=[[op['duration']for op in job['operations']]for job in instance['jobs']])
 try:
  report=structural_probe(instance,horizon,optimize_weights=False)
  # The generic helper's prose conclusion is specific to its original experiment;
  # use verified numerical fields, never repeat that sentence for new cases.
  report.pop('conclusion',None)
  (directory/'structural-proof.json').write_text(json.dumps(report,indent=2)+'\n')
  presolve=report['structural_presolve']
  row.update(accepted_by_compiler=True,formula_unsatisfiable=presolve.get('structural_formula_unsatisfiable',False),
   reduced_bits=presolve.get('reduced_bits'),forced_constants=presolve.get('forced_constants'),
   exact_quadratic=presolve.get('weighted_quadratic_exists',False),
   partial_dag_evaluations=report['partial_dag_evaluations'],
   verified_full_states=presolve.get('full_domain_exact_verification_states'))
 except Exception as error:
  row.update(accepted_by_compiler=False,exception=type(error).__name__,
   meaning='Construction or its exact validation rejected this case; no valid QUBO is claimed')
  (directory/'rejection.txt').write_text(traceback.format_exc())
 # Independent truth-table diagnostic is AFTER construction, and never feeds it.
 scores=[independent_grid_score(instance,[(state>>i)&1 for i in range(9)])for state in range(512)]
 valid=[score for score in scores if score is not None]
 row.update(optimal_makespan=min(valid),deadline_good_states=sum(score<=horizon for score in valid),
  independent_verification_states=512,elapsed_seconds=time.perf_counter()-started)
 if row.get('formula_unsatisfiable'):assert row['deadline_good_states']==0
 results.append(row)
assert (ROOT/'stage2/rank_probe.py').read_bytes()==source,'Source changed during diagnostic'
report=dict(schema='stage2-rank-structural-sensitivity.v1',
 protocol={'seed':2026,'random_matrices':8,'durations':[1,4],
  'random_deadlines':'max(job workload, machine workload) + {0,1,3}',
  'official_deadlines':[7,8,9,10,12],'construction_complete_schedule_scores':0,
  'verification_complete_order_bitstrings_per_case':512,'LP':False,
  'scope':'Only three jobs, three machines, fixed common route; duration/deadline sensitivity, not job-count scaling'},
 source_sha256=hashlib.sha256(source).hexdigest(),cases=results,
 summary={'cases':len(results),'accepted':sum(row['accepted_by_compiler']for row in results),
  'rejected':sum(not row['accepted_by_compiler']for row in results),
  'feasible_cases':sum(row['deadline_good_states']>0 for row in results),
  'accepted_feasible_at_most_five_bits':sum(row.get('exact_quadratic',False)and row.get('reduced_bits',99)<=5 and row['deadline_good_states']>0 for row in results)},
 limitations=['A rejection is failure of this restricted compiler, not proof that no alternative QUBO exists.',
  'A feasible candidate has exact exhaustive verification on this tiny domain; that verification is classical work.',
  'No physical QPU execution, scalability guarantee, quantum advantage or universal four-bit claim.'])
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report['summary'],indent=2))
print(json.dumps([row for row in results if row['family']=='official'],indent=2))
