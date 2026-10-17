import unittest
from copy import deepcopy
from unittest.mock import patch

from stage2.admission import AdmissionSet
from stage2.check import check_trace,check_paired_causality
from stage2.release_admission import ReleaseAwareFactory,ReleasedFamilyAdmissionSet,tasks,validate_tasks
from stage2.spec import build
from stage2.static_control import GuardedCompletionFactory
from stage2.recovery_routing import BASE_WEIGHTS


class ReleasedFamilyAdmissionTests(unittest.TestCase):
    def factory(self,enabled=True,orders=12,seed=0):
        return ReleaseAwareFactory(build(orders,seed=seed),BASE_WEIGHTS,
            release_aware_admission=enabled,maintenance_outage_guard=True,
            tool_policy={'mode':'hard'},recovery_policy={'enabled':True})

    def test_off_has_exact_frozen_physical_behavior(self):
        options=dict(maintenance_outage_guard=True,tool_policy={'mode':'hard'},recovery_policy={'enabled':True})
        expected=GuardedCompletionFactory(build(2,seed=0),BASE_WEIGHTS,**options).run()
        actual=self.factory(False,2).run()
        for k in ('operations','moves','worker_moves','events','energy','metrics','admission_history'):
            self.assertEqual(expected[k],actual[k],k)

    def test_only_released_head_and_existing_slots_survive_with_all_inventory(self):
        f=self.factory();original=f.orders;parts=set(f.parts)
        set.add(f.admitted,'P07') # Preserve even a manually installed future slot.
        f.admitted.update([])
        self.assertIn('P07',f.admitted)
        self.assertTrue({'P01','P05','P09'}.issubset(f.admitted))
        self.assertTrue(all(oid=='P07' or f.orders[oid]['release_tick']<=f.t for oid in f.admitted))
        self.assertIs(f.orders,original);self.assertEqual(set(f.parts),parts)

    def test_exception_restoration_and_deepcopy_backlink(self):
        f=self.factory();original=f.orders
        with patch.object(AdmissionSet,'update',side_effect=RuntimeError('injected')):
            with self.assertRaises(RuntimeError):f.admitted.update([])
        self.assertIs(f.orders,original)
        copied=deepcopy(f);self.assertIs(copied.admitted.factory,copied)
        self.assertIsInstance(copied.admitted,ReleasedFamilyAdmissionSet)
        copied.release_admission_audit['calls']=-1
        self.assertNotEqual(f.release_admission_audit['calls'],-1)

    def test_checked_causal_actual_traces(self):
        traces=[self.factory(True,2,s).run() for s in (0,1,16)]
        self.assertTrue(all(check_trace(t)['valid'] for t in traces))
        self.assertTrue(check_paired_causality(traces)['valid'])

    def test_exact_small_train_protocol_no_final_or_retuning(self):
        declared=tasks();validate_tasks(declared);self.assertEqual(len(declared),128)
        for mutation in ('final','guard','partial'):
            x=deepcopy(declared)
            if mutation=='final':x[0]['config']['seed']=10000
            elif mutation=='guard':x[0]['solver_options']['maintenance_outage_guard']=False
            else:x.pop()
            with self.assertRaises(ValueError):validate_tasks(x)


if __name__=='__main__':unittest.main()
