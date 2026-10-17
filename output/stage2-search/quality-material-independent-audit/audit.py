"""Independent narrow arithmetic audit; no controller and no schedule oracle."""
from copy import deepcopy
from fractions import Fraction
import hashlib
import importlib.util
import json
from itertools import combinations
from pathlib import Path
import random
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from stage2.quality_material_bound import certificate,material_relaxation

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def draw(key):return Fraction(int.from_bytes(hashlib.sha256(key.encode()).digest()[:8],'big'),2**64)

def main():
 source=ROOT/'stage2/quality_material_bound.py';before=digest(source)
 spec_source=ROOT/'output/stage2-search/snapshots/v7-kitting/stage2/spec.py'
 spec=importlib.util.spec_from_file_location('independent_frozen_quality_spec',spec_source)
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 instance=module.build(orders=32,horizon=14400,seed=6,profile='full')
 # Independently reconstruct only exogenous orders/delivery, without bound helpers.
 order_ids={row['id']for row in instance['orders']};arrival=instance['delivery']['normal_tick'];leaf=[]
 for index,stage in enumerate(instance['uncertainty_stages']):
  cumulative=Fraction(0);value=draw(f'6:stage:{index}')
  for outcome in stage['outcomes']:
   cumulative+=Fraction(*outcome['probability'])
   if value<cumulative:break
  leaf.append(outcome['id'])
  if stage['reveal_tick']>instance['horizon_ticks']:continue
  for event in outcome['events']:
   if event['type']=='urgent_orders':order_ids.update(f'U{j+1:02d}'for j in range(event['count']))
   if event['type']=='delivery_delay':arrival=event['new_tick']
 stock=instance['raw_stock_units']['housing']+(instance['delivery']['contents']['housing']if arrival<=instance['horizon_ticks']else 0)
 first=draw('6:quality:P05/housing/1:0');repair=draw('6:quality:P05/housing/1:1')
 heat=[row for row in instance['recipes']['housing']if row['process']=='HEAT'];assert len(heat)==1
 risks=[Fraction(str(instance['quality']['manufacturing_defect_probabilities']['HEAT'][mode]))for mode in instance['modes']['HEAT']]
 assert first<min(risks)-Fraction(1,10**10)
 assert repair<Fraction(str(instance['quality']['repair_residual_probability']))-Fraction(1,10**10)
 assert len(order_ids)==34 and stock==34
 assert len(order_ids)+1>stock
 full=certificate(instance)
 assert full['observed_realized_orders']==len(order_ids)
 assert full['available_raw_blanks']['housing']==stock
 assert full['necessary_blank_demands']['P05']==(2,1,1)
 assert full['unfulfilled_lower_bound']==1
 mutations={
  'additional_repairs':lambda x:x['quality'].update(max_repairs_per_component_attempt=2),
  'additional_replacements':lambda x:x['quality'].update(max_replacements_per_original_component=2),
  'preprocessed_nonraw_units':lambda x:x['units'][0].update(initial_location='QA1',accepted=True),
  'intermediate_quality_reset':lambda x:x['recipes']['housing'].insert(1,dict(process='QA',base_ticks=1)),
  'unbounded_wear_probability':lambda x:x['quality'].update(wear_risk_coefficient=2),
  'negative_mode_wear':lambda x:x['modes']['T']['eco'].update(wear=-2),
 }
 guards=[]
 for name,mutation in mutations.items():
  altered=deepcopy(instance);mutation(altered)
  try:result=certificate(altered)
  except (ValueError,AssertionError)as error:guards.append(dict(case=name,rejected=True,error=str(error)))
  else:guards.append(dict(case=name,rejected=False,emitted_missing_lower_bound=result['unfulfilled_lower_bound']))
 # Independently exhaust all subsets of60 small random resource instances.
 rng=random.Random(137);knapsack_cases=0
 for case in range(60):
  needs={f'O{j}':(None if rng.random()<.12 else tuple(rng.randrange(1,4)for _ in range(3)))for j in range(rng.randrange(1,10))}
  capacity=tuple(rng.randrange(1,12)for _ in range(3));best=0
  for size in range(len(needs)+1):
   for subset in combinations(needs,size):
    if any(needs[o]is None for o in subset):continue
    if all(sum(needs[o][r]for o in subset)<=capacity[r]for r in range(3)):best=max(best,size)
  result=material_relaxation(needs,dict(zip(('housing','rotor','flange'),capacity)))
  assert result['maximum_shipped_upper_bound']==best,(case,needs,capacity)
  knapsack_cases+=1
 after=digest(source);assert before==after,'Audit source changed during execution'
 report=dict(schema='stage2-independent-quality-material-audit.v1',audited_source_sha256=before,
  frozen_spec_sha256=digest(spec_source),instance_sha256=full['instance_sha256'],seed=6,orders=len(order_ids),
  horizon_ticks=14400,realized_leaf=leaf,available_housing_blanks=stock,
  unavoidable_scrap=dict(unit_id='P05/housing/1',first_draw_fraction=[first.numerator,first.denominator],
    repair_draw_fraction=[repair.numerator,repair.denominator],first_draw=float(first),repair_draw=float(repair),
    mandatory_heat_minimum_risk=float(min(risks))),
  necessary_housing_blanks_for_all_orders=len(order_ids)+1,unfulfilled_lower_bound=1,
  conclusion='Arithmetic bound independently confirmed on frozen flagship instance; no witness or secondary optimum inferred',
  adversarial_guard_checks=guards,all_adversarial_assumption_changes_rejected=all(row['rejected']for row in guards),
  independent_knapsack_exhaustive_subset_cases=knapsack_cases)
 path=Path(__file__).with_name('report.json');path.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))

if __name__=='__main__':main()
