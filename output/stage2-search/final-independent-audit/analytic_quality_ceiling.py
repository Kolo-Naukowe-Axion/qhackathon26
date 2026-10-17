"""Ideal independent-uniform necessary-event ceiling; no factory simulations."""
from fractions import Fraction
from itertools import product
import json
import math
from pathlib import Path

from stage2.final_eval import file_hash
from stage2.quality_material_bound import risk_floors
from stage2.spec import build


def component_bound(demand,stock,q):
    if stock<demand:return Fraction(0)
    return sum((Fraction(math.comb(demand,k))*(q*(1-q))**k*(1-q)**(demand-k)
        for k in range(min(demand,stock-demand)+1)),Fraction(0))


def audit(orders=32,horizon=14400):
    instance=build(orders=orders,horizon=horizon,profile='full',seed=0)
    floors,repair=risk_floors(instance);q={recipe:floor*repair for recipe,floor in floors.items()}
    # Independent limiting-case identities, not comparisons to another runtime solver.
    for demand in(1,2,8):
        assert component_bound(demand,demand-1,Fraction(1,10))==0
        assert component_bound(demand,demand,Fraction(1,10))==Fraction(9,10)**demand
        assert component_bound(demand,2*demand,Fraction(1,10))==Fraction(99,100)**demand
        assert component_bound(demand,demand,Fraction(0))==1
    leaves=[];weighted=Fraction(0);mass=Fraction(0)
    for outcomes in product(*(stage['outcomes']for stage in instance['uncertainty_stages'])):
        probability=math.prod(Fraction(*outcome['probability'])for outcome in outcomes)
        if not probability:continue
        demand=orders;arrival=instance['delivery']['normal_tick']
        for stage,outcome in zip(instance['uncertainty_stages'],outcomes):
            if stage['reveal_tick']>horizon:continue
            for event in outcome['events']:
                if event['type']=='urgent_orders':demand+=event['count']
                if event['type']=='delivery_delay':arrival=event['new_tick']
        stock=dict(instance['raw_stock_units'])
        if arrival<=horizon:
            for recipe,count in instance['delivery']['contents'].items():stock[recipe]+=count
        components={recipe:component_bound(demand,stock[recipe],q[recipe])for recipe in stock}
        pump=(1-q['pump'])**demand
        ceiling=pump*math.prod(components.values())
        weighted+=probability*ceiling;mass+=probability
        leaves.append(dict(outcomes=[outcome['id']for outcome in outcomes],probability=[probability.numerator,probability.denominator],
            demand=demand,raw_stock=stock,pump_necessary_success_probability=float(pump),
            component_necessary_success_probabilities={key:float(value)for key,value in components.items()},
            necessary_event_ceiling=float(ceiling)))
    assert mass==1
    return dict(schema='stage2-ideal-quality-material-probability-ceiling.v1',config=dict(orders=orders,horizon=horizon,profile='full'),
        idealized_all_fulfilled_upper_bound=math.nextafter(float(weighted),math.inf),
        weighted_bound_nearest_float=float(weighted),arithmetic='Exact Fraction polynomial and leaf averaging; displayed ceiling rounded upward by one binary64 ulp',
        forced_scrap_probability_floors={key:float(value)for key,value in q.items()},
        initial_risk_floors={key:float(value)for key,value in floors.items()},repair_risk_floor=float(repair),leaves=leaves,
        formula='Component r: sum k=0..min(D,B_r-D) C(D,k)[q_r(1-q_r)]^k(1-q_r)^(D-k), zero ifB_r<D; multiply independent recipes and(1-q_p)^D, then exogenous probability average',
        assumptions=['Ideal independent Uniform[0,1) potential QA keys for every fixed original/replacement unit and attempt',
            'QA keys conditionally independent of exogenous events; this is a modeling idealization, not a theorem about SHA hashes',
            'Fixed canonical lineages, atmostonecomponent replacement and no finalpump replacement',
            'Conservative policy-independent manufacturing/repair risk floors from audited numerical tables'],
        interpretation='Necessary-event relaxation, not achievable success probability. Ignores timing/resources and additional failures outside the forced-event rectangles. A ceiling above an observed policy does not prove that the difference is achievable or attribute it to scheduling.',
        factory_simulations=0,quality_draws_inspected=0,
        source_hashes={name:file_hash(name)for name in('stage2/spec.py','stage2/engine.py','stage2/quality_material_bound.py','instances/stage2/metaltech_pressure.json')},
        analysis_source_sha256=file_hash(__file__))


if __name__=='__main__':
    result=audit();output=Path(__file__).with_name('ideal-quality-ceiling-report.json')
    with output.open('x')as stream:stream.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps({key:value for key,value in result.items()if key!='leaves'},indent=2))
