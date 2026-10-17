import unittest
from copy import deepcopy

from stage2.check import check_trace,check_paired_causality
from stage2.quality_policy import AdmissionQualityFactory,run,diagnostic_tasks
from stage2.recovery_routing import BASE_WEIGHTS,run as original_run
from stage2.spec import build


class QualityPolicyTests(unittest.TestCase):
    def test_standard_is_physical_equivalent(self):
        instance=build(2,seed=0);options=dict(admission=True,tool_policy={'mode':'hard'},recovery_policy={'enabled':True})
        expected=original_run(instance,BASE_WEIGHTS,**options);actual=run(instance,BASE_WEIGHTS,**options)
        for key in ('operations','moves','worker_moves','events','energy','metrics'):self.assertEqual(expected[key],actual[key],key)

    def test_selective_uses_public_time_and_leaves_repair_standard(self):
        factory=AdmissionQualityFactory(build(2,seed=0),BASE_WEIGHTS,quality_policy={'mode':'selective'})
        machine=next(m for m in factory.machines.values() if m['process']=='ASSEMBLY')
        order=next(iter(factory.orders.values()))
        part=dict(id=order['id']+'/pump/1',order_id=order['id'],recipe='pump',family=order['family'],step=0,rework=[])
        factory.t=0;self.assertEqual(factory.assembly_mode(machine,part,'standard'),'standard')
        factory.t=int(factory.i['horizon_ticks']*.78);self.assertEqual(factory.assembly_mode(machine,part,'standard'),'careful')
        # Altering hidden tape identity does not alter this public decision.
        factory.i['seed']=999999;self.assertEqual(factory.assembly_mode(machine,part,'standard'),'careful')
        repair=deepcopy(part);repair['rework']=[dict(process='ASSEMBLY',base_ticks=45)]
        self.assertEqual(factory.assembly_mode(machine,repair,'standard'),'standard')
        factory.t=factory.i['horizon_ticks']-1;self.assertEqual(factory.assembly_mode(machine,part,'standard'),'standard')

    def test_actual_careful_duration_attendance_checker_and_causality(self):
        traces=[]
        for seed in (0,1,16):
            trace=run(build(2,seed=seed),BASE_WEIGHTS,admission=True,tool_policy={'mode':'hard'},
                recovery_policy={'enabled':True},quality_policy={'mode':'selective','start_fraction':0})
            self.assertTrue(check_trace(trace)['valid']);traces.append(trace)
            decisions=trace['algorithm_audit']['assembly_quality_policy']['decisions']
            self.assertTrue(any(d['chosen_mode']=='careful' for d in decisions))
            by_id={o['id']:o for o in trace['operations']}
            for decision in decisions:
                operation=by_id[decision['operation_id']]
                self.assertEqual(decision['chosen_mode'],operation['mode'])
                for interval in operation['worker_intervals']:
                    if 'assembly' in interval['skills']:self.assertEqual(interval['end'],operation['end'])
        self.assertTrue(check_paired_causality(traces)['valid'])

    def test_controls_training_domain_and_reject_unknown(self):
        tasks=diagnostic_tasks();self.assertEqual(len(tasks),27)
        self.assertEqual({t['solver_options']['quality_policy']['mode'] for t in tasks},{'standard','all-careful','selective'})
        self.assertTrue(all(t['config']['seed'] in range(32) for t in tasks))
        with self.assertRaises(ValueError):AdmissionQualityFactory(build(2),quality_policy={'mode':'oracle'})

    def test_original_careful_uses_revealed_order_type(self):
        factory=AdmissionQualityFactory(build(2,seed=0),BASE_WEIGHTS,quality_policy={'mode':'original-careful'})
        machine=next(m for m in factory.machines.values() if m['process']=='ASSEMBLY')
        order=next(iter(factory.orders.values()))
        part=dict(id=order['id']+'/pump/1',order_id=order['id'],recipe='pump',family=order['family'],step=0,rework=[])
        self.assertEqual(factory.assembly_mode(machine,part,'standard'),'careful')
        factory.orders[part['order_id']]['urgent']=True
        self.assertEqual(factory.assembly_mode(machine,part,'standard'),'standard')


if __name__=='__main__':unittest.main()
