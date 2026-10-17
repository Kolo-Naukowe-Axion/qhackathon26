import unittest

from stage2.check import check_trace,check_paired_causality
from stage2.kit_recovery import run as recovery_run
from stage2.recovery_routing import AdmissionRecoveryRoutingFactory,BASE_WEIGHTS,diagnostic_tasks,run,terminal_diagnosis
from stage2.spec import build


class RecoveryRoutingCompositionTests(unittest.TestCase):
    def test_default_scope_preserves_frozen_recovery_physics(self):
        instance=build(2,seed=0);weights=dict(BASE_WEIGHTS,wip_limit=3)
        options=dict(tool_policy={'mode':'hard'},admission=True,recovery_policy={'enabled':True})
        expected=recovery_run(instance,weights,**options);actual=run(instance,weights,**options)
        for key in ('operations','moves','worker_moves','events','energy','metrics'):self.assertEqual(expected[key],actual[key],key)

    def test_causal_composition_and_terminal_diagnosis_keep_physics(self):
        traces=[]
        for seed in (0,1,16):
            factory=AdmissionRecoveryRoutingFactory(build(2,seed=seed),dict(BASE_WEIGHTS,wip_limit=3),
                tool_policy={'mode':'hard'},recovery_policy={'enabled':True},
                routing_policy={'eta_processes':['QA'],'free_buffer_processes':[]})
            trace=factory.run();self.assertTrue(check_trace(trace)['valid']);traces.append(trace)
            diagnosis=terminal_diagnosis(factory)
            self.assertEqual(len(diagnosis['unfinished_orders']),trace['metrics']['orders']-trace['metrics']['shipped'])
            for worker in diagnosis['qa_qualified_workers']:
                self.assertLessEqual(worker['qa_attendance_minutes'],worker['occupied_all_skills_and_walk_minutes'])
                self.assertLessEqual(worker['occupied_all_skills_and_walk_minutes'],worker['calendar_available_minutes'])
        self.assertTrue(check_paired_causality(traces)['valid'])

    def test_diagnostic_domain_is_bounded_and_training_only(self):
        tasks=diagnostic_tasks();self.assertEqual(len(tasks),96)
        self.assertTrue(all(t['config']['seed'] in range(32) for t in tasks))
        self.assertEqual({t['weights']['wip_limit'] for t in tasks},{4,6,8})
        self.assertEqual({t['weights']['qa_guard_threshold'] for t in tasks},{0,4})
        self.assertTrue(all(t['weights']['admission_rule']=='family' for t in tasks))


if __name__=='__main__':unittest.main()
