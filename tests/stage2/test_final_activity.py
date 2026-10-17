"""Synthetic record semantics/integrity fixtures; not factory-performance runs."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from copy import deepcopy

from stage2.final_activity import analyze,digest,energy_activity,selected_rows,summarize_trace


def fixture():
    table=dict(stationary_soc_initial=10,stationary_soc_min=2,stationary_soc_capacity=30,stationary_soc_terminal_min=5,normal_grid_cap_kw=30,no_export=True,
        battery_actions=[dict(id='idle',charge_kw=0,discharge_kw=0,soc_delta=0),dict(id='charge',charge_kw=10,discharge_kw=0,soc_delta=9),dict(id='discharge',charge_kw=0,discharge_kw=9,soc_delta=-10)])
    energy=[];soc=10
    for tick in range(10):
        action=table['battery_actions'][1 if tick==0 else 2 if tick==1 else 0];solar=16 if tick==2 else 0;net=12-solar+action['charge_kw']-action['discharge_kw']
        energy.append(dict(tick=tick,battery_action=action['id'],soc_before=soc,soc=soc+action['soc_delta'],load_kw=12,solar_kw=solar,grid_kw=max(0,net),curtailed_kw=max(0,-net),cap_kw=30));soc+=action['soc_delta']
    def op(oid,start,end,process='T',kind='process',**extra):
        return dict(id=oid,start=start,end=end,process=process,kind=kind,machine_id=oid,unit_ids=[oid+'/part'],parent_unit_ids=[],worker_ids=['W1'],worker_intervals=[dict(worker_id='W1',start=start,end=min(end,start+2))],tool_ids=[],mode='standard',setup_ticks=0,**extra)
    operations=[op('O0',0,4),op('O1',4,8,process='HEAT'),op('O2',6,9,process='ASSEMBLY'),op('O3',8,10,process='QA',is_rework=True),op('O4',2,5,kind='maintenance'),op('O5',5,12,kind='tool_service')]
    operations[0]['setup_ticks']=1;operations[1]['unit_ids']=['c1','c2'];operations[2]['parent_unit_ids']=['h','r','f'];operations[3]['tool_ids']=['rental']
    def move(mid,start,end,entity='part'):
        return dict(id=mid,start=start,end=end,pickup_tick=start,drop_tick=end,kind='transport',entity_type=entity,unit_id='rental' if entity=='tool' else mid,legs=[dict(**{'from':'HUB_A','to':'HUB_B'},start=end-4,end=end,loaded=True)])
    moves=[move('M0',0,9),move('M1',7,10,'tool'),move('M2',8,14),dict(id='M3',kind='charge',start=0,end=12,charge_start=2,legs=[])]
    events=[dict(tick=4,type='process_complete',operation_id='O0'),dict(tick=8,type='process_complete',operation_id='O1'),dict(tick=8,type='process_complete',operation_id='O1'),dict(tick=9,type='process_complete',operation_id='O2'),dict(tick=10,type='process_complete',operation_id='O3'),dict(tick=10,type='qa_result',passed=False),dict(tick=10,type='replacement',replacement_id='new-component'),dict(tick=5,type='maintenance_complete'),dict(tick=0,type='lease_request'),dict(tick=1,type='lease_request'),dict(tick=6,type='lease_delivery',option_id='kit',tool={'id':'rental'})]
    events.extend(dict(tick=6,type='consume',unit_id=uid) for uid in ('h','r','f'))
    return dict(schema='metaltech-stage2-trace.v1',horizon_ticks=10,tick_minutes=1,
        instance=dict(horizon_ticks=10,tick_minutes=1,energy=table,machines=[{'id':o['machine_id']} for o in operations],raw_stock_units={'housing':3},feature_status={'enabled_but_not_exercised':True}),
        operations=operations,moves=moves,events=events,energy=energy,worker_moves=[dict(worker_id='W1',start=9,end=12)],audit={'realized_stages':[]},validation={'valid':True},metrics={'fixture_only':True})


def bundle(folder):
    config=dict(orders=12,horizon=10,profile='full');protocol=dict(total_tapes=16,leaves=[dict(outcomes=[f'leaf{j}'],seeds=[10000+j,20000+j]) for j in range(8)])
    protocol['protocol_sha256']=hashlib.sha256(json.dumps(protocol,sort_keys=True).encode()).hexdigest()
    manifest=dict(source_hashes={'stage2/check.py':'a'*64},configs=[config],actor_seeds=[7,13],methods=[dict(id='selected')],protocol=dict(payload=protocol),trace_policy='first_per_leaf')
    manifest['manifest_sha256']=digest(manifest);rows=[];(folder/'traces').mkdir()
    for leaf_id,leaf in enumerate(protocol['leaves']):
        trace=fixture();trace['audit']['realized_stages']=[{'outcome':leaf['outcomes'][0]}]
        path=folder/'traces'/f'leaf{leaf_id}.json';path.write_text(json.dumps(trace))
        for seed in leaf['seeds']:
            for actor in manifest['actor_seeds']:
                row=dict(method_id='selected',config=config,leaf=leaf_id,seed=seed,policy_seed=actor,leaf_outcomes=leaf['outcomes'],valid=True,terminal_requirements_met=True,identity_audit={'valid':True},manifest_sha256=manifest['manifest_sha256'],protocol_sha256=protocol['protocol_sha256'],checker_sha256='a'*64,physical_instance_sha256=digest(trace['instance']),metrics=trace['metrics'])
                if seed==leaf['seeds'][0] and actor==7:row.update(trace_path=str(path),trace_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
                rows.append(row)
    evaluation=dict(manifest_sha256=manifest['manifest_sha256'],protocol_sha256=protocol['protocol_sha256'],source_hashes=manifest['source_hashes'],rows=rows)
    (folder/'manifest.json').write_text(json.dumps(manifest));(folder/'evaluation.json').write_text(json.dumps(evaluation));return evaluation,manifest


class FinalActivityTests(unittest.TestCase):
    def test_actual_arrival_vs_request_cutoff_and_unique_completions(self):
        r=summarize_trace(fixture());c=r['counts']
        self.assertEqual((c['production_operations_started'],c['production_operations_completed'],c['production_units_completed']),(4,4,5))
        self.assertEqual((c['rental_requests'],c['rental_tools_actually_delivered'],c['rental_tools_actually_used']),(2,1,1))
        self.assertEqual((c['agv_transport_commitments'],c['agv_transport_arrivals']),(3,2)) # Arrival at H counts.
        self.assertEqual((c['replacement_events'],c['replacement_units_actually_released']),(1,0))
        self.assertEqual((c['bridge_crossings'],c['agv_charge_minutes'],c['worker_walk_minutes']),(2,8,1))
        self.assertEqual((c['initial_bom_assembly_starts'],c['assembly_parent_consumption_events']),(1,3))
        self.assertEqual((c['tool_services_started'],c['tool_services_completed']),(1,0))

    def test_electrical_import_curtailment_is_not_export_and_corruption_visible(self):
        t=fixture();e=energy_activity(t)
        self.assertTrue(e['no_export_balance_soc_contact_checks_passed']);self.assertEqual(e['negative_grid_export_kwh'],0)
        self.assertAlmostEqual(e['ac_battery_charge_kwh'],10/60);self.assertAlmostEqual(e['ac_battery_discharge_kwh'],9/60)
        self.assertAlmostEqual(e['curtailed_solar_kwh'],4/60)
        t['energy'][0]['grid_kw']=-1;self.assertFalse(energy_activity(t)['no_export_balance_soc_contact_checks_passed'])
        t=fixture();t['energy'].pop();self.assertRaises(ValueError,energy_activity,t)

    def test_first_declared_tape_actor_every_leaf_and_no_population_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);evaluation,manifest=bundle(p);r=analyze(p/'evaluation.json','selected',12)
            self.assertTrue(r['selection_complete_and_verified']);self.assertEqual(len(r['records']),8)
            self.assertEqual({x['policy_seed'] for x in r['records']},{7});self.assertEqual({x['seed'] for x in r['records']},set(range(10000,10008)))
            self.assertEqual(r['context']['full_protocol_tapes'],16);self.assertIn('only8',r['aggregate_scope'])
            self.assertEqual(r['retained_subset_count_sums']['rental_requests'],16)

    def test_no_replacement_of_invalid_missing_or_corrupt_first_trace(self):
        for case in ('invalid','missing','tamper'):
            with tempfile.TemporaryDirectory() as tmp:
                p=Path(tmp);evaluation,manifest=bundle(p)
                if case=='invalid':evaluation['rows'][0]['valid']=False
                elif case=='missing':evaluation['rows'].pop(0)
                else:(p/'traces/leaf0.json').write_text('{}')
                (p/'evaluation.json').write_text(json.dumps(evaluation));r=analyze(p/'evaluation.json','selected',12)
                self.assertFalse(r['selection_complete_and_verified']);self.assertEqual(len(r['records']),8);self.assertIsNone(r['retained_subset_count_sums'])
                self.assertFalse(r['records'][0]['eligible_checked_activity']);self.assertEqual(r['records'][0]['seed'],10000)

    def test_first_declared_is_not_smallest_actor_or_environment_seed(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);evaluation,manifest=bundle(p);manifest['actor_seeds']=[13,7]
            protocol=manifest['protocol']['payload'];protocol['leaves'][0]['seeds'].reverse();protocol.pop('protocol_sha256')
            protocol['protocol_sha256']=hashlib.sha256(json.dumps(protocol,sort_keys=True).encode()).hexdigest()
            manifest.pop('manifest_sha256');manifest['manifest_sha256']=digest(manifest)
            evaluation.update(manifest_sha256=manifest['manifest_sha256'],protocol_sha256=protocol['protocol_sha256'])
            for row in evaluation['rows']:row.update(manifest_sha256=manifest['manifest_sha256'],protocol_sha256=protocol['protocol_sha256'])
            config,rows,context=selected_rows(evaluation,manifest,'selected',12)
            self.assertEqual(rows[0]['seed'],20000);self.assertEqual({r['policy_seed'] for r in rows},{13})

    def test_seals_checker_leaf_and_ambiguous_context_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);evaluation,manifest=bundle(p)
            for case in ('manifest','checker','leaf','context'):
                e=deepcopy(evaluation);m=deepcopy(manifest)
                if case=='manifest':m['actor_seeds']=[13,7]
                elif case=='checker':e['rows'][0]['checker_sha256']='b'*64
                elif case=='leaf':e['rows'][0]['leaf_outcomes']=['wrong']
                else:m['configs'].append(dict(orders=12,horizon=20,profile='full'));m.pop('manifest_sha256');m['manifest_sha256']=digest(m);e['manifest_sha256']=m['manifest_sha256']
                with self.assertRaises(ValueError):selected_rows(e,m,'selected',12)


if __name__=='__main__':unittest.main()
