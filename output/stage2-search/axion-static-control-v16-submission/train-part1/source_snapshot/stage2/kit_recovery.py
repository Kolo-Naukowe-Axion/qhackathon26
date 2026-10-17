"""Bounded physical repacking of accepted components; disabled by default.

Search rearranges positions, not physics. Every executed leg uses Factory.move,
and parent consumption uses the original assembly process. No storage is added.
"""
from __future__ import annotations

from collections import defaultdict,deque
from copy import deepcopy
import math
import time

from .admission import AdmissionMixin
from .kitting import KitToolingSpecialistFactory

RECIPES={'housing','rotor','flange'}


def repack_search(parts,capacities,fixed_occupancy,goals,*,max_states=5000,max_depth=6):
    """BFS over idle accepted component positions and assembly-only destinations.

    A goal packs all *currently* accepted target components and leaves enough
    real space for its three-component kit. With only two accepted components,
    the third is explicitly awaited rather than forecast to pass inspection.
    """
    if not 1<=max_states<=5000 or not 0<=max_depth<=6:raise ValueError('Search bounds: 1..5000 states, depth0..6')
    if not capacities or any(type(v) is not int or v<0 for v in capacities.values()):raise ValueError('Explicit nonnegative integer assembly capacities required')
    if set(fixed_occupancy)!=set(capacities) or any(type(v) is not int or v<0 for v in fixed_occupancy.values()):raise ValueError('Complete fixed occupancy required')
    if len({p['id'] for p in parts})!=len(parts):raise ValueError('Unique accepted component identities required')
    if any(p['recipe'] not in RECIPES or not p.get('accepted',False) or p.get('busy') or p.get('moving') or p.get('status')!='waiting' for p in parts):
        raise ValueError('Only accepted idle waiting components can enter the search')
    ids=[p['id'] for p in parts];initial=tuple(p['location'] for p in parts);destinations=sorted(capacities)
    indices={uid:i for i,uid in enumerate(ids)}
    for goal in goals:
        if goal['station'] not in capacities or not goal['unit_ids'] or not set(goal['unit_ids'])<=set(ids):raise ValueError('Goal must reference current components and assembly station')
        units=[parts[indices[uid]] for uid in goal['unit_ids']]
        if len({p['recipe'] for p in units})!=len(units) or len(units)>3 or any(p['order_id']!=goal['order_id'] for p in units):raise ValueError('One component of each BOM recipe per target order')
    def occupancy(state):
        return {mid:fixed_occupancy[mid]+sum(loc==mid for loc in state) for mid in destinations}
    if any(occupancy(initial)[mid]>capacities[mid] for mid in destinations):raise ValueError('Initial physical input occupancy exceeds capacity')
    queue=deque([(initial,0)]);previous={initial:None};expanded=0
    while queue:
        state,depth=queue.popleft();occupied=occupancy(state)
        for goal in goals:
            target=goal['station'];members=[indices[uid] for uid in goal['unit_ids']]
            if all(state[i]==target for i in members) and occupied[target]-len(members)+3<=capacities[target]:
                moves=[];current=state
                while previous[current] is not None:
                    old,move=previous[current];moves.append(move);current=old
                return dict(status='planned',moves=list(reversed(moves)),goal=deepcopy(goal),depth=depth,
                    states_seen=len(previous),expanded=expanded,awaits_unaccepted_components=3-len(members))
        if depth>=max_depth or len(previous)>=max_states:continue
        expanded+=1
        for index,uid in enumerate(ids):
            for target in destinations:
                if state[index]==target or occupied[target]>=capacities[target]:continue
                new=list(state);new[index]=target;new=tuple(new)
                if new in previous:continue
                previous[new]=(state,dict(unit_id=uid,source=state[index],destination=target))
                queue.append((new,depth+1))
                if len(previous)>=max_states:break
            if len(previous)>=max_states:break
    return dict(status='no_plan_within_bounds',states_seen=len(previous),expanded=expanded,max_depth=max_depth,moves=[])


class RecoveryMixin:
    def __init__(self,*args,recovery_policy=None,**kwargs):
        super().__init__(*args,**kwargs)
        self.recovery_policy=dict(enabled=False,quiet_minutes=120,cooldown_minutes=120,max_lock_minutes=720,max_states=5000,max_depth=6)
        if recovery_policy:
            if set(recovery_policy)-set(self.recovery_policy):raise ValueError('Unknown kit recovery option')
            self.recovery_policy.update(deepcopy(recovery_policy))
        p=self.recovery_policy
        if type(p['enabled']) is not bool or any(p[k]<0 for k in ('quiet_minutes','cooldown_minutes')) or p['max_lock_minutes']<=0:
            raise ValueError('Explicit recovery flag and bounded positive lock duration required')
        if type(p['max_states']) is not int or not 1<=p['max_states']<=5000 or type(p['max_depth']) is not int or not 0<=p['max_depth']<=6:
            raise ValueError('Recovery search limited to5000 states/depth6')
        self.recovery_active=None;self.recovery_history=[];self.recovery_searches=[]
        self.recovery_last_attempt=-10**12
        self.trace['provenance']['physical_kit_recovery']=dict(p)

    def _ticks(self,minutes):return math.ceil(minutes/self.i['tick_minutes'])

    def _assembly_stations(self):return {mid:m for mid,m in self.machines.items() if m['process']=='ASSEMBLY'}

    def _as_motion(self):
        stations=self._assembly_stations()
        return any(m.get('entity_type')=='part' and m['start']<=self.t<m['end'] and
            (m['from'] in stations or m['to'] in stations) for m in self.trace['moves'])

    def move(self,unit,dest,entity_type='part'):
        if self.recovery_active is not None and entity_type=='part' and dest in self._assembly_stations():return False
        return super().move(unit,dest,entity_type)

    def process(self,m,parts,*args,**kwargs):
        if self.recovery_active is not None and m['process']=='ASSEMBLY' and parts[0]['order_id']!=self.recovery_active['order_id']:
            return False
        return super().process(m,parts,*args,**kwargs)

    def _observed_components(self):
        stations=self._assembly_stations();result=[]
        for part in self.parts.values():
            if part['recipe'] not in RECIPES or not part['accepted'] or part['status']!='waiting' or part['busy'] or part.get('moving'):continue
            location=part['location'];qa=self.machines.get(location,{}).get('process')=='QA' and part['id'] in self.machines[location]['output']
            if location in stations and part['id'] not in stations[location]['output'] or qa:result.append(part)
        return sorted(result,key=lambda p:p['id'])

    def _plan(self):
        stations=self._assembly_stations()
        if self._as_motion() or any(self.reserved[mid] for mid in stations):return None
        parts=self._observed_components();by_order=defaultdict(list);blocked=set()
        for part in parts:
            by_order[part['order_id']].append(part)
            if self.machines.get(part['location'],{}).get('process')=='QA':blocked.add(part['order_id'])
        orders=[oid for oid in blocked if oid in self.orders and f'{oid}/pump/1' not in self.parts]
        complete=[oid for oid in orders if len({p['recipe'] for p in by_order[oid]})==3]
        if complete:orders=complete
        goals=[dict(order_id=oid,station=mid,unit_ids=[p['id'] for p in by_order[oid]])
            for oid in sorted(orders,key=lambda oid:(self.orders[oid]['due_tick'],oid)) for mid in sorted(stations)]
        if not goals:return None
        fixed={mid:self.input_count(mid)+self.reserved[mid]-sum(p['location']==mid for p in parts) for mid in stations}
        started=time.perf_counter()
        result=repack_search(parts,{mid:m['input_capacity'] for mid,m in stations.items()},fixed,goals,
            max_states=self.recovery_policy['max_states'],max_depth=self.recovery_policy['max_depth'])
        self.recovery_last_attempt=self.t
        self.recovery_searches.append(dict(tick=self.t,wall_seconds=time.perf_counter()-started,
            status=result['status'],states_seen=result['states_seen'],expanded=result['expanded'],
            blocked_orders=sorted(blocked),pool_units=[p['id'] for p in parts],max_depth=self.recovery_policy['max_depth']))
        return result if result['status']=='planned' else None

    def _release(self,status):
        active=self.recovery_active
        if status!='assembled':
            if active['had_original_target']:self.assembly_target[active['order_id']]=active['original_target']
            else:self.assembly_target.pop(active['order_id'],None)
        active.update(status=status,finished_tick=self.t)
        self.recovery_history.append(deepcopy(active));self.recovery_active=None;self.recovery_last_attempt=self.t

    def _activate(self,plan):
        goal=plan['goal'];oid=goal['order_id']
        self.recovery_active=dict(order_id=oid,station=goal['station'],started_tick=self.t,
            had_original_target=oid in self.assembly_target,original_target=self.assembly_target.get(oid),
            plan=plan['moves'],search_states=plan['states_seen'],plan_depth=plan['depth'],
            awaits_unaccepted_components=plan['awaits_unaccepted_components'],plan_index=0,in_flight=None,executed_legs=[])
        self.assembly_target[oid]=goal['station']

    def _retarget_observed_complete_kit(self):
        # Other manufacturing remains live during recovery. If a newly observed
        # accepted QA output completes some other real kit, finishing it now can
        # release space instead of waiting for the original incomplete target.
        ready=self._observed_components();by_order=defaultdict(set);blocked=set()
        for part in ready:
            by_order[part['order_id']].add(part['recipe'])
            if self.machines.get(part['location'],{}).get('process')=='QA':blocked.add(part['order_id'])
        if not any(by_order[oid]==RECIPES and f'{oid}/pump/1' not in self.parts for oid in blocked):return False
        plan=self._plan()
        if plan is None or plan['awaits_unaccepted_components']:return False
        self._release('retargeted_observed_complete_kit');self._activate(plan);return True

    def _physical_leg(self,unit,destination):
        part=self.parts.get(unit)
        if part is None or not part.get('accepted') or part['recipe'] not in RECIPES or part['status']!='waiting':
            self._release('aborted_changed_component');return
        if part.get('moving') or part['busy']:return
        # Bypass only our assembly-traffic lock. All original move semantics,
        # AGV SOC/paths/capacity, reservations and pickup/drop events remain.
        source=part['location']
        if super().move(unit,destination,'part'):
            self.recovery_active['in_flight']=dict(unit_id=unit,source=source,destination=destination,
                dispatched_tick=self.t,move_id=self.trace['moves'][-1]['id'])
            self.recovery_active['executed_legs'].append(deepcopy(self.recovery_active['in_flight']))

    def _advance(self):
        active=self.recovery_active
        if self.t-active['started_tick']>=self._ticks(self.recovery_policy['max_lock_minutes']):self._release('aborted_timeout');return
        flight=active['in_flight']
        if flight:
            part=self.parts[flight['unit_id']]
            if part.get('moving') or part['busy']:return
            if part['location']!=flight['destination']:self._release('aborted_arrival_mismatch');return
            active['in_flight']=None
            if active['plan_index']<len(active['plan']):active['plan_index']+=1
        if active['plan_index']<len(active['plan']):
            step=active['plan'][active['plan_index']];part=self.parts.get(step['unit_id'])
            if part is None or part['location']!=step['source']:self._release('aborted_plan_precondition');return
            self._physical_leg(step['unit_id'],step['destination']);return
        components=[p for p in self.parts.values() if p['order_id']==active['order_id'] and
            p['recipe'] in RECIPES and p['accepted'] and p['status']=='waiting' and not p['busy'] and not p.get('moving')]
        incoming=[p for p in components if p['location']!=active['station']]
        if incoming:self._physical_leg(min(incoming,key=lambda p:p['id'])['id'],active['station']);return
        if len(components)!=3 or {p['recipe'] for p in components}!=RECIPES:
            if self._retarget_observed_complete_kit():self._advance()
            return
        original=self.orders;self.orders={active['order_id']:original[active['order_id']]}
        try:super().assembly()
        finally:self.orders=original
        if f"{active['order_id']}/pump/1" in self.parts and all(self.parts[p['id']]['status']=='consumed' for p in components):
            self._release('assembled')

    def assembly(self):
        if not self.recovery_policy['enabled']:return super().assembly()
        if self.recovery_active is not None:return self._advance()
        super().assembly()
        latest=max((op['start'] for op in self.trace['operations'] if op['kind']=='process'),default=0)
        if self.t-latest<self._ticks(self.recovery_policy['quiet_minutes']) or self.t-self.recovery_last_attempt<self._ticks(self.recovery_policy['cooldown_minutes']):return
        plan=self._plan()
        if plan is None:return
        self._activate(plan)
        self._advance()

    def finish(self):
        super().finish()
        self.trace.setdefault('algorithm_audit',{})['physical_kit_recovery']=dict(policy=deepcopy(self.recovery_policy),
            searches=deepcopy(self.recovery_searches),history=deepcopy(self.recovery_history),active_at_horizon=deepcopy(self.recovery_active),
            scope='Bounded accepted-component repacking; original physical transport and assembly, no added storage or deadlock-free guarantee')


class RecoveryFactory(RecoveryMixin,KitToolingSpecialistFactory):pass
class AdmissionRecoveryFactory(AdmissionMixin,RecoveryFactory):pass


def run(instance,weights=None,controller=None,*,tool_policy=None,kit_reservation=True,admission=False,recovery_policy=None):
    cls=AdmissionRecoveryFactory if admission else RecoveryFactory
    return cls(instance,weights,controller,tool_policy=tool_policy,
        kit_reservation=kit_reservation,recovery_policy=recovery_policy).run()
