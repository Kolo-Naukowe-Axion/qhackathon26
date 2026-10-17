import unittest
from stage2.window_experiments import tiny_problem
from stage2.window_qubo import check_plan
from stage2.column_parents import generate


class ColumnParentTests(unittest.TestCase):
    def test_raw_parent_generator_needs_no_global_qubo_or_cp_teacher(self):
        p=tiny_problem();result=generate(p,attempts=32,wanted=3,seed=7,seconds=3)
        self.assertGreaterEqual(len(result['parents']),2);self.assertFalse(result['cp_teacher_used'])
        self.assertEqual(result['raw_assignment_candidates'],6)
        for plan in result['parents']:self.assertTrue(check_plan(p,plan)['valid'])
        self.assertEqual(sum(r.get('distinct',False)for r in result['history']),len(result['parents']))


if __name__=='__main__':unittest.main()
