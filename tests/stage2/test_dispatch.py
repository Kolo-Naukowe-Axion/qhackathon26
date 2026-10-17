import itertools
import unittest

from stage2.qubo import build_qubo,select


class CompactCapacityTests(unittest.TestCase):
    def test_gcd_scaling_is_lossless_including_nonmultiple_capacity(self):
        candidates=[dict(id="slow",reward=4,resources={"power":60}),dict(id="fast",reward=6,resources={"power":90})]
        q=build_qubo(candidates,[],{"power":100})
        self.assertEqual(q.resource_scales["power"],30)
        self.assertLessEqual(q.size,5)
        for bits in itertools.product((0,1),repeat=2):
            chosen=[i for i,b in enumerate(bits) if b]
            self.assertEqual(q.feasible(chosen),sum(candidates[i]["resources"]["power"] for i in chosen)<=100)
            if q.feasible(chosen):
                self.assertAlmostEqual(q.energy(q.encode(chosen)),-sum(candidates[i]["reward"] for i in chosen))

    def test_all_samplers_return_legal_observed_or_disclosed_decisions(self):
        cs=[dict(id=f"C{i}",reward=r,resources={}) for i,r in enumerate([10,6,6])]
        conflicts=[("C0","C1"),("C0","C2")]
        q=build_qubo(cs,conflicts)
        self.assertEqual(select(cs,conflicts,method="exact")["reward"],12)
        for method in ("greedy","sa","qaoa","uniform","exact_random_tie"):
            result=select(cs,iter(conflicts),method=method,seed=1)
            self.assertTrue(q.feasible([int(x[1:]) for x in result["selected"]]))
            self.assertTrue(result["feasible"])


if __name__=="__main__":unittest.main()
