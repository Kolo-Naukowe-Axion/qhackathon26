"""Offline necessary-quality/material relaxation; never a controller feature.

A component whose two inspection uniforms lie below policy-independent risk
floors must be replaced. Successful orders therefore consume at least their
nominal blanks plus any unavoidable first-version scrap. A finite knapsack
relaxation bounds shipments without assuming that its subset is schedulable.
"""
from fractions import Fraction
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RECIPES=('housing','rotor','flange')
AUDITED_ENGINE_SHA256='ec97bf3c1e57110cc0ddef02e54fafc2626b3aab079718a8ab0f04a5ba26244f'


def keyed_uniform(seed,key):
    # Independent literal reconstruction of the documented hash tape.
    return Fraction(int.from_bytes(hashlib.sha256(f'{seed}:{key}'.encode()).digest()[:8],'big'),2**64)


def risk_floors(instance):
    quality=instance['quality']
    if quality.get('risk_model')!='manufacturing_mode_history':raise ValueError('Manufacturing-history quality model required')
    wear=Fraction(str(quality.get('wear_risk_coefficient',-1)))
    if wear<0 or instance['maintenance']['wear_limit']<=0:raise ValueError('Nonnegative wear risk and bounded wear required')
    if any(Fraction(str(mode.get('wear',1)))<0 for modes in instance['modes'].values() for mode in modes.values()):
        raise ValueError('Nonnegative legal mode wear required')
    result={};margin=Fraction(1,10**10)
    for recipe,steps in instance['recipes'].items():
        if not 1<=len(steps)<=16 or steps[-1]['process']!='QA' or sum(s['process']=='QA' for s in steps)!=1:
            raise ValueError('Short required route with exactly one terminal QA required')
        lower=[]
        for step in steps:
            process=step['process']
            if process=='QA':continue
            probabilities=quality['manufacturing_defect_probabilities'][process]
            legal=instance['modes'][process]
            values=[Fraction(str(probabilities[mode])) for mode in legal]
            if not values or min(values)<0 or max(values)+wear>=1:raise ValueError('Bounded nonnegative legal mode risks including wear required')
            lower.append(min(values))
        # Compounded risk is at least each required individual step risk.
        # A conservative rounding margin dominates IEEE errors on these short
        # bounded routes; do not use a near-threshold equality as a certificate.
        result[recipe]=max(Fraction(0),max(lower,default=Fraction(0))-margin)
    repair=Fraction(str(quality['repair_residual_probability']))-margin
    if not 0<=repair<1:raise ValueError('Positive bounded fixed repair risk required')
    return result,repair


def realized_orders_and_stock(instance):
    orders={o['id'] for o in instance['orders']};horizon=instance['horizon_ticks']
    # Match the audited engine's float accumulation exactly at exogenous
    # thresholds. Fraction arithmetic below is reserved for conservative QA
    # floor comparisons; a near-threshold branch must not change the tape.
    selected=[]
    for index,stage in enumerate(instance['uncertainty_stages']):
        draw=float(keyed_uniform(instance['seed'],f'stage:{index}'));cumulative=0.
        for outcome in stage['outcomes']:
            a,b=outcome['probability'];cumulative+=a/b
            if draw<cumulative:selected.append(outcome['id']);break
        else:raise ValueError('Invalid exogenous outcome distribution')
    arrival=instance['delivery']['normal_tick']
    for stage,outcome_id in zip(instance['uncertainty_stages'],selected):
        if stage['reveal_tick']>horizon:continue
        outcome=next(o for o in stage['outcomes'] if o['id']==outcome_id)
        for event in outcome['events']:
            if event['type']=='urgent_orders':
                orders.update(f'U{j+1:02d}' for j in range(event['count']))
            elif event['type']=='delivery_delay':arrival=event['new_tick']
    stock=dict(instance['raw_stock_units'])
    if arrival<=horizon:
        for recipe,count in instance['delivery']['contents'].items():stock[recipe]+=count
    return sorted(orders),stock,selected


def material_relaxation(demands,stock,max_states=250000):
    """Exact unit-profit multi-resource knapsack; no factory-feasibility claim."""
    capacity=tuple(stock[r] for r in RECIPES)
    if any(type(c) is not int or c<0 for c in capacity):raise ValueError('Integer nonnegative blank budgets required')
    states={(0,0,0):()}
    for order,need in demands.items():
        if need is None:continue
        if len(need)!=3 or any(type(x) is not int or x<1 for x in need):raise ValueError('Three positive integer blank demands required')
        additions={}
        for used,chosen in states.items():
            new=tuple(a+b for a,b in zip(used,need))
            if any(a>b for a,b in zip(new,capacity)):continue
            candidate=chosen+(order,)
            if len(candidate)>len(states.get(new,())) and len(candidate)>len(additions.get(new,())):additions[new]=candidate
        states.update(additions)
        if len(states)>max_states:raise ValueError('Exact relaxation state budget exceeded; no bound emitted')
    used,chosen=max(states.items(),key=lambda item:len(item[1]))
    return dict(maximum_shipped_upper_bound=len(chosen),unfulfilled_lower_bound=len(demands)-len(chosen),
        relaxed_selected_orders=list(chosen),relaxed_blank_use=dict(zip(RECIPES,used)),states=len(states),
        scope='Necessary material/quality constraints only; selected subset is not a physical schedule')


def certificate(instance):
    if hashlib.sha256((ROOT/'stage2/engine.py').read_bytes()).hexdigest()!=AUDITED_ENGINE_SHA256:
        raise ValueError('Engine contract changed; independently reaudit the proof')
    if set(instance['raw_stock_units'])!=set(RECIPES):raise ValueError('The audited three-blank BOM is required')
    if instance['quality'].get('max_replacements_per_original_component')!=1 or instance['quality'].get('max_repairs_per_component_attempt')!=1:
        raise ValueError('Exactly one permitted repair and one component replacement required')
    if set(instance['recipes'])!=set((*RECIPES,'pump')) or [s['process'] for s in instance['recipes']['pump']]!=['ASSEMBLY','QA']:
        raise ValueError('The audited matched three-component and assembly/QA recipe structure is required')
    order_ids=[o['id'] for o in instance['orders']]
    if len(set(order_ids))!=len(order_ids) or any(not oid.startswith('P') for oid in order_ids):raise ValueError('Unique original order lineages required')
    expected={(f'{oid}/{recipe}/1',oid,recipe) for oid in order_ids for recipe in RECIPES}
    actual={(u['id'],u['order_id'],u['recipe']) for u in instance['units']}
    if actual!=expected or len(instance['units'])!=len(expected) or any(u['initial_location']!='RAW_A' or u.get('accepted') or u.get('replacement',0) for u in instance['units']):
        raise ValueError('Complete original RAW units only; accepted WIP or extra replacement births require a new proof')
    for container in (instance['raw_stock_units'],instance['delivery']['contents']):
        if set(container)!=set(RECIPES) or any(type(v) is not int or v<0 for v in container.values()):raise ValueError('Nonnegative three-material supply tables required')
    floors,repair=risk_floors(instance);orders,stock,leaf=realized_orders_and_stock(instance)
    demands={};evidence=[]
    for order in orders:
        need=[];impossible=False
        for recipe in (*RECIPES,'pump'):
            uid=f'{order}/{recipe}/1'
            def forced_scrap(unit):
                a=keyed_uniform(instance['seed'],f'quality:{unit}:0');b=keyed_uniform(instance['seed'],f'quality:{unit}:1')
                result=a<floors[recipe] and b<repair
                if result:evidence.append(dict(order_id=order,recipe=recipe,unit_id=unit,
                    first_draw=float(a),repair_draw=float(b),first_risk_floor=float(floors[recipe]),
                    repair_risk_floor=float(repair),necessary_scrap=True))
                return result
            first=forced_scrap(uid)
            if recipe=='pump':impossible|=first
            else:
                need.append(1+int(first))
                if first:impossible|=forced_scrap(uid+'~r1')
        demands[order]=None if impossible else tuple(need)
    relaxation=material_relaxation(demands,stock)
    names=('stage2/engine.py','stage2/spec.py','stage2/check.py','stage2/quality_material_bound.py','instances/stage2/metaltech_pressure.json')
    return dict(schema='stage2-quality-material-necessary-bound.v1',seed=instance['seed'],
        instance_sha256=hashlib.sha256(json.dumps(instance,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
        source_hashes={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names},
        horizon_ticks=instance['horizon_ticks'],observed_realized_orders=len(orders),realized_exogenous_leaf=list(leaf),
        available_raw_blanks=stock,necessary_blank_demands=demands,unavoidable_quality_evidence=evidence,
        risk_floor_method='Maximum necessary single-step minimum legal-mode risk, less1e-10 conservative rounding margin; nonnegative wear and compounded history cannot lower it',
        assumptions=['Audited engine action domain and fixed unit-lineage keys, including order/pump/1; no policy-selected UID redraws',
            'Original three matched component recipes per pump; no substitutions',
            'One repair attempt; fixed residual risk; at most one component replacement; no final pump replacement',
            'No additional raw procurement or material creation; only declared initial stock and delivery',
            'Source-bound offline proof: keyed future draws are not inputs to a deployed policy'],
        **relaxation,secondary_optimality_gap=None)
