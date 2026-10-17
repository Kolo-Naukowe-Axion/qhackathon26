import itertools
import random
import unittest

from stage2.column_blocks import conditional_master, conflict_graph, propose, search
from stage2.column_qubo import compile_columns
from stage2.trajectory_mixer import sample
from stage2.window_experiments import tiny_problem
from stage2.window_qubo import assignments


class ColumnBlockTests(unittest.TestCase):
    def model(self):
        p = tiny_problem()
        rows = {op['id']:assignments(p,op) for op in p['operations']}
        def row(name,start):
            return next(r for r in rows[name] if r['start']==start)
        columns = {'P/housing':[[row('a',2)],[row('a',0)]],
                   'P/assembly':[[row('b',4)],[row('b',2)]]}
        q = compile_columns(p,columns)
        initial = q.encode(columns['P/housing'][0]+columns['P/assembly'][0])
        return q,initial

    def test_all_mapped_energies_exact_and_incumbent_retained(self):
        q,initial = self.model()
        alternatives = {name:q.groups[name][1] for name in q.columns}
        local = conditional_master(q,initial,alternatives)
        mapped = []
        for bits in itertools.product((0,1),repeat=len(local.linear)):
            full = local.full_bits(bits)
            self.assertEqual(local.energy(bits),q.energy(full))
            mapped.append(full)
        self.assertIn(initial,mapped)
        row = sample(local,7,2,32,32,'qaoa_xy')
        self.assertLess(row['makespan_invariant_leakage'],1e-12)
        self.assertIn('gate rxx',row['qasm'])

    def test_resource_closure_and_exact_search_improve_valid_incumbent(self):
        q,initial = self.model()
        alternatives = propose(q,initial,random.Random(7),conflict_graph(q))
        self.assertTrue(alternatives)
        result = search(q,initial,'exact',7,8)
        self.assertTrue(result['decoded']['valid'])
        self.assertEqual(result['energy'],4)
        self.assertLess(result['energy'],result['initial_energy'])


if __name__=='__main__':
    unittest.main()
