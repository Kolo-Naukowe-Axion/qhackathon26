"""Exact material-only envelope of the held factory; no simulated schedules."""
from fractions import Fraction
from itertools import product
import hashlib,json,math
from pathlib import Path
from stage2.spec import build

def report():
    rows=[]
    for initial in range(28,37):
        instance=build(orders=initial,horizon=14400,seed=0,profile='full')
        leaves=[];mean_missing=Fraction(0);possible=Fraction(0)
        for outcomes in product(*(stage['outcomes'] for stage in instance['uncertainty_stages'])):
            probability=math.prod(Fraction(*o['probability']) for o in outcomes)
            demand=initial;arrival=instance['delivery']['normal_tick']
            for stage,outcome in zip(instance['uncertainty_stages'],outcomes):
                if stage['reveal_tick']>instance['horizon_ticks']:continue
                for event in outcome['events']:
                    if event['type']=='urgent_orders':demand+=event['count']
                    if event['type']=='delivery_delay':arrival=event['new_tick']
            stock=dict(instance['raw_stock_units'])
            if arrival<=instance['horizon_ticks']:
                for recipe,count in instance['delivery']['contents'].items():stock[recipe]+=count
            minimum_missing=max(0,demand-min(stock.values()))
            mean_missing+=probability*minimum_missing
            possible+=probability*(minimum_missing==0)
            leaves.append(dict(outcomes=[o['id'] for o in outcomes],probability=[probability.numerator,probability.denominator],demand=demand,total_component_blanks=stock,necessary_missing=minimum_missing))
        rows.append(dict(initial_orders=initial,material_only_expected_missing_lower_bound=float(mean_missing),material_only_all_fulfilled_probability_ceiling=float(possible),leaves=leaves))
    sources=['stage2/spec.py','stage2/engine.py','instances/stage2/metaltech_pressure.json']
    return dict(schema='stage2-structural-stock-envelope.v1',horizon_ticks=14400,rows=rows,factory_simulations=0,
        scope='Conservation bound, no QA independence assumption. Every shipped pump consumes one distinct housing, rotor and flange blank; replacements consume extra stock. Only the held scheduled material delivery can add blanks; paid capacity option adds a calibration tool. Timing, quality and all resource conflicts are optimistically free. A passing necessary condition does not establish a feasible schedule.',
        conclusion='32 initial orders is the largest integer count whose material-only bound permits all orders on every rush/no-rush branch. At33 or34 initial, all-fulfilled probability is at most0.5; at35 ormore it is zero. This does not prove any tested policy attains those ceilings.',
        source_hashes={name:hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in sources},analysis_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())

if __name__=='__main__':
    value=report();p=Path(__file__).with_name('report.json')
    with p.open('x') as f:f.write(json.dumps(value,indent=2)+'\n')
    print(json.dumps([{k:v for k,v in row.items() if k!='leaves'} for row in value['rows']],indent=2))
