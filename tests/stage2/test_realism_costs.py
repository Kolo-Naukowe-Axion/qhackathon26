"""Independent arithmetic checks for declared variable-family representations."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from stage2.engine import Factory
from stage2.realism_costs import audit,counter_bits,endpoint_pairs,operation_slots,conflict_families,local_ablation,wear_grid,main
from stage2.qubo import build_qubo
from stage2.spec import build


def families(result):return {row['name']:row for row in result['variable_families']}


class RealismCostTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.trace=Factory(build(3,horizon=2880,seed=0),dict(wip_limit=3,mode='standard',lease_calibration=True,selector='exact')).run()

    def test_counter_width_includes_upper_endpoint_and_rejects_invalid_limits(self):
        self.assertEqual([counter_bits(limit) for limit in (0,1,2,3,4,600,1050,2400)], [0,1,2,2,3,10,11,12])
        for limit in (-1,1.2,True):
            with self.assertRaises(ValueError):counter_bits(limit)

    def test_full_dimensions_and_no_fake_global_total(self):
        result=audit(build(24));f=families(result)
        self.assertEqual(result['dimensions'],dict(machines=15,workers=10,halls=2,agvs=4,nodes=24,potential_tools=6,families=3))
        self.assertEqual(f['worker_hall_indicators']['bits'],10*2*5761)
        self.assertEqual(f['tool_node_indicators']['bits'],6*24*5761)
        self.assertEqual(f['tool_remaining_life_counters']['bits'],6*10*5761)
        self.assertEqual(f['machine_wear_counters']['bits'],15*13*5761)
        self.assertEqual(f['raw_stock_counters']['bits'],3*6*5761)
        self.assertEqual(f['stationary_battery_actions']['bits'],3*5760)
        self.assertEqual(f['stationary_battery_soc_counters']['bits'],12*5761)
        self.assertIsNone(result['additive_global_total']);self.assertIsNone(result['lossless_reduction_ratio'])
        self.assertFalse(result['complete_global_formulation'])

    def test_nominal_routes_have79_endpoint_pairs_and_closed_start_boundaries(self):
        instance=build(1,horizon=12);pairs=endpoint_pairs(instance)
        self.assertEqual(len(pairs),79)
        self.assertEqual({recipe:sum(pair['recipe']==recipe for pair in pairs) for recipe in ('housing','rotor','flange','pump')},
                         dict(housing=26,rotor=26,flange=21,pump=6))
        self.assertEqual(sum(pair['duration_ticks']==4 for pair in pairs),42)
        self.assertEqual(sum(pair['duration_ticks']==8 for pair in pairs),37)
        self.assertEqual(families(audit(instance))['nominal_loaded_pickup_choices']['bits'],4*(42*9+37*5))
        instance['horizon_ticks']=3
        self.assertEqual(families(audit(instance))['nominal_loaded_pickup_choices']['bits'],0)

    def test_transport_count_changes_with_real_bridge_and_release_windows(self):
        instance=build(1,horizon=12);before=families(audit(instance))['nominal_loaded_pickup_choices']['bits']
        for edge in instance['graph_edges']:
            if {edge['a'],edge['b']}=={'HUB_A','HUB_B'}:edge['ticks']+=3
        self.assertEqual(before-families(audit(instance))['nominal_loaded_pickup_choices']['bits'],4*37*3)
        instance['orders'][0]['release_tick']=4
        self.assertEqual(families(audit(instance))['nominal_loaded_pickup_choices']['bits'],4*42*5)

    def test_quality_envelope44_slots_reduces_to_nominal_when_contingencies_disabled(self):
        instance=build(24);result=audit(instance)
        self.assertEqual(len(operation_slots(instance)),44)
        self.assertEqual(result['quality_slots']['bounded_known_total'],1056)
        self.assertEqual(result['quality_slots']['bounded_including_maximum_urgent'],1144)
        instance['quality'].update(max_repairs_per_component_attempt=0,max_replacements_per_original_component=0)
        result=audit(instance);f=families(result)
        self.assertEqual(len(operation_slots(instance)),16)
        self.assertEqual(f['bounded_quality_production_start_envelope']['bits'],f['nominal_manufacturing_starts']['bits'])

    def test_changed_counter_capacity_and_lease_are_not_silently_ignored(self):
        instance=build(1);before=families(audit(instance))
        instance['tools'][0]['life']=1
        after=families(audit(instance))
        self.assertEqual(before['tool_remaining_life_counters']['bits']-after['tool_remaining_life_counters']['bits'],9*5761)
        self.assertEqual(before['rental_request_time_indicators']['bits'],5760)
        self.assertEqual(before['rental_arrival_indicators_derived']['bits'],5281)
        instance['lease_options']=[]
        self.assertEqual(families(audit(instance))['rental_request_time_indicators']['bits'],0)
        instance['lease_options']=build(1)['lease_options'];instance['lease_options'][0]['lead_ticks']=0
        self.assertEqual(families(audit(instance))['rental_arrival_indicators_derived']['bits'],5760)

    def test_fractional_eco_wear_requires_scaled_counter_not_integer_truncation(self):
        instance=build(24);grid=wear_grid(instance)
        self.assertEqual((grid['scale'],grid['scaled_limit'],grid['bits_per_counter']),(5,5250,13))
        # Housing mill base90, eco3/2, slow F3 factor5/4: ceil168.75=169.
        machine=next(machine for machine in instance['machines'] if machine['id']=='F3')
        mode=instance['modes']['F']['eco']
        a,b=mode['duration_factor'];c,d=machine['duration_factor']
        duration=(90*a*c+b*d-1)//(b*d)
        self.assertEqual(duration,169)
        self.assertEqual(duration*grid['mode_scaled_increments']['F']['eco'],507)
        self.assertAlmostEqual(507/grid['scale'],101.4)
        # A newly declared fractional initial state must also refine the grid.
        instance['machines'][0]['initial_wear']=.1
        self.assertEqual(wear_grid(instance)['scale'],10)

    def test_interval_aware_worker_family_preserves_disjoint_attendance(self):
        offers=[dict(machine_id='T1',unit_ids=['p'],tool_ids=[],worker_ids=['w'],worker_calendar_aware=True,
                     worker_intervals=[dict(worker_id='w',start=0,end=5)]),
                dict(machine_id='T2',unit_ids=['q'],tool_ids=[],worker_ids=['w'],worker_calendar_aware=True,
                     worker_intervals=[dict(worker_id='w',start=5,end=10)])]
        candidates=[dict(id='C0'),dict(id='C1')]
        self.assertFalse(conflict_families(offers,candidates)['worker'])
        offers[1]['worker_intervals'][0]['start']=4
        self.assertEqual(conflict_families(offers,candidates)['worker'],{('C0','C1')})
        offers[1]['worker_intervals'][0]['start']=5;offers[0]['worker_calendar_aware']=False
        self.assertEqual(conflict_families(offers,candidates)['worker'],{('C0','C1')})

    def test_conflict_couplers_overlap_and_power_can_add_slack(self):
        candidates=[dict(id=f'C{i}',reward=1,resources={'p':3}) for i in range(3)]
        power=build_qubo(candidates,capacities={'p':6})
        self.assertEqual((power.summary()['core_variables'],power.summary()['slack_variables']),(3,2))
        self.assertEqual(power.summary()['variables'],5)
        # Two physical reasons for one prohibited pair still need one coupler.
        worker={('C0','C1')};machine={('C0','C1')}
        pairwise=build_qubo([dict(c,resources={}) for c in candidates],worker|machine,{})
        self.assertEqual(pairwise.summary()['couplers'],1);self.assertEqual(pairwise.summary()['slack_variables'],0)

    def test_actual_checked_trace_reconstruction_and_ablation_are_nonmutating(self):
        original=deepcopy(self.trace);result=local_ablation(self.trace)
        self.assertTrue(result['valid']);self.assertEqual(self.trace,original)
        self.assertGreater(len(result['rows']),0)
        for row in result['rows']:
            self.assertEqual(row['ablations']['reward_only']['slack_variables'],0)
            self.assertEqual(row['ablations']['reward_only']['couplers'],0)
            self.assertEqual(row['ablations']['all_conflicts']['slack_variables'],0)
            self.assertEqual(row['ablations']['full']['core_variables'],row['core_candidates'])

    def test_corrupt_offer_conflict_correspondence_cannot_be_reported_as_measured(self):
        trace=deepcopy(self.trace)
        decision=next(decision for decision in trace['qubo_decisions'] if decision['conflicts'])
        decision['conflicts'].pop()
        with self.assertRaisesRegex(ValueError,'conflict reconstruction'):local_ablation(trace)

    def test_cli_retains_complete_instance_blueprint_and_matching_source_snapshot(self):
        with tempfile.TemporaryDirectory() as temporary:
            output=Path(temporary)/'evidence'
            self.assertEqual(main(['--orders','1','--output',str(output)]),0)
            manifest=json.loads((output/'manifest.json').read_text())
            instance=json.loads((output/'instance-n1.json').read_text())
            report=json.loads((output/'families-n1.json').read_text())
            self.assertTrue(manifest['source_stable'])
            self.assertEqual(report['instance_sha256'],hashlib.sha256(json.dumps(instance,sort_keys=True).encode()).hexdigest())
            for name,digest in manifest['source_before'].items():
                self.assertEqual(digest,hashlib.sha256((output/'sources'/name).read_bytes()).hexdigest())
            self.assertEqual(manifest['blueprint_sha256_before'],hashlib.sha256((output/'sources/metaltech_pressure.json').read_bytes()).hexdigest())


if __name__=='__main__':unittest.main()
