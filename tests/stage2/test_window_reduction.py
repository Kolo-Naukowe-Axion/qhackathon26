import itertools
import unittest

from stage2.window_experiments import tiny_problem
from stage2.window_qubo import compile_qubo,check_plan
from stage2.window_search import constructive
from stage2.planning_quantum import neighborhood,energy_table
from stage2.planning_compressed import compress,expand,sample_compressed
from stage2.window_pump import pump_cell


class WindowReductionTests(unittest.TestCase):
    def test_support_pruning_preserves_every_feasible_schedule(self):
        p=tiny_problem();before=compile_qubo(p);after=compile_qubo(p,support_pruning=True)
        retained={tuple(sorted(row.items()))for row in after.variables if row['operation']!='@makespan'}
        feasible=0
        names=[name for name in before.groups if name!='@makespan']
        for choices in itertools.product(*(before.groups[n]for n in names)):
            plan=[before.variables[i]for i in choices]
            if check_plan(p,plan)['valid']:
                feasible+=1
                for row in plan:self.assertIn(tuple(sorted(row.items())),retained)
        self.assertGreater(feasible,0);self.assertLess(len(after.linear),len(before.linear))

    def test_affine_compression_preserves_every_reduced_energy(self):
        q=compile_qubo(tiny_problem());initial=constructive(q)
        free,fixed=neighborhood(q,initial['bits'],13,groups=2,alternatives=1)
        reduction=compress(q,free,fixed);table=energy_table(reduction['block'])
        self.assertLess(reduction['compressed_bits'],reduction['original_bits'])
        retained=set()
        for mask,energy in enumerate(table):
            values=[(mask>>j)&1 for j in range(reduction['compressed_bits'])];original=expand(reduction,values);retained.add(tuple(original))
            full=[fixed.get(i,0)for i in range(len(q.linear))]
            for i,v in zip(free,original):full[i]=v
            self.assertEqual(int(energy),q.energy(full))
        for original in itertools.product((0,1),repeat=len(free)):
            full=[fixed.get(i,0)for i in range(len(q.linear))]
            for i,v in zip(free,original):full[i]=v
            if q.decode(full)['valid']:self.assertIn(tuple(original),retained)

    def test_compressed_qaoa_returns_sample_with_full_energy(self):
        q=compile_qubo(tiny_problem());initial=constructive(q);free,fixed=neighborhood(q,initial['bits'],3,groups=2,alternatives=1)
        row=sample_compressed(q,free,fixed,seed=7,shots=64,evaluations=16)
        self.assertEqual(row['energy'],q.energy(row['bits']));self.assertEqual(sum(row['observed_counts'].values()),64)
        self.assertIn(f'qreg q[{row["free_bits"]}]',row['qasm'])

    def test_complete_pump_bom_has_three_parent_assembly(self):
        p=pump_cell(2,1440,60);self.assertEqual(len(p['operations']),32)
        assembly=[op for op in p['operations']if '/pump/step0'in op['id']]
        self.assertEqual([len(o['predecessors'])for o in assembly],[3,3])
        self.assertEqual(sum(not any(o['id']in x['predecessors']for x in p['operations'])for o in p['operations']),2)


if __name__=='__main__':unittest.main()
