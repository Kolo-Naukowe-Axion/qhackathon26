"""Numerical costs of declared variable families, not a complete global QUBO.

Counts are single-trajectory, explicit representation choices. Alternatives and
superset envelopes must not be summed into a total or a lossless reduction ratio.
An optional frozen-trace ablation measures actual local QUBO structure only.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
import gzip
import hashlib
import heapq
import json
from pathlib import Path
import time

from .encoding_audit import audit as nominal_audit
from .qubo import build_qubo, exact_reference
from .spec import build

COMPONENTS = ('housing','rotor','flange')
ROOT = Path(__file__).resolve().parents[1]


def counter_bits(limit):
    """Bits for integers0..limit, before bound/transition constraints."""
    if type(limit) is not int or limit<0:raise ValueError('Counter limit must be a nonnegative integer')
    return limit.bit_length()


def shortest_distances(instance):
    graph = defaultdict(list)
    for edge in instance['graph_edges']:
        if type(edge['ticks']) is not int or edge['ticks']<1:raise ValueError('Positive integer edge ticks required')
        graph[edge['a']].append((edge['b'],edge['ticks']));graph[edge['b']].append((edge['a'],edge['ticks']))
    result = {}
    for source in graph:
        queue=[(0,source)];distance={}
        while queue:
            ticks,node=heapq.heappop(queue)
            if node in distance:continue
            distance[node]=ticks
            for target,length in graph[node]:
                if target not in distance:heapq.heappush(queue,(ticks+length,target))
        if len(distance)!=len(graph):raise ValueError('Connected transport graph required')
        result[source]=distance
    return result


def endpoint_pairs(instance):
    """Nominal loaded-transfer alternatives, preserving leg/recipe identity."""
    distances=shortest_distances(instance)
    stations=defaultdict(list)
    for machine in instance['machines']:stations[machine['process']].append(machine['id'])
    pairs=[];handling=instance['transport']['load_ticks']+instance['transport']['unload_ticks']
    for recipe in (*COMPONENTS,'pump'):
        if recipe=='pump':
            previous=stations['ASSEMBLY'];route=instance['recipes']['pump'][1:]
            destinations=[stations[step['process']] for step in route]+[['SHIP_B']]
        else:
            previous=sorted({unit.get('initial_location','RAW_A') for unit in instance['units'] if unit['recipe']==recipe}) or ['RAW_A']
            destinations=[stations[step['process']] for step in instance['recipes'][recipe]]+[stations['ASSEMBLY']]
        for leg,destination in enumerate(destinations):
            for source in previous:
                for target in destination:
                    if source==target:continue
                    pairs.append(dict(recipe=recipe,leg=leg,source=source,target=target,
                        loaded_ticks=distances[source][target],duration_ticks=distances[source][target]+handling))
            previous=destination
    return pairs


def operation_slots(instance):
    """Potential production route slots per order, before causal birth gates."""
    quality=instance['quality'];repairs=quality['max_repairs_per_component_attempt'];replacements=quality['max_replacements_per_original_component']
    if repairs not in (0,1) or replacements not in (0,1):raise ValueError('Audit scope is the bounded0/1 repair/replacement model')
    slots=[]
    for recipe in (*COMPONENTS,'pump'):
        copies=1 if recipe=='pump' else replacements+1
        for copy in range(copies):
            for index,step in enumerate(instance['recipes'][recipe]):
                slots.append(dict(recipe=recipe,copy=copy,kind='normal',step=index,**step))
            for repair in range(repairs):
                process='ASSEMBLY' if recipe=='pump' else 'T'
                slots.extend([dict(recipe=recipe,copy=copy,kind='repair',step=repair*2,process=process,base_ticks=quality['repair_ticks']),
                    dict(recipe=recipe,copy=copy,kind='repeat_qa',step=repair*2+1,process='QA',base_ticks=instance['recipes']['pump'][-1]['base_ticks'])])
    return slots


def start_choices(instance,slots):
    """Exact count for chosen relaxed release/duration windows; no allocation."""
    horizon=instance['horizon_ticks'];count=0
    for order in instance['orders']:
        for slot in slots:
            process=slot['process'];modes=instance['modes'][process]
            names=instance.get('certification_modes',{}).get('precision',{}).get(process,modes) if order.get('precision_required') else modes
            for machine in instance['machines']:
                if machine['process']!=process:continue
                for name in names:
                    a,b=modes[name]['duration_factor'];c,d=machine['duration_factor']
                    duration=(slot['base_ticks']*a*c+b*d-1)//(b*d)
                    count+=max(0,horizon-duration-order['release_tick']+1)
    return count


def audit(instance):
    horizon=instance['horizon_ticks'];boundaries=horizon+1
    distances=shortest_distances(instance);nodes=len(distances);halls=len({machine['hall'] for machine in instance['machines']})
    workers=len(instance['workers']);machines=len(instance['machines']);agvs=len(instance['agvs']);orders=len(instance['orders'])
    tools={tool['id']:tool for tool in instance['tools']}
    for option in instance.get('lease_options',[]):tools[option['resource']['id']]=option['resource']
    urgent=sum(max((sum(event['count'] for event in outcome['events'] if event['type']=='urgent_orders')
                   for outcome in stage['outcomes']),default=0) for stage in instance.get('uncertainty_stages',[]))
    copies=instance['quality']['max_replacements_per_original_component']+1
    unit_slots=orders*(3*copies+1);maximum_order_slots=orders+urgent
    slots=operation_slots(instance);nominal=nominal_audit(instance);pairs=endpoint_pairs(instance)
    transport=sum(agvs*max(0,horizon-pair['duration_ticks']-order['release_tick']+1) for pair in pairs for order in instance['orders'])
    family_count=len(instance['setup_matrix']);families=[]
    def add(name,bits,formula,scope,**extra):
        families.append(dict(name=name,bits=bits,formula=formula,scope=scope,**extra))
    add('nominal_manufacturing_starts',nominal['naive_known_nominal_start_bits'],
        'sum over known orders,nominal recipe slots,eligible machines,certified legal modes: max(0,H-duration-release+1)',
        'Exact size of this relaxed start-choice family; singleton member representation needs batch linking',alternative_group='production_starts')
    add('bounded_quality_production_start_envelope',start_choices(instance,slots),
        'same start-window sum over all normal/replacement/repair/repeat-QA slots',
        'Includes nominal starts; not an incremental cost. Causal failure/birth gates and earliest replacement lead time omitted',alternative_group='production_starts')
    add('worker_hall_indicators',workers*halls*boundaries,'workers*halls*(H+1)',
        'One-hot physical hall indicators; zero hall flags during a walk; skill/attendance/setup assignment linking still required')
    add('worker_walking_indicators',workers*horizon,'workers*H',
        'Per-tick walking occupation; direction, duration and hall-state transitions not compiled')
    add('tool_node_indicators',len(tools)*nodes*boundaries,'potential_tools*nodes*(H+1)',
        'Physical-node flags for initial and possible leased tools; no node flag when carried or absent')
    add('tool_carrier_or_absence_indicators',len(tools)*(agvs+1)*boundaries,'potential_tools*(AGVs+1)*(H+1)',
        'Companion one-hot carrier/absence states; pre-birth absence fixed by lease gates')
    add('tool_remaining_life_counters',sum(counter_bits(tool['life']) for tool in tools.values())*boundaries,
        '(H+1)*sum_tools ceil(log2(life+1))','Binary counters include invalid top codes; bounds, service/reset and usage linking omitted')
    add('machine_wear_counters',machines*counter_bits(instance['maintenance']['wear_limit'])*boundaries,
        'machines*(H+1)*ceil(log2(wear_limit+1))','Wear bounds, manufacturing increments and maintenance resets require constraints')
    add('machine_family_indicators',machines*(family_count+1)*boundaries,'machines*(families+initial_none)*(H+1)',
        'Family state for setup calculation; setup attendance, duration and transition products uncompiled')
    add('buffer_reserved_or_present_counters',sum(counter_bits(machine['input_capacity']) for machine in instance['machines'])*boundaries,
        '(H+1)*sum_machines ceil(log2(input_capacity+1))','Counts present input plus inbound reservation, excludes output; dispatch/consumption linking omitted')
    add('blocked_output_indicators',machines*boundaries,'machines*(H+1)',
        'Whether any output remains; unit identity/last batch pickup comes from part-state and move linking')
    # These part-state indicators are an alternative to eliminating location
    # states through transport/start variables; they are not an additive minimum.
    add('part_location_status_envelope',unit_slots*(nodes+agvs+4)*boundaries,
        'known_orders*(3*(replacements+1)+1)*(nodes+AGVs+unreleased+consumed+scrapped+shipped)*(H+1)',
        'All component versions and one pump per known order; includes permanently inactive slots; ancestry and legal transitions uncompiled')
    add('part_acceptance_flags',unit_slots*boundaries,'potential_known_unit_slots*(H+1)',
        'Inspection acceptance history; manufactured risk, sampled revelation and QA gating uncompiled')
    add('bom_consumption_event_indicators',unit_slots*horizon,'potential_known_unit_slots*H',
        'Deliberate per-unit consume-event envelope; pump consume choices fixed zero; matched lineage/mass-balance linking omitted')
    stock_limits={recipe:count+instance.get('delivery',{}).get('contents',{}).get(recipe,0) for recipe,count in instance['raw_stock_units'].items()}
    add('raw_stock_counters',sum(counter_bits(limit) for limit in stock_limits.values())*boundaries,
        '(H+1)*sum_recipes ceil(log2(initial_stock+scheduled_delivery+1))',
        'No emergency purchases in current model; realized delivery/release balance and integer bounds still required',counter_limits=stock_limits)
    add('nominal_loaded_pickup_choices',transport,
        'sum_known_orders sum_legal(endpoint,recipe,leg)_pairs AGVs*max(0,H-loaded_path-handling-release+1)',
        'Loading-start choices, not dispatch starts. Empty preposition, reservation start, routes/lanes, vehicle continuity, tool/repair/scrap moves uncounted')
    add('agv_node_indicators',agvs*nodes*boundaries,'AGVs*nodes*(H+1)',
        'Node states have zero flags while traversing; edge/arrival/traction/action linking omitted')
    add('agv_soc_counters',sum(counter_bits(agv['capacity']) for agv in instance['agvs'])*boundaries,
        '(H+1)*sum_AGVs ceil(log2(capacity+1))','Includes traction and charging SOC state; transition and saturation constraints omitted')
    add('agv_charger_occupation',agvs*len(instance['transport']['chargers'])*horizon,'AGVs*chargers*H',
        'Occupation flags, not all variable charge-duration alternatives; charger capacity and travel linking omitted')
    add('stationary_battery_actions',len(instance['energy']['battery_actions'])*horizon,'battery_actions*H',
        'One-hot idle/charge/discharge each tick; grid/solar balance, curtailment and SOC coupling not compiled')
    add('stationary_battery_soc_counters',counter_bits(instance['energy']['stationary_soc_capacity'])*boundaries,
        '(H+1)*ceil(log2(stationary_capacity+1))','Binary SOC state with lossy transitions, bounds and terminal floor requiring constraints')
    heat_starts=sum(max(0,horizon-min((step['base_ticks']*mode['duration_factor'][0]*machine['duration_factor'][0]+
        mode['duration_factor'][1]*machine['duration_factor'][1]-1)//(mode['duration_factor'][1]*machine['duration_factor'][1])
        for recipe in instance['recipes'].values() for step in recipe if step['process']=='HEAT' for mode in instance['modes']['HEAT'].values())+1)
        for machine in instance['machines'] if machine['process']=='HEAT')
    add('heat_batch_family_activations',heat_starts*family_count,
        'families*sum_heat_machines max(0,H-shortest_heat_duration+1)',
        'Shared same-family batch start flags; member starts already overlap manufacturing family; capacity/compatibility/max-duration/setup linking omitted')
    add('machine_maintenance_starts',machines*max(0,horizon-instance['maintenance']['duration']+1),
        'machines*max(0,H-maintenance_duration+1)','Known fixed duration; worker, output blocking, wear reset and power linking omitted')
    add('tool_service_node_starts',nodes*sum(max(0,horizon-tool['service_ticks']+1) for tool in tools.values()),
        'nodes*sum_potential_tools max(0,H-service_duration+1)','Superset of tool-node service choices; location, birth, worker and life reset linking omitted')
    add('rental_request_time_indicators',sum(option['max_count']*horizon for option in instance.get('lease_options',[])),
        'sum_options max_count*H','Optional request slots; late requests arriving after H retained; investment-budget/at-most-count constraints uncompiled')
    add('rental_arrival_indicators_derived',sum(option['max_count']*max(0,horizon-option['lead_ticks']+1) for option in instance.get('lease_options',[])),
        'sum_options max_count*max(0,H-lead+1)','Redundant derived in-horizon delivery states; may eliminate in favor of request variables; never add as mandatory independent decisions')
    return dict(schema='stage2-declared-realism-costs.v1',instance_sha256=hashlib.sha256(json.dumps(instance,sort_keys=True).encode()).hexdigest(),
        horizon_ticks=horizon,tick_minutes=instance['tick_minutes'],known_orders=orders,potential_urgent_orders=urgent,
        dimensions=dict(machines=machines,workers=workers,halls=halls,agvs=agvs,nodes=nodes,potential_tools=len(tools),families=family_count),
        quality_slots=dict(nominal_per_order=sum(len(route) for route in instance['recipes'].values()),
            bounded_per_order=len(slots),bounded_known_total=orders*len(slots),bounded_including_maximum_urgent=maximum_order_slots*len(slots),
            potential_known_unit_slots=unit_slots,scope='Activity-slot envelope, not all slots realizable together; no scenario/history copies'),
        nominal_transport=dict(endpoint_pairs_per_order=len(pairs),pairs_by_recipe=dict(Counter(pair['recipe'] for pair in pairs)),pairs=pairs),
        variable_families=families,complete_global_formulation=False,additive_global_total=None,lossless_reduction_ratio=None,
        global_secondary_optimality_gap=None,
        uncounted=['global linking/reduction auxiliaries and penalty couplers','qualified attendance/setup assignment cross-products',
            'empty AGV dispatch/preposition and reservation-start choices','repair/replacement/tool/scrap transport alternatives',
            'quality-risk arithmetic and branch revelation gates','scenario/history copies and nonanticipativity','global exact power/solar balance encoding'],
        interpretation='Exact arithmetic for stated families, many are alternative representations or relaxed envelopes; do not sum or call a complete global QUBO')


def conflict_families(offers,candidates):
    """Independently classify current dispatch semantics on a frozen pool."""
    if len(offers)!=len(candidates):raise ValueError('Offer/candidate mapping is incomplete')
    result={name:set() for name in ('machine','unit','tool','worker')}
    for i,a in enumerate(offers):
        for j,b in enumerate(offers[:i]):
            pair=tuple(sorted((candidates[j]['id'],candidates[i]['id'])))
            if a['machine_id']==b['machine_id']:result['machine'].add(pair)
            if set(a['unit_ids'])&set(b['unit_ids']):result['unit'].add(pair)
            if set(a['tool_ids'])&set(b['tool_ids']):result['tool'].add(pair)
            shared=bool(set(a['worker_ids'])&set(b['worker_ids']))
            interval_aware=a.get('worker_calendar_aware',False) and b.get('worker_calendar_aware',False)
            overlap=any(x['worker_id']==y['worker_id'] and x['start']<y['end'] and y['start']<x['end']
                        for x in a['worker_intervals'] for y in b['worker_intervals'])
            if (shared and not interval_aware) or overlap:result['worker'].add(pair)
    return result


def local_ablation(trace):
    from .check import check_trace
    checked=check_trace(trace)
    if not checked['valid']:raise ValueError('Frozen local ablation requires a checked physical trace')
    started=time.perf_counter();rows=[]
    for index,decision in enumerate(trace.get('qubo_decisions',[])):
        offers=decision['offered_operations'];candidates=decision['candidates'];caps=decision['capacities']
        families=conflict_families(offers,candidates);all_conflicts=set().union(*families.values())
        recorded={tuple(sorted(pair)) for pair in decision['conflicts']}
        if all_conflicts!=recorded:raise ValueError(f'Independent conflict reconstruction disagrees at decision{index}')
        variants={'reward_only':(set(),False),'power_only':(set(),True),'all_conflicts':(all_conflicts,False),'full':(all_conflicts,True)}
        for name,pairs in families.items():
            variants[name+'_only']=(pairs,False)
            variants['without_'+name]=(set().union(*(v for key,v in families.items() if key!=name)),True)
        variants['without_power']=(all_conflicts,False)
        ablations={}
        for name,(pairs,power) in variants.items():
            active_candidates=deepcopy(candidates)
            if not power:
                for candidate in active_candidates:candidate['resources']={}
            qubo=build_qubo(active_candidates,sorted(pairs),caps if power else {})
            exact_reward=exact_reference(qubo)['reward'] if len(candidates)<=12 else None
            ablations[name]=dict(qubo.summary(),conflict_pairs=len(pairs),exact_pool_reward=exact_reward)
        reference=decision['result']['qubo'];rebuilt=ablations['full']
        for key in ('variables','core_variables','slack_variables','couplers','capacity_encoding','resource_integer_gcd_scales'):
            if rebuilt[key]!=reference[key]:raise ValueError(f'Rebuilt full encoding differs:{key}, decision{index}')
        rows.append(dict(decision=index,tick=decision['tick'],core_candidates=len(candidates),
            original_simulated=bool(decision['result'].get('quantum_algorithm_simulated')),
            original_fallback=bool(decision['result'].get('fallback_reason')),
            overlapping_conflict_families={name:len(pairs) for name,pairs in families.items()},ablations=ablations))
    names=list(rows[0]['ablations']) if rows else []
    summary={name:dict(calls=len(rows),sum_slack=sum(row['ablations'][name]['slack_variables'] for row in rows),
        sum_couplers=sum(row['ablations'][name]['couplers'] for row in rows),
        max_total_bits=max((row['ablations'][name]['variables'] for row in rows),default=0),
        max_slack_bits=max((row['ablations'][name]['slack_variables'] for row in rows),default=0)) for name in names}
    return dict(schema='stage2-frozen-local-realism-ablation.v1',valid=True,checker_provenance=checked['provenance'],
        rows=rows,summary=summary,wall_seconds=time.perf_counter()-started,
        scope='Identical already prefiltered candidate pools; removed constraints are structural diagnostics, never executed factory actions',
        classical_prefiltered=['calendar legality and hall travel','tool life/location/service','buffer/output/transport/BOM readiness','certification and hidden-event guards'],
        caveat='Zero added local bits means classical filtering/fixed boundary, not zero global modeling cost; conflict families overlap and marginal couplers are nonadditive')


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--orders',type=int,nargs='+',default=[8,12,24])
    parser.add_argument('--trace',type=Path);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args(argv)
    if args.output.exists():raise ValueError('Use a new output directory')
    args.output.mkdir(parents=True)
    names=('realism_costs.py','encoding_audit.py','qubo.py','spec.py','engine.py','check.py','dispatch.py')
    before={name:hashlib.sha256((ROOT/'stage2'/name).read_bytes()).hexdigest() for name in names}
    for orders in args.orders:(args.output/f'families-n{orders}.json').write_text(json.dumps(audit(build(orders)),indent=2)+'\n')
    source_trace=None
    if args.trace:
        data=args.trace.read_bytes();plain=gzip.decompress(data) if args.trace.suffix=='.gz' else data
        result=local_ablation(json.loads(plain));source_trace=dict(path=str(args.trace.resolve()),file_sha256=hashlib.sha256(data).hexdigest(),json_sha256=hashlib.sha256(plain).hexdigest())
        result['source_trace']=source_trace;(args.output/'local-ablation.json').write_text(json.dumps(result,indent=2)+'\n')
    after={name:hashlib.sha256((ROOT/'stage2'/name).read_bytes()).hexdigest() for name in names}
    manifest=dict(source_before=before,source_after=after,source_stable=before==after,source_trace=source_trace,
        scope='Read-only arithmetic and frozen local-pool analysis; no global QUBO built, no factory/quantum jobs executed')
    (args.output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(dict(source_stable=manifest['source_stable'],output=str(args.output))))
    return 0 if before==after else 1


if __name__=='__main__':raise SystemExit(main())
