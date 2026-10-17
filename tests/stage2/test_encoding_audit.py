"""Independent counting and certificate-falsification checks."""
from copy import deepcopy
import unittest

from stage2.encoding_audit import audit
from stage2.engine import run
from stage2.spec import build


class EncodingScopeTests(unittest.TestCase):
    def test_machine_modes_certification_and_closed_start_boundary(self):
        instance=dict(horizon_ticks=10,tick_minutes=1,
            orders=[dict(id='regular',release_tick=2),dict(id='precision',release_tick=2,precision_required=True)],
            machines=[dict(id='Tfast',process='T',duration_factor=[1,2]),dict(id='irrelevant',process='F',duration_factor=[1,1])],
            modes={'T':{'standard':{'duration_factor':[1,1]},'eco':{'duration_factor':[2,1]}}},
            certification_modes={'precision':{'T':['eco']}},
            recipes={kind:[dict(process='T',base_ticks=3)]for kind in ('housing','rotor','flange','pump')})
        result=audit(instance)
        # Each regular operation: duration2 starts2..8 (7), duration3 starts2..7 (6).
        # Each precision operation permits eco only (6); four operations/order.
        self.assertEqual(result['nominal_known_operations'],8)
        self.assertEqual(result['naive_known_nominal_start_bits'],4*(7+6)+4*6)
        self.assertFalse(result['naive_is_complete_formulation'])
        self.assertIsNone(result['global_lexicographic_optimality_gap'])
        instance['horizon_ticks']=3
        self.assertEqual(audit(instance)['naive_known_nominal_start_bits'],0)

    def test_current_factory_count_is_only_the_declared_nominal_start_family(self):
        instance=build(8,seed=3)
        self.assertEqual(audit(instance)['nominal_known_operations'],128)
        # Independently enumerate each actual integer start with exact arithmetic.
        count=0
        for order in instance['orders']:
            for recipe in instance['recipes'].values():
                for step in recipe:
                    process=step['process'];modes=instance['modes'][process]
                    names=instance['certification_modes']['precision'].get(process,modes) if order['precision_required'] else modes
                    for machine in instance['machines']:
                        if machine['process']!=process:continue
                        for name in names:
                            a,b=modes[name]['duration_factor'];c,d=machine['duration_factor']
                            duration=(step['base_ticks']*a*c+b*d-1)//(b*d)
                            count+=sum(start+duration<=instance['horizon_ticks']for start in range(order['release_tick'],instance['horizon_ticks']+1))
        self.assertEqual(audit(instance)['naive_known_nominal_start_bits'],count)

    def test_forged_fulfillment_and_stored_validation_cannot_create_certificate(self):
        trace=run(build(2,horizon=300,seed=3),dict(wip_limit=3,lease_calibration=True))
        self.assertLess(trace['metrics']['shipped'],trace['metrics']['orders'])
        trace['metrics'].update(all_orders_fulfilled=True,shipped=trace['metrics']['orders'])
        trace['validation']={'valid':True,'status':'passed','terminal_requirements_met':True}
        certificate=audit(trace['instance'],trace)['fulfillment_primary_certificate']
        self.assertFalse(certificate['primary_optimal_on_this_realization'])
        self.assertGreater(certificate['unfulfilled'],0)

    def test_invalid_physics_defeats_a_real_complete_trace_certificate(self):
        trace=run(build(1,seed=3),dict(wip_limit=3,lease_calibration=True))
        self.assertTrue(trace['metrics']['all_orders_fulfilled'])
        self.assertTrue(audit(trace['instance'],trace)['fulfillment_primary_certificate']['primary_optimal_on_this_realization'])
        broken=deepcopy(trace)
        broken['energy'][0]['grid_kw']=broken['energy'][0]['cap_kw']+100
        broken['validation']={'valid':True,'status':'passed'}
        certificate=audit(broken['instance'],broken)['fulfillment_primary_certificate']
        self.assertFalse(certificate['independently_checked_valid'])
        self.assertFalse(certificate['primary_optimal_on_this_realization'])

    def test_classical_fallback_size_is_not_a_simulated_quantum_size(self):
        trace=run(build(1,horizon=60,seed=3))
        def evidence(bits,quantum,fallback=None):
            return dict(committed=['C0'],result=dict(selected=['C0'],quantum_algorithm_simulated=quantum,
                fallback_reason=fallback,qubo=dict(variables=bits,core_variables=3,slack_variables=bits-3,couplers=bits)))
        # Synthetic metadata probes accounting, not a measured performance run.
        trace['qubo_decisions']=[evidence(5,True),evidence(11,False,'exceeds physical device bit budget')]
        measured=audit(trace['instance'],trace)['measured_local']
        self.assertEqual(measured['max_total_bits'],11)
        self.assertEqual(measured['max_simulated_quantum_total_bits'],5)
        self.assertEqual(measured['genuine_qaoa_simulated_calls'],1)
        self.assertEqual(measured['classical_fallback_calls'],1)


if __name__=='__main__':unittest.main()
