"""Metadata-only activity audit of first-tape/first-actor retained final traces.

No factory, controller or checker is imported or executed. Checked execution
status comes from the sealed evaluation; this postprocessor checks artifact
links and counts observed records, not causal bottlenecks or population rates.
"""
from __future__ import annotations

import argparse
from collections import Counter,defaultdict
from copy import deepcopy
import gzip
import hashlib
import json
import math
from pathlib import Path

SCHEMA='stage2-retained-final-activity.v1'


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def file_hash(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def observed(start,end,horizon):return max(0,min(end,horizon)-max(0,start))


def union_ticks(intervals):
    total=0;end=None
    for a,b in sorted(intervals):
        if b<=a:continue
        if end is None or a>end:total+=b-a;end=b
        elif b>end:total+=b-end;end=b
    return total


def energy_activity(trace):
    """Count literal action-table electrical flows; no export is invented."""
    horizon=trace['horizon_ticks'];minutes=trace['tick_minutes'];table=trace['instance']['energy']
    actions={a['id']:a for a in table['battery_actions']};rows=[r for r in trace['energy'] if 0<=r['tick']<horizon]
    ticks=[r['tick'] for r in rows]
    if sorted(ticks)!=list(range(horizon)):raise ValueError('Activity requires exactly one electrical row per execution tick')
    rows.sort(key=lambda r:r['tick']);counts=Counter(r['battery_action'] for r in rows)
    charge=discharge=0.;issues=[];previous=table['stationary_soc_initial'];tol=1e-6
    for r in rows:
        if r['battery_action'] not in actions:raise ValueError('Unknown battery action; cannot infer physical flows')
        a=actions[r['battery_action']];charge+=a['charge_kw']*minutes/60;discharge+=a['discharge_kw']*minutes/60
        if not math.isclose(r['soc_before'],previous,abs_tol=tol,rel_tol=0) or not math.isclose(r['soc']-r['soc_before'],a['soc_delta'],abs_tol=tol,rel_tol=0):issues.append(dict(code='soc_transition',tick=r['tick']))
        balance=r['grid_kw']+r['solar_kw']+a['discharge_kw']-r['load_kw']-a['charge_kw']-r['curtailed_kw']
        if abs(balance)>tol:issues.append(dict(code='electrical_balance',tick=r['tick']))
        if r['grid_kw']<-tol:issues.append(dict(code='negative_grid_export',tick=r['tick']))
        if r['grid_kw']>r['cap_kw']+tol:issues.append(dict(code='grid_cap',tick=r['tick']))
        if not table['stationary_soc_min']-tol<=r['soc']<=table['stationary_soc_capacity']+tol:issues.append(dict(code='soc_bounds',tick=r['tick']))
        if r['curtailed_kw']<-tol or r['curtailed_kw']>r['solar_kw']+tol:issues.append(dict(code='curtailment_outside_solar',tick=r['tick']))
        previous=r['soc']
    headroom=[r['cap_kw']-r['grid_kw'] for r in rows]
    return dict(action_ticks=dict(counts),charge_minutes=counts['charge']*minutes,discharge_minutes=counts['discharge']*minutes,
        ac_battery_charge_kwh=charge,ac_battery_discharge_kwh=discharge,
        grid_import_kwh=sum(max(0,r['grid_kw'])*minutes/60 for r in rows),
        negative_grid_export_kwh=sum(max(0,-r['grid_kw'])*minutes/60 for r in rows),
        curtailed_solar_kwh=sum(r['curtailed_kw']*minutes/60 for r in rows),
        no_export_declared=table.get('no_export') is True,no_export_balance_soc_contact_checks_passed=not issues,
        contact_check_issues=issues,grid_cap_contact_minutes=sum(abs(x)<=tol for x in headroom)*minutes,
        min_grid_headroom_kw=min(headroom) if headroom else None,
        derated_grid_minutes=sum(r['cap_kw']<table['normal_grid_cap_kw']-tol for r in rows)*minutes,
        stationary_min_soc=min([table['stationary_soc_initial']]+[r['soc'] for r in rows]),terminal_soc=previous,
        terminal_reserve_met=previous>=table['stationary_soc_terminal_min']-tol,
        interpretation='Action-table AC flows; nonnegative grid is import only. Curtailment is not export. Balance/SOC checks are a small metadata consistency supplement,not a repeated full physical check. Contact does not prove causal binding.')


def summarize_trace(trace):
    """Pure record semantics; checked/identity status must be supplied separately."""
    if trace.get('schema')!='metaltech-stage2-trace.v1':raise ValueError('Expected complete v1 execution trace')
    horizon=trace['horizon_ticks'];minutes=trace['tick_minutes'];instance=trace['instance']
    if horizon!=instance['horizon_ticks'] or minutes!=instance['tick_minutes']:raise ValueError('Trace/instance horizon or time-unit mismatch')
    operations=[o for o in trace['operations'] if 0<=o['start']<horizon]
    production=[o for o in operations if o['kind']=='process'];moves=[m for m in trace['moves'] if 0<=m['start']<horizon]
    events=[e for e in trace['events'] if 0<=e['tick']<=horizon];ec=Counter(e['type'] for e in events)
    completed={e['operation_id'] for e in events if e['type']=='process_complete'}
    transports=[m for m in moves if m['kind']=='transport'];arrived=[m for m in transports if m['drop_tick']<=horizon]
    charges=[m for m in moves if m['kind']=='charge'];bridge=[]
    for m in moves:
        for leg in m.get('legs',[]):
            if {leg['from'],leg['to']}=={'HUB_A','HUB_B'} and leg['end']<=horizon:
                bridge.append(dict(move_id=m['id'],loaded=leg['loaded'],start=leg['start'],end=leg['end']))
    workers=defaultdict(list)
    for o in operations:
        intervals=o.get('worker_intervals')
        if intervals is None:intervals=[dict(worker_id=w,start=o['start'],end=o['end']) for w in o['worker_ids']]
        for x in intervals:workers[x['worker_id']].append((max(0,x['start']),min(horizon,x['end'])))
    walks=[w for w in trace.get('worker_moves',[]) if 0<=w['start']<horizon]
    used={tid for o in operations for tid in o['tool_ids']};rentals=[]
    for e in events:
        if e['type']!='lease_delivery':continue
        tid=e['tool']['id'];uses=[o for o in operations if tid in o['tool_ids'] and o['start']>=e['tick']]
        delivered_moves=[m for m in arrived if m.get('entity_type')=='tool' and m['unit_id']==tid and m['pickup_tick']>=e['tick']]
        rentals.append(dict(option_id=e['option_id'],tool_id=tid,actual_birth_tick=e['tick'],used_after_birth=bool(uses),first_use_tick=min((o['start'] for o in uses),default=None),completed_agv_tool_transports_after_birth=len(delivered_moves)))
    replacement_ids={e['replacement_id'] for e in events if e['type']=='replacement'}
    released={e['unit_id'] for e in events if e['type']=='release'}
    stock=dict(instance.get('raw_stock_units',{}));minimum=dict(stock)
    for e in sorted(events,key=lambda e:e['tick']):
        if e['type']=='release' and e['recipe'] in stock:
            stock[e['recipe']]-=1;minimum[e['recipe']]=min(minimum[e['recipe']],stock[e['recipe']])
        elif e['type']=='delivery':
            for recipe,count in e['contents'].items():stock[recipe]=stock.get(recipe,0)+count
    outages=[e for e in events if e['type']=='outage'];delays=[e for e in events if e['type']=='delivery_delay'];urgents=[e for e in events if e['type']=='urgent_order']
    counts=dict(production_operations_started=len(production),production_operations_completed=len({o['id'] for o in production}&completed),
        production_units_completed=ec['process_complete'],setup_operations=sum(o.get('setup_ticks',0)>0 for o in production),
        setup_minutes=sum(observed(o['start'],o['start']+o.get('setup_ticks',0),horizon) for o in production)*minutes,
        rework_operations_started=sum(bool(o.get('is_rework')) for o in production),qa_inspections_completed=ec['qa_result'],
        qa_failures=sum(e['type']=='qa_result' and e['passed'] is False for e in events),repair_events=ec['repair'],scrap_events=ec['scrap'],
        replacement_events=ec['replacement'],replacement_units_actually_released=len(replacement_ids&released),
        machine_maintenance_started=sum(o['kind']=='maintenance' for o in operations),machine_maintenance_completed=ec['maintenance_complete'],
        tool_services_started=sum(o['kind']=='tool_service' for o in operations),tool_services_completed=ec['tool_service_complete'],
        rental_requests=ec['lease_request'],rental_tools_actually_delivered=len(rentals),rental_tools_actually_used=sum(r['used_after_birth'] for r in rentals),
        agv_transport_commitments=len(transports),agv_transport_arrivals=len(arrived),
        agv_part_arrivals=sum(m.get('entity_type','part')=='part' for m in arrived),agv_tool_arrivals=sum(m.get('entity_type')=='tool' for m in arrived),
        agv_charge_sessions_committed=len(charges),agv_charge_sessions_ended_by_cutoff=sum(m['end']<=horizon for m in charges),
        agv_charge_minutes=sum(observed(m['charge_start'],m['end'],horizon) for m in charges)*minutes,
        bridge_crossings=len(bridge),loaded_bridge_crossings=sum(b['loaded'] for b in bridge),empty_bridge_crossings=sum(not b['loaded'] for b in bridge),
        bridge_occupied_minutes=union_ticks([(b['start'],b['end']) for b in bridge])*minutes,
        worker_walks=len(walks),worker_walk_minutes=sum(observed(w['start'],w['end'],horizon) for w in walks)*minutes,
        worker_attendance_minutes=sum(union_ticks(v) for v in workers.values())*minutes,
        initial_bom_assembly_starts=sum(o['process']=='ASSEMBLY' and bool(o.get('parent_unit_ids')) for o in production),
        assembly_parent_consumption_events=ec['consume'],heat_multiunit_batches=sum(o['process']=='HEAT' and len(o['unit_ids'])>1 for o in production),
        realized_urgent_orders=len(urgents),realized_outage_events=len(outages),realized_delivery_delay_events=len(delays),actual_stock_deliveries=ec['delivery'])
    return dict(horizon_ticks=horizon,tick_minutes=minutes,physical_horizon_hours=horizon*minutes/60,
        counts=counts,event_counts=dict(ec),processing_modes=dict(Counter(o['mode'] for o in production)),
        process_counts=dict(Counter(o['process'] for o in production)),production_machine_ids=sorted({o['machine_id'] for o in production}),
        unused_production_machine_ids=sorted({m['id'] for m in instance['machines']}-{o['machine_id'] for o in production}),
        worker_ids_with_attendance=sorted(w for w,v in workers.items() if union_ticks(v)),tool_ids_used=sorted(used),rental_deliveries=rentals,
        energy=energy_activity(trace),minimum_observed_raw_stock=minimum,terminal_raw_stock=stock,
        raw_stock_zero_observed=any(v==0 for v in minimum.values()),
        omitted_activity_reconstructions='No new input-buffer/output-blocking replay is claimed here. Repacking can transfer a unit again before consumption; simple next-process occupancy counting would overcount such intervals.',
        shocks=dict(realized_stages=deepcopy(trace['audit']['realized_stages']),outages=outages,delivery_delays=delays,
            urgent_order_ids=[e['order']['id'] for e in urgents],outage_machine_minutes=sum(observed(e['start'],e['end'],horizon) for e in outages)*minutes),
        implemented_feature_flags=deepcopy(instance.get('feature_status',{})),
        interpretation='Observed events/intervals only. Arrivals/completions at H count: the engine processes that boundary before stopping. Durations clip to[0,H),electrical rows to0..H-1. Feature flags are metadata,not activity; contact is not proof of causal binding.')


def _verify_bundle(evaluation,manifest):
    unsigned=deepcopy(manifest);seal=unsigned.pop('manifest_sha256',None)
    if seal!=digest(unsigned) or evaluation.get('manifest_sha256')!=seal:raise ValueError('Evaluation/manifest seal mismatch')
    if evaluation.get('source_hashes')!=manifest['source_hashes']:raise ValueError('Evaluation/source manifest differs')
    protocol=manifest['protocol']['payload'];p=deepcopy(protocol);recorded=p.pop('protocol_sha256',None)
    if recorded!=hashlib.sha256(json.dumps(p,sort_keys=True).encode()).hexdigest() or evaluation.get('protocol_sha256')!=recorded:raise ValueError('Protocol seal mismatch')
    if len(protocol['leaves'])!=8:raise ValueError('This audit is predeclared for exactly8 disruption leaves')
    if manifest.get('trace_policy') not in ('first_per_leaf','all'):raise ValueError('Manifest did not predeclare retained traces')
    if not manifest.get('actor_seeds'):raise ValueError('First declared actor is required')
    return protocol


def selected_rows(evaluation,manifest,method_id,orders,horizon=None):
    protocol=_verify_bundle(evaluation,manifest)
    if orders not in (12,32):raise ValueError('Activity audit scope is predeclared selected12 and stretch32')
    methods=[m for m in manifest['methods'] if m['id']==method_id]
    if len(methods)!=1:raise ValueError('Explicit method must occur exactly once in manifest')
    configs=[c for c in methods[0].get('configs',manifest['configs']) if c['orders']==orders and (horizon is None or c['horizon']==horizon)]
    if len(configs)!=1:raise ValueError('Select exactly one declared physical context; specify horizon if ambiguous')
    config=configs[0];actor=manifest['actor_seeds'][0];chosen=[]
    group=[r for r in evaluation['rows'] if r['method_id']==method_id and r['config']==config]
    for leaf_id,leaf in enumerate(protocol['leaves']):
        seed=leaf['seeds'][0];matches=[r for r in group if r['leaf']==leaf_id and r['seed']==seed and r['policy_seed']==actor]
        if len(matches)!=1:chosen.append(dict(leaf=leaf_id,seed=seed,policy_seed=actor,missing_or_duplicate_rows=len(matches)));continue
        row=matches[0]
        if row.get('manifest_sha256')!=manifest['manifest_sha256'] or row.get('protocol_sha256')!=protocol['protocol_sha256']:raise ValueError('Selected row seal mismatch')
        if row.get('checker_sha256')!=manifest['source_hashes']['stage2/check.py'] or row.get('leaf_outcomes')!=leaf['outcomes']:raise ValueError('Selected row checker/leaf mismatch')
        chosen.append(row)
    return config,chosen,dict(evaluation_rows_in_context=len(group),invalid_evaluation_rows_in_context=sum(not r.get('valid',False) for r in group),
        full_protocol_tapes=protocol['total_tapes'],declared_actor_replicas=len(manifest['actor_seeds']),selected_retained_environment_tapes=8)


def _resolve_trace(row,evaluation_path,trace_root):
    original=Path(row['trace_path']);root=Path(trace_root) if trace_root else evaluation_path.parent
    candidates=[root/original.name,root/'traces'/original.name]
    if not any(p.is_file() for p in candidates) and original.exists():candidates.append(original)
    existing=list(dict.fromkeys(p.resolve() for p in candidates if p.is_file()))
    if len(existing)!=1:raise ValueError('Exact retained trace path missing or ambiguous; no substitute trace is selected')
    return existing[0]


def analyze(evaluation_path,method_id,orders,*,manifest_path=None,trace_root=None,horizon=None,expected_manifest_sha256=None):
    evaluation_path=Path(evaluation_path).resolve();manifest_path=Path(manifest_path) if manifest_path else evaluation_path.parent/'manifest.json'
    input_hash=file_hash(evaluation_path);manifest_hash=file_hash(manifest_path)
    evaluation=json.loads(evaluation_path.read_text());manifest=json.loads(manifest_path.read_text())
    if expected_manifest_sha256 is not None and expected_manifest_sha256!=manifest.get('manifest_sha256'):raise ValueError('Unexpected pinned manifest')
    config,chosen,context=selected_rows(evaluation,manifest,method_id,orders,horizon);records=[]
    for row in chosen:
        entry={k:deepcopy(row[k]) for k in ('leaf','seed','policy_seed')};entry['eligible_checked_activity']=False
        try:
            if 'missing_or_duplicate_rows' in row:raise ValueError('Missing/duplicated predeclared first row; never replace it')
            if not row.get('valid') or not row.get('terminal_requirements_met') or not row.get('identity_audit',{}).get('valid'):raise ValueError('Predeclared first execution is invalid/unverified; never replace it')
            path=_resolve_trace(row,evaluation_path,trace_root);raw=path.read_bytes();plain=gzip.decompress(raw) if path.suffix=='.gz' else raw
            recorded_bytes=raw if Path(row['trace_path']).suffix=='.gz' else plain
            if hashlib.sha256(recorded_bytes).hexdigest()!=row['trace_sha256']:raise ValueError('Retained trace SHA differs from measured row')
            trace=json.loads(plain)
            if digest(trace['instance'])!=row['physical_instance_sha256'] or trace.get('metrics')!=row['metrics']:raise ValueError('Trace instance/metrics differ from measured row')
            if [s['outcome'] for s in trace['audit']['realized_stages']]!=row['leaf_outcomes']:raise ValueError('Trace realized leaf differs from predeclared selected leaf')
            if trace.get('validation',{}).get('valid') is not True:raise ValueError('Trace annotation differs from checked evaluation')
            if digest(trace['instance'])!=row.get('executed_instance_sha256',row['physical_instance_sha256']):raise ValueError('Executed-instance digest mismatch')
            activity=summarize_trace(trace)
            if activity['energy']['contact_check_issues']:raise ValueError('Supplemental electrical record consistency failed')
            entry.update(eligible_checked_activity=True,source_trace=dict(path=str(path),file_sha256=hashlib.sha256(raw).hexdigest(),json_payload_sha256=hashlib.sha256(plain).hexdigest(),row_recorded_sha256=row['trace_sha256']),
                physical_instance_sha256=row['physical_instance_sha256'],checker_sha256=row['checker_sha256'],identity_audit=deepcopy(row['identity_audit']),activity=activity)
        except Exception as exc:entry.update(error=dict(type=type(exc).__name__,message=str(exc)),source_row_status={k:deepcopy(row.get(k)) for k in ('valid','issues','error','trace_path','trace_sha256')})
        records.append(entry)
    complete=all(r['eligible_checked_activity'] for r in records) and len(records)==8
    totals={};exercised={}
    if complete:
        keys=records[0]['activity']['counts']
        totals={k:sum(r['activity']['counts'][k] for r in records) for k in keys}
        exercised={k:sum(r['activity']['counts'][k]>0 for r in records) for k in keys}
    result=dict(schema=SCHEMA,method_id=method_id,config=config,context=context,selection_complete_and_verified=complete,records=records,
        retained_subset_count_sums=totals if complete else None,
        retained_trace_counts_with_positive_activity=exercised if complete else None,
        aggregate_scope='Sums across only8 predeclared first-seed/first-actor retained executions,one per leaf; not a probability-weighted estimate or activity rate across all256 environments. Actors are not additional environments.',
        binding_claims='None: activity and grid/stock contact do not establish marginal capacity value or causal bottlenecks.',
        provenance=dict(evaluation_path=str(evaluation_path),evaluation_file_sha256=input_hash,manifest_path=str(manifest_path.resolve()),manifest_file_sha256=manifest_hash,
            manifest_sha256=manifest['manifest_sha256'],protocol_sha256=manifest['protocol']['payload']['protocol_sha256'],frozen_evaluation_source_hashes=manifest['source_hashes'],
            analysis_source_sha256=file_hash(__file__),verification='Sealed evaluation/row/trace links checked; original physical/identity checker statuses consumed,not recomputed; no simulator/controller/checker execution'))
    if input_hash!=file_hash(evaluation_path) or manifest_hash!=file_hash(manifest_path):raise RuntimeError('Input artifact changed during activity audit')
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--evaluation',type=Path,required=True);p.add_argument('--manifest',type=Path)
    p.add_argument('--method',required=True);p.add_argument('--orders',type=int,choices=(12,32),required=True);p.add_argument('--horizon',type=int)
    p.add_argument('--trace-root',type=Path);p.add_argument('--expected-manifest-sha256');p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise ValueError('Refuse to overwrite retained activity evidence')
    r=analyze(a.evaluation,a.method,a.orders,manifest_path=a.manifest,trace_root=a.trace_root,horizon=a.horizon,expected_manifest_sha256=a.expected_manifest_sha256)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    source=a.output.with_suffix('.analysis-source.py')
    with source.open('x') as f:f.write(Path(__file__).read_text())
    r['provenance']['analysis_source_snapshot']=str(source.resolve())
    with a.output.open('x') as f:f.write(json.dumps(r,indent=2)+'\n')
    print(json.dumps(dict(selection_complete_and_verified=r['selection_complete_and_verified'],context=r['context'],counts=r['retained_subset_count_sums']),indent=2))
    if not r['selection_complete_and_verified']:raise SystemExit(1)


if __name__=='__main__':main()
