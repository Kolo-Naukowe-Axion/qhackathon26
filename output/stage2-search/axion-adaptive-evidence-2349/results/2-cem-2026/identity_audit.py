"""Supplemental canonical lineage/QA stream audit for the frozen Stage2 trace.

Independent of engine/check.py. This supplements, never replaces, anchored
physical replay. Identity rules prevent a policy choosing names to redraw QA.
"""
from __future__ import annotations

from collections import Counter,defaultdict
import hashlib
import json
from pathlib import Path

COMPONENTS=('housing','rotor','flange')


def audit_trace(trace,instance=None):
    issues=[];spec=instance if instance is not None else trace.get('instance')
    def issue(code,message,row=None,**extra):
        value=dict(code=code,message=message,**extra)
        if row is not None:
            if 'tick' in row:value['tick']=row['tick']
            if 'id' in row:value['record_id']=row['id']
        issues.append(value)
    if trace.get('schema')!='metaltech-stage2-trace.v1' or not isinstance(spec,dict):
        return dict(valid=False,issues=[dict(code='schema_or_instance',message='Complete v1 trace and numerical instance required')],coverage=[])
    orders={};order_birth={};units={};births={};pump_counts=Counter();replacement_counts=Counter()
    initial_orders=spec.get('orders',[]);initial_units=spec.get('units',[])
    for order in initial_orders:
        oid=order.get('id')
        if not isinstance(oid,str) or not oid or oid in orders:
            issue('initial_order_identity','Initial order identities must be unique nonempty strings',order);continue
        orders[oid]=order;order_birth[oid]=0
    expected={f'{oid}/{recipe}/1':(oid,recipe) for oid in orders for recipe in COMPONENTS}
    seen=Counter()
    for unit in initial_units:
        uid=unit.get('id');seen[uid]+=1
        if uid not in expected or expected.get(uid)!=(unit.get('order_id'),unit.get('recipe')):
            issue('initial_component_identity','Initial stock must contain exactly the canonical three components per order, with no pump',unit,unit_id=uid);continue
        if seen[uid]>1:issue('duplicate_initial_component','Initial component identity is duplicated',unit,unit_id=uid)
        order=orders[unit['order_id']]
        if unit.get('family')!=order.get('family') or unit.get('release_tick')!=order.get('release_tick'):
            issue('initial_component_template','Initial component changes immutable order template',unit,unit_id=uid)
        units[uid]=dict(unit);births[uid]=0
    for uid in expected:
        if seen[uid]!=1:issue('initial_component_set','Exactly one canonical initial component required',unit_id=uid,count=seen[uid])
    if instance is not None and (trace.get('instance',{}).get('units')!=initial_units or trace.get('instance',{}).get('orders')!=initial_orders):
        issue('anchored_initial_identity','Trace initial identity tables differ from the supplied numerical instance')
    events=trace.get('events',[]);urgent=[]
    for event in sorted((e for e in events if e.get('type')=='urgent_order'),key=lambda e:e.get('tick',-1)):
        order=event.get('order',{});oid=order.get('id');canonical=f'U{len(urgent)+1:02d}'
        if oid!=canonical or oid in orders:
            issue('urgent_order_identity','Urgent order identity must follow fixed U01,U02,... revelation order',event,expected=canonical,actual=oid)
        if not isinstance(oid,str):continue
        orders[oid]=order;order_birth[oid]=event.get('tick',0);urgent.append(oid)
    new_events=[e for e in events if e.get('type')=='new_unit'];new_by_id=defaultdict(list)
    for event in new_events:new_by_id[event.get('unit',{}).get('id')].append(event)
    # Urgent components are born exactly once, at their order revelation boundary.
    authorized_new=set()
    for oid in urgent:
        order=orders[oid]
        for recipe in COMPONENTS:
            uid=f'{oid}/{recipe}/1';matches=new_by_id.get(uid,[])
            if len(matches)!=1:
                issue('urgent_component_set','Urgent order needs exactly three canonical component births',unit_id=uid,count=len(matches));continue
            event=matches[0];unit=event['unit'];authorized_new.add(uid)
            if (unit.get('order_id'),unit.get('recipe'),unit.get('family'),unit.get('release_tick'),unit.get('initial_location'),event.get('tick'))!=(oid,recipe,order.get('family'),order.get('release_tick'),'RAW_A',order_birth[oid]):
                issue('urgent_component_template','Urgent component identity/template differs from its revealed order',event,unit_id=uid)
            units[uid]=dict(unit);births[uid]=event.get('tick',0)
    # Replacements retain the original identity; no recursive or pump replacement.
    for event in (e for e in events if e.get('type')=='replacement'):
        original=event.get('unit_id');replacement=event.get('replacement_unit_id',event.get('replacement_id'))
        replacement_counts[original]+=1;unit=units.get(original)
        if (unit is None or unit.get('recipe') not in COMPONENTS or original not in expected and original not in authorized_new
                or '~r' in str(original) or replacement_counts[original]>1 or replacement!=f'{original}~r1'):
            issue('replacement_identity','One replacement must be original canonical component UID + ~r1; pump/recursive/renamed births forbidden',event,unit_id=original,replacement_id=replacement);continue
        matches=new_by_id.get(replacement,[])
        if len(matches)!=1:
            issue('replacement_birth_count','Authorized replacement needs exactly one new-unit birth',event,replacement_id=replacement,count=len(matches));continue
        birth=matches[0];new=birth['unit'];authorized_new.add(replacement)
        if (new.get('order_id'),new.get('recipe'),new.get('family'),new.get('release_tick'),new.get('initial_location'),birth.get('tick'))!=(unit.get('order_id'),unit.get('recipe'),unit.get('family'),event.get('release_tick'),'RAW_A',event.get('tick')):
            issue('replacement_template','Replacement birth changes fixed identity/template or creation boundary',birth,unit_id=replacement)
        units[replacement]=dict(new);births[replacement]=birth.get('tick',0)
    for uid,matches in new_by_id.items():
        if uid not in authorized_new:issue('unauthorized_component_birth','New unit is neither canonical urgent component nor authorized replacement',matches[0],unit_id=uid)
        if len(matches)>1:issue('duplicate_component_birth','A unit identity may be born only once',matches[0],unit_id=uid,count=len(matches))
    operations=trace.get('operations',[]);ops={}
    for op in operations:
        if op.get('id') in ops:issue('duplicate_operation_id','Operation IDs must be unique for QA references',op)
        ops[op.get('id')]=op
    for op in sorted(operations,key=lambda o:(o.get('start',0),str(o.get('id')))):
        if op.get('kind')!='process':continue
        oid=op.get('order_id');uid=op.get('unit_id');ids=op.get('unit_ids',[]);tick=op.get('start',-1)
        if op.get('process')=='ASSEMBLY' and not op.get('is_rework',False):
            canonical=f'{oid}/pump/1';pump_counts[oid]+=1
            if oid not in orders or tick<order_birth.get(oid,0):issue('pump_order_identity','Pump birth requires a known revealed order',op)
            if uid!=canonical or ids!=[canonical]:issue('pump_birth_identity','Assembly birth must use the fixed order/pump/1 UID and singleton output',op,expected=canonical,actual=uid)
            if pump_counts[oid]!=1 or uid in units:issue('duplicate_pump_birth','Each order has at most one initial pump; no new QA stream after scrap',op,order_id=oid)
            if isinstance(uid,str):
                units[uid]=dict(id=uid,order_id=oid,recipe='pump');births[uid]=tick
        if uid not in ids or len(ids)!=len(set(ids)):issue('operation_primary_identity','Primary unit must appear exactly once in the operation unit list',op)
        if uid in units and units[uid].get('order_id')!=oid:issue('operation_order_identity','Primary unit/order identity disagrees',op)
        if 'recipe_steps' in op and set(op['recipe_steps'])!=set(ids):issue('recipe_step_identity','Per-unit recipe step keys must match operation units',op)
    def reference(uid,tick,row,field):
        if uid not in units:issue('unknown_unit_reference','Executed part reference has no authorized canonical birth',row,unit_id=uid,field=field)
        elif tick<births.get(uid,0):issue('unit_before_identity_birth','Part referenced before its canonical birth',row,unit_id=uid,field=field)
    for op in operations:
        if op.get('kind')!='process':continue
        for uid in op.get('unit_ids',[]):reference(uid,op.get('start',-1),op,'unit_ids')
        for uid in op.get('parent_unit_ids',[]):
            reference(uid,op.get('start',-1),op,'parent_unit_ids')
            if uid in units and (units[uid].get('recipe') not in COMPONENTS or units[uid].get('order_id')!=op.get('order_id')):
                issue('parent_lineage_identity','Assembly parents retain same-order canonical component lineage',op,unit_id=uid)
    for move in trace.get('moves',[]):
        if move.get('entity_type')=='part':reference(move.get('unit_id'),move.get('start',-1),move,'part_move')
    qa_seen=Counter();seed=spec.get('seed');qa_count=0
    for event in events:
        kind=event.get('type')
        if kind in ('release','process_complete','qa_result','consume','ship','repair','scrap','replacement'):
            reference(event.get('unit_id'),event.get('tick',-1),event,kind)
        if kind=='qa_result':
            qa_count+=1;uid=event.get('unit_id');op=ops.get(event.get('operation_id'),{});attempt=op.get('attempt')
            if op.get('process')!='QA' or uid not in op.get('unit_ids',[]) or type(attempt) is not int or attempt not in (0,1):
                issue('qa_identity_reference','Inspection must reference that unit and bounded attempt on its QA operation',event);continue
            qa_seen[uid,attempt]+=1
            if qa_seen[uid,attempt]>1:issue('duplicate_qa_identity','A unit/attempt cannot receive a fresh inspection stream',event,unit_id=uid,attempt=attempt)
            if type(seed) is not int:
                issue('qa_seed','Integer audit seed required to verify immutable QA stream',event);continue
            expected_draw=int.from_bytes(hashlib.sha256(f'{seed}:quality:{uid}:{attempt}'.encode()).digest()[:8],'big')/2**64
            if event.get('keyed_uniform')!=expected_draw:
                issue('qa_stream_key','QA draw must use quality:{unit_id}:{attempt}; operation ID never selects random stream',event,unit_id=uid,attempt=attempt,expected=expected_draw,actual=event.get('keyed_uniform'))
    legacy=spec.get('quality',{}).get('paired_key')
    return dict(schema='stage2-identity-audit.v1',valid=not issues,issues=issues,
        coverage=['canonical_initial_components','canonical_urgent_order_and_components','single_canonical_pump_birth_per_order',
            'bounded_canonical_replacement','authorized_part_references','immutable_unit_attempt_qa_stream'],
        metrics=dict(initial_components=len(initial_units),urgent_orders=len(urgent),authorized_unit_identities=len(units),
            initial_pump_births=sum(pump_counts.values()),replacement_events=sum(replacement_counts.values()),qa_results=qa_count),
        metadata_notes=[dict(field='instance.quality.paired_key',declared_value=legacy,
            actual_implemented_key='quality:{unit_id}:{attempt}',operation_id_role='Diagnostic reference only, never a random-stream key',
            status='Legacy descriptive metadata includes operation_id; execution/TRACE_CONTRACT use unit+attempt' if isinstance(legacy,list) and 'operation_id' in legacy else 'Execution key verified independently')],
        provenance=dict(auditor_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            instance_anchor='supplied_instance' if instance is not None else 'trace_instance_only'),
        limitations=['Supplement only: run anchored check.py physical replay as well.',
            'Does not certify nonanticipativity, optimality or model provenance; a trusted fresh numerical instance is required for external identity anchoring.'])


def main():
    import argparse,gzip
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('trace',type=Path);p.add_argument('--instance',type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    payload=a.trace.read_bytes();raw=gzip.decompress(payload) if a.trace.suffix=='.gz' else payload
    result=audit_trace(json.loads(raw),json.loads(a.instance.read_bytes()) if a.instance else None)
    if a.output.exists():raise ValueError('Preserve earlier audit; use a new output file')
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2));return int(not result['valid'])


if __name__=='__main__':raise SystemExit(main())
