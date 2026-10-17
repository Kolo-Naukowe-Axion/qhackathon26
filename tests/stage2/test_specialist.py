import unittest
from copy import deepcopy

from stage2.advanced import run as advanced
from stage2.specialist import run,SpecialistFactory
from stage2.spec import build
from stage2.check import check_trace,check_paired_causality


class ScarceSkillTests(unittest.TestCase):
    def test_disabled_guard_preserves_advanced_dispatch(self):
        instance=build(3,seed=0);w=dict(wip_limit=3,lease_calibration=True)
        a=advanced(instance,w);b=run(instance,dict(w,qa_guard_threshold=0))
        for key in ('operations','moves','events','energy','metrics'):self.assertEqual(a[key],b[key],key)

    def test_temporary_skill_restriction_restores_immutable_eligibility(self):
        f=SpecialistFactory(build(2));before=deepcopy(f.i);skills={w:wk['skills'][:] for w,wk in f.workers.items()}
        f.weights.update(qa_guard_threshold=1);f.qa_backlog=lambda:4
        f.trace['operations'].append(dict(worker_ids=['W01'],worker_intervals=[
            dict(worker_id='W01',start=0,end=100)]))
        self.assertIsNone(f.available_worker('machining','A',5,False))
        self.assertEqual(f.i,before)
        self.assertEqual({w:wk['skills'] for w,wk in f.workers.items()},skills)
        self.assertEqual(f.available_worker('qa','A',45,False)['id'],'W04')

    def test_guard_traces_remain_physically_valid_and_causal(self):
        traces=[run(build(8,seed=s),dict(wip_limit=6,lease_calibration=True,
            worker_calendar=True,preposition=False,qa_guard_threshold=2)) for s in (0,1)]
        for trace in traces:self.assertTrue(check_trace(trace)['valid'])
        r=check_paired_causality(traces);self.assertTrue(r['valid'],r)


if __name__=='__main__':unittest.main()
