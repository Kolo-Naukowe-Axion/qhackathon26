"""Authorized one-field contraction of a parked-AGV wait in a COPY only."""
from copy import deepcopy
import importlib.util
from pathlib import Path

from stage2.identity_audit import audit_trace

HERE=Path(__file__).resolve().parent
SPEC=importlib.util.spec_from_file_location('reference_physical_encounter_for_normalization',HERE/'reference_identity.py')
R=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(R)


def structural_diff(a,b,path=()):
    if type(a) is not type(b):return [(path,a,b)]
    if isinstance(a,dict):
        if set(a)!=set(b):return [(path,a,b)]
        return [v for key in a for v in structural_diff(a[key],b[key],path+(key,))]
    if isinstance(a,list):
        if len(a)!=len(b):return [(path,a,b)]
        return [v for i,(x,y) in enumerate(zip(a,b)) for v in structural_diff(x,y,path+(i,))]
    return [] if a==b else [(path,a,b)]


def normalize(trace,instance):
    scoped=R.audit(trace,instance)
    if not scoped['valid']:raise ValueError('Original must pass reference-scoped physical-encounter identity')
    original=audit_trace(trace,instance)
    expected=[dict(code='unit_before_identity_birth',message='Part referenced before its canonical birth',
                   unit_id='P04/pump/1',field='part_move',record_id='move74')]
    if original['valid'] or original['issues']!=expected:raise ValueError('Expected sole literal stock-auditor prebirth reservation')
    entries=scoped['prebirth_planned_reservations']
    if len(entries)!=1:raise ValueError('Exactly one known reservation may be contracted')
    entry=entries[0]
    if entry!=dict(move_id='move74',unit_id='P04/pump/1',dispatch_start=1382,birth_tick=1420,
                   producer_completion=1480,pickup_tick=1480,first_loaded_tick=1481,empty_leg_count=0):
        raise ValueError('Only the held zero-empty-leg move74 wait is supported')
    index=next(i for i,m in enumerate(trace['moves']) if m['id']=='move74');move=trace['moves'][index]
    if any(leg['start']<1420 for leg in move['legs']):raise ValueError('Cannot remove physical legs before birth')
    previous=trace['moves'][index-1]
    if previous['to']!='A1' or previous['end']>1382:raise ValueError('AGV must already be parked at source before the contracted wait')
    result=deepcopy(trace);result['moves'][index]['start']=1420
    differences=structural_diff(trace,result)
    if differences!=[(('moves',index,'start'),1382,1420)]:raise ValueError('Transformation must change exactly one dispatch field')
    return result,dict(original_stock_identity=original,reference_scoped_identity=scoped,
                       structural_changes=[dict(path=list(differences[0][0]),old=1382,new=1420)],
                       previous_agv_delivery=dict(move_id=previous['id'],end=previous['end'],location=previous['to']),
                       scope='Deterministic audit-only witness COPY: one parked-AGV wait/reservation begins at canonical birth instead of earlier; every physical leg, operation, pickup/drop, shipping, worker, energy, metric, source instance and original CP artifact remains unchanged. This is not literal solver output, a new factory execution or an added performance sample.')
