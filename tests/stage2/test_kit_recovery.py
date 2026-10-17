import unittest
from unittest.mock import patch

from stage2.check import check_trace,check_paired_causality
from stage2.kit_recovery import AdmissionRecoveryFactory,RecoveryFactory,repack_search,run
from stage2.kitting import KitToolingSpecialistFactory,run as kit_run
from stage2.spec import build


WEIGHTS=dict(wip_limit=8,mode='standard',due=.25,remaining=-4.,family=24.,setup=10,
    lease_calibration=True,selector='priority',policy_seed=0,tool_distance=0,
    qa_guard_threshold=4,worker_calendar=True,preposition=False,admission_rule='family')


def component(uid,order,recipe,location):
    return dict(id=uid,order_id=order,recipe=recipe,location=location,
        accepted=True,status='waiting',busy=False,moving=False)


class RepackSearchTests(unittest.TestCase):
    def fixture(self):
        parts=[]
        for station,orders in (('A1',('P02','P04')),('A2',('P08','P10'))):
            for order in orders:
                for recipe in ('housing','flange'):parts.append(component(order+'/'+recipe,order,recipe,station))
        parts.extend([component('P05/housing','P05','housing','QA1'),component('P05/flange','P05','flange','QA2')])
        return parts,dict(A1=6,A2=6),dict(A1=0,A2=0),[dict(order_id='P05',station='A1',unit_ids=['P05/housing','P05/flange'])]

    def test_three_real_moves_create_room_for_observed_two_and_future_third(self):
        parts,capacities,fixed,goals=self.fixture();result=repack_search(parts,capacities,fixed,goals)
        self.assertEqual(result['status'],'planned');self.assertEqual(result['depth'],3)
        self.assertEqual(result['awaits_unaccepted_components'],1)
        positions={p['id']:p['location'] for p in parts}
        for move in result['moves']:
            self.assertEqual(positions[move['unit_id']],move['source'])
            self.assertLess(sum(location==move['destination'] for location in positions.values()),capacities[move['destination']])
            positions[move['unit_id']]=move['destination']
        self.assertEqual(positions['P05/housing'],'A1');self.assertEqual(positions['P05/flange'],'A1')
        self.assertEqual(sum(location=='A1' for location in positions.values()),5)
        self.assertLessEqual(result['states_seen'],5000)

    def test_bounds_and_invalid_states_do_not_create_free_storage(self):
        parts,capacities,fixed,goals=self.fixture()
        self.assertEqual(repack_search(parts,capacities,fixed,goals,max_depth=2)['status'],'no_plan_within_bounds')
        self.assertEqual(repack_search(parts,capacities,fixed,goals,max_states=1)['states_seen'],1)
        with self.assertRaises(ValueError):repack_search(parts,dict(A1=3,A2=6),fixed,goals)
        parts[0]['busy']=True
        with self.assertRaises(ValueError):repack_search(parts,capacities,fixed,goals)


class PhysicalRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.traces={seed:run(build(12,seed=seed),WEIGHTS,tool_policy=dict(mode='hard'),
            admission=True,recovery_policy=dict(enabled=True)) for seed in (8,15,24,26)}

    def test_default_disabled_matches_frozen_kit_policy(self):
        instance=build(2,seed=0)
        expected=kit_run(instance,WEIGHTS,tool_policy=dict(mode='hard'),specialist=True,admission=True)
        actual=run(instance,WEIGHTS,tool_policy=dict(mode='hard'),admission=True)
        for key in ('operations','moves','worker_moves','events','energy','metrics'):self.assertEqual(expected[key],actual[key],key)

    def test_diagnosed_training_failures_are_rescued_with_full_checking_and_causality(self):
        for seed,trace in self.traces.items():
            report=check_trace(trace);self.assertTrue(report['valid'],(seed,report))
            self.assertTrue(any(r['status']=='assembled' for r in trace['algorithm_audit']['physical_kit_recovery']['history']))
            self.assertGreaterEqual(trace['metrics']['shipped'],12)
            if seed!=15:self.assertTrue(trace['metrics']['all_orders_fulfilled'])
        # Seed15 leaves one scrapped original pump and one unfinished urgent order: a rescue is not a universal
        # completion or deadlock-freedom claim, and that negative stays explicit.
        self.assertEqual(self.traces[15]['metrics']['shipped'],12)
        self.assertEqual(self.traces[15]['metrics']['orders'],14)
        report=check_paired_causality(list(self.traces.values()));self.assertTrue(report['valid'],report)

    def test_all_locked_assembly_arrivals_are_logged_physical_recovery_legs(self):
        for trace in self.traces.values():
            moves={move['id']:move for move in trace['moves']}
            for recovery in trace['algorithm_audit']['physical_kit_recovery']['history']:
                ids={leg['move_id'] for leg in recovery['executed_legs']};previous_end=-1
                for leg in recovery['executed_legs']:
                    move=moves[leg['move_id']]
                    self.assertEqual(move['unit_id'],leg['unit_id'])
                    self.assertEqual(move['from'],leg['source']);self.assertEqual(move['to'],leg['destination'])
                    self.assertGreaterEqual(move['start'],previous_end);previous_end=move['end']
                for move in trace['moves']:
                    if move.get('entity_type')=='part' and move['to'] in ('A1','A2') and recovery['started_tick']<=move['start']<recovery['finished_tick']:
                        self.assertIn(move['id'],ids)
                for op in trace['operations']:
                    if op['process']=='ASSEMBLY' and recovery['started_tick']<=op['start']<recovery['finished_tick']:
                        self.assertEqual(op['order_id'],recovery['order_id'])

    def test_locks_reject_unplanned_deliveries_and_timeout_restores_assignment(self):
        factory=AdmissionRecoveryFactory(build(2,seed=0),WEIGHTS,tool_policy=dict(mode='hard'),recovery_policy=dict(enabled=True,max_lock_minutes=1))
        factory.recovery_active=dict(order_id='P01',started_tick=0,had_original_target=False,
            original_target=None,plan=[],plan_index=0,in_flight=None,executed_legs=[])
        factory.assembly_target['P01']='A1'
        part=next(p for p in factory.parts.values() if p['order_id']=='P02')
        self.assertFalse(factory.move(part['id'],'A1'))
        with patch.object(KitToolingSpecialistFactory,'process',return_value='original') as underlying:
            self.assertFalse(factory.process(factory.machines['A1'],[part],preview=True))
            self.assertEqual(factory.process(factory.machines['T1'],[part],preview=True),'original')
            self.assertEqual(underlying.call_count,1)
        factory.t=1;factory._advance()
        self.assertIsNone(factory.recovery_active);self.assertNotIn('P01',factory.assembly_target)
        self.assertEqual(factory.recovery_history[-1]['status'],'aborted_timeout')


if __name__=='__main__':unittest.main()
