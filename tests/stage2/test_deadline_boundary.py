import itertools
import unittest

from stage2.deadline_boundary import ConditionedQuery, boundary_domains, graph_of
from stage2.deadline_qubo import compile_deadline
from stage2.window_experiments import tiny_problem


class DeadlineBoundaryTests(unittest.TestCase):
    def test_exact_substitution_all_bitstrings_and_full_checker(self):
        p=tiny_problem()
        q=compile_deadline(p, support_pruning=False)
        a=next(i for i in q.groups['a'] if q.variables[i]['start']==0)
        parent={'a':q.variables[a]}
        domains,fixed=boundary_domains(q,parent,{'b'},graph_of(q))
        local=ConditionedQuery(q,domains,fixed)
        for bits in itertools.product((0,1),repeat=len(local.linear)):
            self.assertEqual(local.energy(bits),q.energy(local.expand(bits)))
            self.assertEqual(local.decode(bits)['valid'],q.decode(local.expand(bits))['valid'])
        self.assertTrue(all(q.variables[i]['start']>=2 for i in domains['b']))

    def test_fixed_conflicts_are_filtered_not_ignored(self):
        p=tiny_problem()
        q=compile_deadline(p, support_pruning=False)
        a=next(i for i in q.groups['a'] if q.variables[i]['start']==2)
        domains,_=boundary_domains(q,{'a':q.variables[a]},{'b'},graph_of(q))
        self.assertEqual(domains['b'],[])


if __name__=='__main__':unittest.main()
