import unittest
from copy import deepcopy

from stage2.engine import Factory
from stage2.admission import AdmissionFactory,run
from stage2.mpc import continuation,resume
from stage2.spec import build
from stage2.check import check_trace,check_paired_causality


class OrderAdmissionTests(unittest.TestCase):
    def test_due_adapter_preserves_original_dispatch(self):
        i=build(3,seed=0);a=Factory(i,dict(wip_limit=3)).run();b=run(i,dict(wip_limit=3))
        for key in ('operations','moves','events','energy','metrics'):self.assertEqual(a[key],b[key],key)

    def test_family_selection_keeps_existing_admitted_material(self):
        f=AdmissionFactory(build(12),dict(wip_limit=4,admission_rule='family'))
        f.t=360;f.admitted.update([])
        self.assertEqual(f.admitted,{'P01','P04','P07','P10'})
        f.weights['wip_limit']=1;f.admitted.update([])
        self.assertEqual(f.admitted,{'P01','P04','P07','P10'})
        g=deepcopy(f);self.assertIs(g.admitted.factory,g)
        self.assertIsNot(g.admitted.factory,f)

    def test_continuation_keeps_new_admission_rule(self):
        f=AdmissionFactory(build(3,seed=0),dict(wip_limit=3,admission_rule='priority',family=24))
        g=continuation(f,0,{},0,False);a=f.run();b=resume(g)
        for key in ('operations','moves','events','energy','metrics','admission_history'):self.assertEqual(a[key],b[key],key)

    def test_reordered_orders_remain_physical_and_prefix_causal(self):
        traces=[run(build(8,seed=s),dict(wip_limit=6,admission_rule='family',family=24,lease_calibration=True)) for s in (0,1)]
        for t in traces:self.assertTrue(check_trace(t)['valid'])
        r=check_paired_causality(traces);self.assertTrue(r['valid'],r)


if __name__=='__main__':unittest.main()
