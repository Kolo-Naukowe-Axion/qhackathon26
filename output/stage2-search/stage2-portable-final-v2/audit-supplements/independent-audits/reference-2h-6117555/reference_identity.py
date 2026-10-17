"""Narrow reference identity semantics for future empty-dispatch reservations.

The frozen general identity auditor remains unchanged and its literal result is
retained separately. This independent check encounters cargo at pickup/loaded
legs, never equates an earlier parked-AGV reservation with a born physical part.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path

from stage2.reference_multi import make_multi,activities,validate_scope

ROOT=Path(__file__).resolve().parents[4]
INSTANCE_SHA='3c6bda8bbf315951447394c68053894ff4a756be1c63f826de7c58739b5c3f7e'
SOURCES={'stage2/reference_multi.py':'226dced1939ee824a0e661d4112efc488be4de3286e6280e9da4e58163700efe',
         'stage2/reference.py':'ffd604b8e5da58bd789cdc24cdf7bdc69f18ea984a28b4d843c718326d8c5732',
         'stage2/engine.py':'ec97bf3c1e57110cc0ddef02e54fafc2626b3aab079718a8ab0f04a5ba26244f',
         'stage2/check.py':'40c96bf26f19aa10e33566332d55133f8bd73c32878753668202b4690ce4bf5b',
         'stage2/identity_audit.py':'3faf6ca7e90e8061babef543aeb68e19a292ce8dbcab309d4412f0a258f95c70'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def audit(trace,instance):
    issues=[];planned=[]
    def issue(code,**details):issues.append(dict(code=code,**details))
    if digest(instance)!=INSTANCE_SHA or instance!=make_multi(4) or trace.get('instance')!=instance:
        raise ValueError('Only the identical held four-pump reference is supported')
    for name,expected in SOURCES.items():
        if sha(ROOT/name)!=expected:raise ValueError('Held reference/physical/identity source drift')
    validate_scope(instance)
    if not(instance['reference_scope']['early_empty_preposition'] and not instance['reference_scope']['dispatch_after_source_completion']):raise ValueError('Early preposition reference required')
    expected_ops,expected_moves=activities(instance)
    canonical={f'{o["id"]}/{r}/1' for o in instance['orders'] for r in ('housing','rotor','flange','pump')}
    initial={u['id'] for u in instance['units']};birth={u:0 for u in initial};pumps=Counter();sources={};ops={}
    for op in trace['operations']:
        uid=op.get('unit_id');oid=op.get('order_id')
        if op['id'] in ops:issue('duplicate_operation',operation_id=op['id'])
        ops[op['id']]=op
        if uid not in canonical or op.get('unit_ids')!=[uid]:issue('unknown_or_noncanonical_operation',unit_id=uid)
        if uid and uid.split('/')[0]!=oid:issue('operation_order_identity',unit_id=uid)
        if op.get('attempt')!=0 or op.get('is_rework') or op.get('kind')!='process':issue('unexpected_repair_or_operation_kind',operation_id=op['id'])
        if op.get('process')=='ASSEMBLY':
            expected=f'{oid}/pump/1';pumps[oid]+=1
            if uid!=expected or pumps[oid]!=1:issue('noncanonical_or_duplicate_pump',unit_id=uid)
            parents=[f'{oid}/{r}/1' for r in ('housing','rotor','flange')]
            if Counter(op.get('parent_unit_ids',[]))!=Counter(parents):issue('noncanonical_assembly_parents',unit_id=uid)
            birth[uid]=op['start']
        pair=(uid,op.get('machine_id'))
        if pair in sources:issue('duplicate_reference_producer',unit_id=uid)
        sources[pair]=op
    if set(pumps)!=set(o['id'] for o in instance['orders']) or any(v!=1 for v in pumps.values()):issue('pump_birth_set')
    if Counter((o['unit_id'],o['recipe_step']) for o in trace['operations'])!=Counter((o['unit_id'],o['recipe_step']) for o in expected_ops):issue('mandatory_operation_identity_set')
    for op in trace['operations']:
        for uid in op.get('unit_ids',[])+op.get('parent_unit_ids',[]):
            if uid not in birth or op['start']<birth[uid]:issue('operation_before_birth',unit_id=uid)
    if Counter((m.get('unit_id'),m.get('from'),m.get('to')) for m in trace['moves'])!=Counter((m['unit_id'],m['from'],m['to']) for m in expected_moves):issue('mandatory_move_identity_set')
    for move in trace['moves']:
        uid=move.get('unit_id');pickup=move.get('pickup_tick',-1)
        if move.get('entity_type')!='part' or uid not in birth:
            issue('unknown_cargo_identity',unit_id=uid,move_id=move.get('id'));continue
        if move['from']=='RAW_A':
            producer_end=0
            if uid not in initial:issue('pump_cannot_be_raw_input',unit_id=uid)
        else:
            producer=sources.get((uid,move['from']))
            if producer is None:issue('missing_canonical_producer',unit_id=uid,move_id=move['id']);continue
            producer_end=producer['end']
        if pickup<birth[uid]:issue('pickup_before_birth',unit_id=uid,move_id=move['id'])
        if pickup<producer_end:issue('pickup_before_producer_completion',unit_id=uid,move_id=move['id'])
        loaded=[leg for leg in move.get('legs',[]) if leg.get('loaded')]
        if not loaded:issue('missing_loaded_cargo_legs',unit_id=uid,move_id=move['id'])
        for leg in loaded:
            if leg['start']<birth[uid]:issue('loaded_before_birth',unit_id=uid,move_id=move['id'])
            if leg['start']<producer_end:issue('loaded_before_producer_completion',unit_id=uid,move_id=move['id'])
            if leg['start']<pickup+instance['transport']['load_ticks']:issue('loaded_before_pickup_handling',unit_id=uid,move_id=move['id'])
        if move['start']<birth[uid]:planned.append(dict(move_id=move['id'],unit_id=uid,dispatch_start=move['start'],
            birth_tick=birth[uid],producer_completion=producer_end,pickup_tick=pickup,
            first_loaded_tick=min((leg['start'] for leg in loaded),default=None),empty_leg_count=sum(not leg.get('loaded') for leg in move.get('legs',[]))))
    qa=Counter()
    for event in trace['events']:
        if event.get('type') not in ('release','process_complete','consume','qa_result','ship'):
            issue('unexpected_reference_event',event_type=event.get('type'));continue
        uid=event.get('unit_id')
        if uid not in birth or event['tick']<birth[uid]:issue('event_before_canonical_birth',unit_id=uid)
        if event['type']=='qa_result':
            op=ops.get(event.get('operation_id'),{});qa[uid]+=1
            if op.get('process')!='QA' or op.get('unit_id')!=uid or qa[uid]!=1:issue('qa_operation_identity',unit_id=uid)
            draw=int.from_bytes(hashlib.sha256(f'{instance["seed"]}:quality:{uid}:0'.encode()).digest()[:8],'big')/2**64
            if event.get('keyed_uniform')!=draw:issue('immutable_qa_stream_key',unit_id=uid)
            if event.get('passed') is not True or event.get('defect_probability')!=0:issue('nonzero_quality_in_deterministic_reference',unit_id=uid)
    if set(qa)!=canonical or any(count!=1 for count in qa.values()):issue('qa_canonical_set')
    return dict(schema='stage2-reference-only-physical-encounter-identity.v1',valid=not issues,issues=issues,
                instance_sha256=INSTANCE_SHA,canonical_unit_count=len(canonical),initial_components=len(initial),canonical_pump_births=sum(pumps.values()),
                physical_part_moves_checked=len(trace['moves']),loaded_legs_checked=sum(leg.get('loaded',False) for m in trace['moves'] for leg in m.get('legs',[])),
                qa_streams_checked=sum(qa.values()),prebirth_planned_reservations=planned,
                source_hashes=SOURCES,audit_source_sha256=sha(__file__),
                interpretation='Reference-only identity audit at physical pickup and every loaded leg, with canonical producer/birth/parent/QA checks. Earlier empty dispatch or parked-AGV reservation is a planned future encounter, not physical cargo. Frozen generic identity_audit result is retained separately and is not relabeled valid. No input trace or frozen checker is modified.')
