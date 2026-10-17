import unittest

from stage2.manufacturing_cases import production_case
from stage2.realism_streaming import conflict_block, count_model, prune
from stage2.window_experiments import tiny_problem
from stage2.window_qubo import assignments, compile_qubo, conflict_reasons, digest
from stage2.window_reduction import arc_prune


class RealismStreamingTests(unittest.TestCase):
    def test_block_reason_multiplicity_matches_scalar_semantics(self):
        problem = production_case(2, 'heat-lease')
        for worker in problem['workers'].values():
            worker['available'] = [[0, problem['horizon']]]
        ops = {op['id']: op for op in problem['operations']}
        # Different families, resources, both precedence directions and assembly.
        names = ['P01/housing/step0', 'P01/housing/step1', 'P01/rotor/step0', 'P02/housing/step0', 'P01/pump/step0']
        for a in names:
            for b in names:
                if a == b:
                    continue
                ra = assignments(problem, ops[a])[::19]
                rb = assignments(problem, ops[b])[::17]
                block = conflict_block(problem, ops[a], ops[b], ra, rb)
                for i, row in enumerate(ra):
                    for j, other in enumerate(rb):
                        self.assertEqual(int(block[i, j]), len(conflict_reasons(problem, row, other, ops)))

    def test_streamed_counts_and_support_match_literal_compiler(self):
        problem = tiny_problem()
        domains = {op['id']: assignments(problem, op) for op in problem['operations']}
        reduced, _ = prune(problem, domains)
        scalar, _ = arc_prune(problem, domains)
        self.assertEqual(digest(reduced), digest(scalar))
        for support, rows in [(False, domains), (True, reduced)]:
            counts = count_model(problem, rows)
            model = compile_qubo(problem, support_pruning=support)
            self.assertEqual(counts['variables'], len(model.linear))
            self.assertEqual(counts['couplers'], len(model.quadratic))
            self.assertEqual(counts['penalty'], model.penalty)
            self.assertEqual(counts['coefficient_min'], min([*model.linear, *model.quadratic.values()]))
            self.assertEqual(counts['coefficient_max'], max([*model.linear, *model.quadratic.values()]))


if __name__ == '__main__':
    unittest.main()
