"""Exact CP reference for 1–4 deterministic matched-BOM pumps, not the flagship.

All mandatory operations, part moves, machine output holds, reserved inputs,
empty AGV repositioning and worker walks are optimized in the declared domain.
Quality, energy, service, modes and calendars are explicitly nonbinding.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import time

from .reference import make_tiny,shortest_path,validate_scope as validate_single

ROOT=Path(__file__).resolve().parents[1]
RECIPES=('housing','rotor','flange')


def make_multi(pumps=2,processing_scale=15,horizon=None,automatic_attendance=True,
               bridge_ticks=4,input_capacity=1,dispatch_after_ready=False):
    if type(pumps)is not int or not 1<=pumps<=4:raise ValueError('Reference supports 1–4 pumps only')
    if horizon is None:horizon=pumps*(160*processing_scale+200)
    instance=make_tiny(processing_scale,horizon,automatic_attendance,bridge_ticks,input_capacity,dispatch_after_ready)
    template=instance['orders'][0]
    instance['orders']=[dict(template,id=f'P{k+1:02d}')for k in range(pumps)]
    instance['units']=[dict(id=f'{order["id"]}/{recipe}/1',order_id=order['id'],recipe=recipe,
        family='alloy_A',release_tick=0,initial_location='RAW_A')for order in instance['orders']for recipe in RECIPES]
    instance['raw_stock_units']={recipe:pumps for recipe in RECIPES}
    # A continuous worker is part of the declared relaxation. No omitted midnight boundary.
    instance['day_ticks']=horizon+1;instance['workers'][0]['daily_shift']=[0,horizon+1]
    instance['name']=f'Exact deterministic {pumps}-pump matched-BOM reference'
    instance['profile']='tiny-multi-reference'
    instance['reference_scope'].update(pumps=pumps,matched_order_bom=True,
        continuous_worker_calendar=True,standalone_empty_agv_actions=False,
        empty_repositioning='Shortest tree path inside each mandatory part-transfer dispatch; early preposition may wait for source completion',
        objective='All orders fulfilled, constant minimum energy cost, then last physical shipment',
        label_symmetry='Identical orders may be relabeled; first housing starts ordered without loss',
        flagship_global_gap=None)
    return instance


def activities(instance):
    stations={machine['process']:machine for machine in instance['machines']}
    if len(stations)!=len(instance['machines']):raise ValueError('One fixed station per process required')
    operations=[];moves=[]
    for order in instance['orders']:
        oid=order['id'];assembly_id=f'{oid}/pump/1/op0'
        for recipe in (*RECIPES,'pump'):
            uid=f'{oid}/{recipe}/1';previous_op=None;location='RAW_A'
            for step_index,step in enumerate(instance['recipes'][recipe]):
                machine=stations[step['process']];op_id=f'{uid}/op{step_index}'
                operations.append(dict(id=op_id,unit_id=uid,order_id=oid,recipe=recipe,recipe_step=step_index,
                    machine_id=machine['id'],process=step['process'],duration=step['base_ticks'],hall=machine['hall']))
                if recipe!='pump'or step_index:
                    moves.append(dict(id=f'move{len(moves)}',unit_id=uid,order_id=oid,source_op=previous_op,target_op=op_id,
                        **{'from':location,'to':machine['id']}))
                previous_op,location=op_id,machine['id']
            moves.append(dict(id=f'move{len(moves)}',unit_id=uid,order_id=oid,source_op=previous_op,
                target_op=None if recipe=='pump'else assembly_id,
                **{'from':location,'to':'SHIP_B'if recipe=='pump'else stations['ASSEMBLY']['id']}))
    return operations,moves


def validate_scope(instance):
    def require(condition,message):
        if not condition:raise ValueError('Outside exact multi-pump scope: '+message)
    orders=instance['orders'];n=len(orders);h=instance['horizon_ticks']
    require(1<=n<=4 and len(instance['workers'])==len(instance['agvs'])==1,'1–4 orders, one worker, one AGV')
    require(len({order['id']for order in orders})==n,'duplicate order IDs')
    require(instance['reference_scope'].get('matched_order_bom')is True,'unmatched or undeclared BOM')
    require(instance['reference_scope'].get('continuous_worker_calendar')is True,'continuous calendar not declared')
    require(instance['reference_scope'].get('standalone_empty_agv_actions')is False,'standalone empty preposition actions not modeled')
    require(instance['day_ticks']>h,'periodic calendar boundary would bind inside horizon')
    expected={(order['id'],recipe):f'{order["id"]}/{recipe}/1'for order in orders for recipe in RECIPES}
    require(len(instance['units'])==3*n,'wrong component count')
    require({(u['order_id'],u['recipe']):u['id']for u in instance['units']}==expected,'component IDs/order lineage do not match BOM')
    require(len({u['id']for u in instance['units']})==3*n,'duplicate unit IDs')
    require(all(order['family']=='alloy_A'and order['release_tick']==0 and order['due_tick']==h and not order.get('urgent')for order in orders),
        'label symmetry needs identical family/release/deadline orders')
    # Reuse every original feature guard per order, then strengthen shared totals.
    for order in orders:
        single=deepcopy(instance);single['orders']=[deepcopy(order)]
        single['units']=[deepcopy(u)for u in instance['units']if u['order_id']==order['id']]
        validate_single(single)
    operations,moves=activities(instance)
    require(instance['maintenance']['wear_limit']>=sum(op['duration']for op in operations),'aggregate wear may require maintenance')
    for tool in instance['tools']:
        workload=sum(op['duration']for op in operations if instance['process_tools'].get(op['process'])==tool['kind'])
        require(tool['life']>=workload,'aggregate tool life may require service')
    require(all(instance['raw_stock_units'].get(recipe,0)>=n for recipe in RECIPES),'insufficient aggregate stock')
    require(instance['transport']['load_ticks']==instance['transport']['unload_ticks']==1,'handling differs from the engine fixture')
    require(type(instance['worker_travel_ticks'])is int and instance['worker_travel_ticks']>=0,'noninteger worker travel')
    require(all(rule['kind']in ('start','full')and(rule['kind']=='full'or type(rule['ticks'])is int and rule['ticks']>=1)
        for rule in instance['attendance'].values()),'invalid worker attendance rule')
    nodes={edge[key]for edge in instance['graph_edges']for key in ('a','b')}
    distance=lambda a,b:sum(d for _,_,d in shortest_path(instance,a,b))
    max_empty=max(distance(a,b)for a in nodes for b in nodes)
    loaded=sum(distance(move['from'],move['to'])for move in moves)
    require(instance['agvs'][0]['initial_soc']>=2*loaded+len(moves)*max_empty,'aggregate AGV traction may require charging')


def resource_bounds(instance):
    operations,moves=activities(instance);work=0;machine=defaultdict(int)
    for op in operations:
        rule=instance['attendance'][op['process']]
        work+=op['duration']if rule['kind']=='full'else min(op['duration'],rule['ticks'])
        machine[op['machine_id']]+=op['duration']
    loaded=sum(sum(ticks for _,_,ticks in shortest_path(instance,m['from'],m['to']))+2 for m in moves)
    return dict(worker_attendance_ticks=work,machine_processing_ticks=dict(machine),
        loaded_transport_and_handling_ticks=loaded,
        makespan_lower_bound_ticks=max(work,loaded,*machine.values()),
        scope='Necessary reusable-resource work bounds only; no added empty travel, worker walks, blocking or initial/join gaps')


def schedule_from_trace(instance,operations,movements,trace):
    """Match a checked physical witness to semantic activities, never by job index."""
    from .check import check_trace
    verified=check_trace(trace)
    if trace['instance']!=instance or not(verified['valid']and verified['all_orders_fulfilled']and verified['terminal_requirements_met']):
        raise ValueError('Witness must be complete and valid on the identical numerical instance')
    op_lookup={(row['unit_id'],row['recipe_step']):row for row in trace['operations']if row.get('kind')=='process'}
    move_lookup={(row['unit_id'],row['from'],row['to']):row for row in trace['moves']if row['kind']=='transport'and row['entity_type']=='part'}
    op_keys={(op['unit_id'],op['recipe_step']):index+1 for index,op in enumerate(operations)}
    move_keys={(move['unit_id'],move['from'],move['to']):index+1 for index,move in enumerate(movements)}
    if set(op_lookup)!=set(op_keys)or set(move_lookup)!=set(move_keys):raise ValueError('Witness activities differ from exact matched-BOM domain')
    worker_path=[0]+[op_keys[key]for key in sorted(op_keys,key=lambda key:op_lookup[key]['start'])]+[0]
    agv_path=[0]+[move_keys[key]for key in sorted(move_keys,key=lambda key:move_lookup[key]['start'])]+[0]
    return dict(operations={op['id']:op_lookup[op['unit_id'],op['recipe_step']]['start']for op in operations},
        moves={move['id']:dict(start=move_lookup[move['unit_id'],move['from'],move['to']]['start'],
            pickup=move_lookup[move['unit_id'],move['from'],move['to']]['pickup_tick'],drop=move_lookup[move['unit_id'],move['from'],move['to']]['drop_tick'])for move in movements},
        worker_successors=dict(zip(worker_path,worker_path[1:])),agv_successors=dict(zip(agv_path,agv_path[1:])))


def to_trace(instance,operations,movements,schedule):
    trace=dict(schema='metaltech-stage2-trace.v1',run_id='tiny-multi-cp-reference',tick_minutes=instance['tick_minutes'],
        horizon_ticks=instance['horizon_ticks'],instance=deepcopy(instance),
        resources={key:deepcopy(instance[key])for key in ('machines','workers','tools','agvs')},
        provenance=dict(kind='measured',solver='OR-Tools CP-SAT exact matched-BOM multi-pump reference'),
        operations=[],moves=[],worker_moves=[],events=[],energy=[],metrics={})
    wid=instance['workers'][0]['id'];wear=defaultdict(float)
    for unit in instance['units']:
        trace['events'].append(dict(tick=0,type='release',unit_id=unit['id'],recipe=unit['recipe']))
    for op in sorted(operations,key=lambda row:(schedule['operations'][row['id']],row['id'])):
        start=schedule['operations'][op['id']];end=start+op['duration'];oid=op['order_id']
        rule=instance['attendance'][op['process']];attend=op['duration']if rule['kind']=='full'else min(op['duration'],rule['ticks'])
        tools=[tool['id']for tool in instance['tools']if tool['kind']==instance['process_tools'].get(op['process'])]
        parents=[u['id']for u in instance['units']if u['order_id']==oid]if op['process']=='ASSEMBLY'else []
        trace['operations'].append(dict(id=op['id'],unit_ids=[op['unit_id']],unit_id=op['unit_id'],order_id=oid,
            process=op['process'],machine_id=op['machine_id'],start=start,end=end,mode='standard',worker_ids=[wid],tool_ids=tools,
            worker_intervals=[dict(worker_id=wid,start=start,end=start+attend,role='process',skills=[instance['process_skills'][op['process']]])],
            worker_roles={wid:[instance['process_skills'][op['process']]]},parent_unit_ids=parents,setup_ticks=0,
            processing_ticks=op['duration'],power_kw=instance['modes'][op['process']]['standard']['power_kw'],
            family='alloy_A',kind='process',recipe_step=op['recipe_step'],recipe_steps={op['unit_id']:op['recipe_step']},
            attempt=0,is_rework=False,repair_step=None,wear_before=wear[op['machine_id']]))
        wear[op['machine_id']]+=op['duration']
        trace['events'].append(dict(tick=end,type='process_complete',unit_id=op['unit_id'],operation_id=op['id']))
        trace['events'] += [dict(tick=start,type='consume',unit_id=uid,parent_operation=op['id'],order_id=oid)for uid in parents]
        if op['process']=='QA':
            raw=hashlib.sha256(f'{instance["seed"]}:quality:{op["unit_id"]}:0'.encode()).digest()
            trace['events'].append(dict(tick=end,type='qa_result',unit_id=op['unit_id'],operation_id=op['id'],
                passed=True,keyed_uniform=int.from_bytes(raw[:8],'big')/2**64,defect_probability=0))
    agv=instance['agvs'][0];location=agv['initial_location'];soc=agv['initial_soc']
    index=schedule['agv_successors'][0];seen=set()
    while index:
        if index in seen:raise ValueError('AGV successor cycle omitted dummy terminal')
        seen.add(index);move=movements[index-1];times=schedule['moves'][move['id']];legs=[];tick=times['start']
        for origin,dest,duration in shortest_path(instance,location,move['from']):
            legs.append(dict(**{'from':origin,'to':dest},start=tick,end=tick+duration,loaded=False));tick+=duration
        assert tick<=times['pickup']
        tick=times['pickup']+1
        for origin,dest,duration in shortest_path(instance,move['from'],move['to']):
            legs.append(dict(**{'from':origin,'to':dest},start=tick,end=tick+duration,loaded=True));tick+=duration
        assert tick+1==times['drop']
        cost=sum((leg['end']-leg['start'])*(2 if leg['loaded']else 1)for leg in legs)
        trace['moves'].append(dict(id=move['id'],unit_id=move['unit_id'],entity_type='part',agv_id=agv['id'],
            start=times['start'],pickup_tick=times['pickup'],drop_tick=times['drop'],end=times['drop'],
            **{'from':move['from'],'to':move['to']},legs=legs,soc_before=soc,soc_after=soc-cost,kind='transport'))
        soc-=cost;location=move['to']
        if location=='SHIP_B':trace['events'].append(dict(tick=times['drop'],type='ship',unit_id=move['unit_id'],order_id=move['order_id']))
        index=schedule['agv_successors'][index]
    assert len(seen)==len(movements)
    hall=instance['workers'][0]['initial_hall'];index=schedule['worker_successors'][0];seen=set()
    while index:
        if index in seen:raise ValueError('Worker successor cycle omitted dummy terminal')
        seen.add(index);op=operations[index-1]
        if hall!=op['hall']:
            end=schedule['operations'][op['id']]
            trace['worker_moves'].append(dict(worker_id=wid,start=end-instance['worker_travel_ticks'],end=end,from_hall=hall,to_hall=op['hall']))
        hall=op['hall'];index=schedule['worker_successors'][index]
    assert len(seen)==len(operations)
    energy=instance['energy']
    for tick in range(instance['horizon_ticks']):
        load=energy['base_load_kw']+sum(op['power_kw']for op in trace['operations']if op['start']<=tick<op['end'])
        trace['energy'].append(dict(tick=tick,load_kw=load,grid_kw=load,cap_kw=energy['normal_grid_cap_kw'],solar_kw=0,curtailed_kw=0,
            soc_before=energy['stationary_soc_initial'],soc=energy['stationary_soc_initial'],battery_action='idle',tariff=energy['tariff_low'],carbon_intensity=energy['carbon_low']))
    trace['events'].sort(key=lambda row:row['tick']);return trace


def solve(instance,deterministic_limit=10,wall_limit=15,seed=0,workers=1,incumbent=None):
    import ortools
    from ortools.sat.python import cp_model
    from .check import check_trace
    if deterministic_limit<=0 or wall_limit<=0 or type(workers)is not int or workers<1:raise ValueError('Positive solve budgets/workers required')
    began=time.perf_counter();validate_scope(instance)
    operations,movements=activities(instance);horizon=instance['horizon_ticks'];model=cp_model.CpModel()
    op_start={};op_end={};attended_end={}
    for op in operations:
        name=op['id'];duration=op['duration']
        op_start[name]=model.new_int_var(0,max(0,horizon-duration),'start:'+name)
        op_end[name]=model.new_int_var(duration,max(duration,horizon),'end:'+name)
        model.add(op_end[name]==op_start[name]+duration);model.add(op_end[name]<=horizon)
        rule=instance['attendance'][op['process']]
        attended_end[name]=op_start[name]+(duration if rule['kind']=='full'else min(duration,rule['ticks']))
    dispatch={};pickup={};drop={};incoming=defaultdict(list);outgoing={}
    distance=lambda a,b:sum(d for _,_,d in shortest_path(instance,a,b))
    for move in movements:
        name=move['id']
        dispatch[name]=model.new_int_var(0,horizon,'dispatch:'+name)
        pickup[name]=model.new_int_var(0,horizon,'pickup:'+name)
        drop[name]=model.new_int_var(0,horizon,'drop:'+name)
        model.add(drop[name]==pickup[name]+2+distance(move['from'],move['to']))
        if move['source_op']:
            if instance['reference_scope']['dispatch_after_source_completion']:model.add(dispatch[name]>=op_end[move['source_op']])
            model.add(pickup[name]>=op_end[move['source_op']]);outgoing[move['source_op']]=name
        if move['target_op']:
            model.add(drop[name]<=op_start[move['target_op']]);incoming[move['target_op']].append(name)
    machines={machine['id']:machine for machine in instance['machines']}
    machine_intervals=defaultdict(list);buffers=defaultdict(list);worker_intervals=[]
    for op in operations:
        name=op['id'];machine=op['machine_id'];release=pickup[outgoing[name]]
        model.add(release>=op_end[name]);span=model.new_int_var(op['duration'],horizon,'occupied:'+name)
        model.add(span==release-op_start[name])
        machine_intervals[machine].append(model.new_interval_var(op_start[name],span,release,'machine:'+name))
        rule=instance['attendance'][op['process']];attend=op['duration']if rule['kind']=='full'else min(op['duration'],rule['ticks'])
        worker_intervals.append(model.new_interval_var(op_start[name],attend,attended_end[name],'worker:'+name))
        for mid in incoming[name]:
            size=model.new_int_var(0,horizon,'buffer_size:'+mid);model.add(size==op_start[name]-dispatch[mid])
            buffers[machine].append(model.new_interval_var(dispatch[mid],size,op_start[name],'buffer:'+mid))
    for intervals in machine_intervals.values():model.add_no_overlap(intervals)
    for machine,intervals in buffers.items():model.add_cumulative(intervals,[1]*len(intervals),machines[machine]['input_capacity'])
    model.add_no_overlap(worker_intervals)
    agv_arcs={};worker_arcs={}
    for a in range(len(movements)+1):
        for b in range(len(movements)+1):
            if a==b:continue
            literal=model.new_bool_var(f'agv_arc:{a}:{b}');agv_arcs[a,b]=literal
            if b:
                move=movements[b-1];mid=move['id'];prior=instance['agvs'][0]['initial_location']if not a else movements[a-1]['to']
                if a:model.add(dispatch[mid]>=drop[movements[a-1]['id']]).only_enforce_if(literal)
                model.add(pickup[mid]>=dispatch[mid]+distance(prior,move['from'])).only_enforce_if(literal)
    model.add_circuit([(a,b,literal)for (a,b),literal in agv_arcs.items()])
    for a in range(len(operations)+1):
        for b in range(len(operations)+1):
            if a==b:continue
            literal=model.new_bool_var(f'worker_arc:{a}:{b}');worker_arcs[a,b]=literal
            if b:
                op=operations[b-1];hall=instance['workers'][0]['initial_hall']if not a else operations[a-1]['hall']
                walk=instance['worker_travel_ticks']if hall!=op['hall']else 0
                model.add(op_start[op['id']] >= (0 if not a else attended_end[operations[a-1]['id']])+walk).only_enforce_if(literal)
    model.add_circuit([(a,b,literal)for (a,b),literal in worker_arcs.items()])
    ids=[order['id']for order in instance['orders']]
    for earlier,later in zip(ids,ids[1:]):model.add(op_start[f'{earlier}/housing/1/op0']<=op_start[f'{later}/housing/1/op0'])
    shipping=[move for move in movements if move['to']=='SHIP_B']
    makespan=model.new_int_var(0,horizon,'last_shipment')
    model.add_max_equality(makespan,[drop[move['id']]for move in shipping])
    bounds=resource_bounds(instance);model.add(makespan>=bounds['makespan_lower_bound_ticks'])
    hint_report={'used':False}
    if incumbent is not None:
        checked=check_trace(incumbent)
        if incumbent['instance']!=instance or not checked['valid']or not checked['all_orders_fulfilled']:raise ValueError('Incumbent must be valid and complete on the identical instance')
        hint_report=dict(used=True,makespan=max(checked['metrics']['delivery_ticks'].values()),scope='Validated upper bound and warm-start hints; no choices fixed')
        model.add(makespan<=hint_report['makespan'])
        op_lookup={(row['unit_id'],row['recipe_step']):row for row in incumbent['operations']if row.get('kind')=='process'}
        move_lookup={(row['unit_id'],row['from'],row['to']):row for row in incumbent['moves']if row['kind']=='transport'and row['entity_type']=='part'}
        op_ids={(op['unit_id'],op['recipe_step']):index+1 for index,op in enumerate(operations)}
        move_ids={(move['unit_id'],move['from'],move['to']):index+1 for index,move in enumerate(movements)}
        if set(op_lookup)!=set(op_ids)or set(move_lookup)!=set(move_ids):raise ValueError('Incumbent activities differ from the declared exact domain')
        for op in operations:
            row=op_lookup[op['unit_id'],op['recipe_step']]
            model.add_hint(op_start[op['id']],row['start']);model.add_hint(op_end[op['id']],row['end'])
        for move in movements:
            row=move_lookup[move['unit_id'],move['from'],move['to']]
            for variables,key in ((dispatch,'start'),(pickup,'pickup_tick'),(drop,'drop_tick')):model.add_hint(variables[move['id']],row[key])
        worker_path=[0]+[op_ids[key]for key in sorted(op_ids,key=lambda key:op_lookup[key]['start'])]+[0]
        agv_path=[0]+[move_ids[key]for key in sorted(move_ids,key=lambda key:move_lookup[key]['start'])]+[0]
        for arcs,path in ((worker_arcs,worker_path),(agv_arcs,agv_path)):
            used=set(zip(path,path[1:]))
            for edge,literal in arcs.items():model.add_hint(literal,int(edge in used))
        model.add_hint(makespan,hint_report['makespan']);hint_report['complete_operation_move_arc_hint']=True
    model.minimize(makespan)
    error=model.validate()
    if error:raise ValueError(error)
    solver=cp_model.CpSolver();solver.parameters.max_deterministic_time=deterministic_limit
    solver.parameters.max_time_in_seconds=wall_limit;solver.parameters.num_search_workers=workers;solver.parameters.random_seed=seed
    status=solver.solve(model)
    report=dict(schema='metaltech-stage2-multi-reference.v1',solver='OR-Tools CP-SAT',solver_version=ortools.__version__,
        status=solver.status_name(status),optimal=status==cp_model.OPTIMAL,objective_ticks=None,best_bound_ticks=solver.best_objective_bound,
        deterministic_limit=deterministic_limit,wall_limit_seconds=wall_limit,search_workers=workers,seed=seed,
        build_and_solve_seconds=time.perf_counter()-began,solver_wall_seconds=solver.wall_time,
        solver_response=solver.response_stats(),model_stats=model.model_stats(),
        counts=dict(pumps=len(ids),operations=len(operations),moves=len(movements),machines=len(machines),agv_arc_bits=len(agv_arcs),worker_arc_bits=len(worker_arcs)),
        scope=deepcopy(instance['reference_scope']),resource_bounds=bounds,incumbent=hint_report,
        model_infeasibility_proven=status==cp_model.INFEASIBLE,global_infeasibility_proven=False,flagship_global_gap=None,
        optimality_scope='Declared matched-BOM deterministic direct-transfer domain; all fulfillment and constant minimum cost precede last-shipment makespan')
    if status not in (cp_model.FEASIBLE,cp_model.OPTIMAL):return report
    schedule=dict(operations={op['id']:solver.value(op_start[op['id']])for op in operations},
        moves={move['id']:dict(start=solver.value(dispatch[move['id']]),pickup=solver.value(pickup[move['id']]),drop=solver.value(drop[move['id']]))for move in movements},
        agv_successors={a:b for (a,b),literal in agv_arcs.items()if solver.value(literal)},
        worker_successors={a:b for (a,b),literal in worker_arcs.items()if solver.value(literal)})
    trace=to_trace(instance,operations,movements,schedule);validation=check_trace(trace)
    report.update(objective_ticks=solver.value(makespan),trace=trace,validation=validation,schedule=schedule)
    if not(validation['valid']and validation['all_orders_fulfilled']and validation['terminal_requirements_met']):
        report.update(status='INVALID_EXPORTED_SOLUTION',optimal=False)
    return report


def compare(instance,**solve_options):
    from .engine import run
    from .check import check_trace
    names=('stage2/reference_multi.py','stage2/reference.py','stage2/check.py','stage2/engine.py')
    hashes=lambda:{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest()for name in names}
    before=hashes();heuristic=run(deepcopy(instance),dict(wip_limit=1,mode='standard'))
    validation=check_trace(heuristic)
    usable=validation['valid']and validation['all_orders_fulfilled']and validation['terminal_requirements_met']
    exact=solve(instance,incumbent=heuristic if usable else None,**solve_options)
    delivered=max(validation['metrics']['delivery_ticks'].values(),default=None)if usable else None
    same_tiers=usable and exact.get('validation',{}).get('valid',False)and abs(validation['metrics']['total_cost']-exact['validation']['metrics']['total_cost'])<1e-5
    gap=(delivered-exact['objective_ticks'])/exact['objective_ticks']if exact['optimal']and same_tiers else None
    return dict(exact=exact,heuristic_trace=heuristic,heuristic_validation=validation,
        comparison=dict(heuristic_policy={'wip_limit':1,'mode':'standard'},heuristic_makespan_ticks=delivered,
            same_earlier_objective_tiers=bool(same_tiers),heuristic_makespan_gap=gap,
            optimum_makespan_ticks=exact['objective_ticks']if exact['optimal']else None,
            proved_lower_bound_ticks=exact['best_bound_ticks'],flagship_global_gap=None),
        provenance=dict(instance_sha256=hashlib.sha256(json.dumps(instance,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
            source_sha256=before,sources_stable_during_run=before==hashes(),final_heldout_tapes_used=0))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pumps',type=int,choices=(1,2,3,4),default=2)
    parser.add_argument('--processing-scale',type=int,default=15);parser.add_argument('--horizon',type=int)
    parser.add_argument('--full-attendance',action='store_true');parser.add_argument('--dispatch-after-ready',action='store_true')
    parser.add_argument('--wall-limit',type=float,default=15);parser.add_argument('--deterministic-limit',type=float,default=10)
    parser.add_argument('--workers',type=int,default=1);parser.add_argument('--seed',type=int,default=0)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    instance=make_multi(args.pumps,args.processing_scale,args.horizon,not args.full_attendance,dispatch_after_ready=args.dispatch_after_ready)
    result=compare(instance,wall_limit=args.wall_limit,deterministic_limit=args.deterministic_limit,workers=args.workers,seed=args.seed)
    artifacts={'instance.json':instance,'heuristic-trace.json':result.pop('heuristic_trace')}
    if 'trace'in result['exact']:artifacts['cp-trace.json']=result['exact'].pop('trace')
    if 'schedule'in result['exact']:artifacts['cp-schedule.json']=result['exact'].pop('schedule')
    for name,data in artifacts.items():(args.output/name).write_text(json.dumps(data,indent=2)+'\n')
    result['artifacts_sha256']={name:hashlib.sha256((args.output/name).read_bytes()).hexdigest()for name in artifacts}
    (args.output/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(status=result['exact']['status'],objective=result['exact']['objective_ticks'],
        bound=result['exact']['best_bound_ticks'],valid=result['exact'].get('validation',{}).get('valid'),
        heuristic=result['comparison']['heuristic_makespan_ticks'],gap=result['comparison']['heuristic_makespan_gap'],
        solve_seconds=result['exact']['solver_wall_seconds']),indent=2))


if __name__=='__main__':main()
