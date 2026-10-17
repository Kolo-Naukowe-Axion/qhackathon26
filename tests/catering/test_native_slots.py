import json
from pathlib import Path
import unittest
from unittest.mock import patch

from catering.classical_cases import cases
from catering.domain import fixture, snapshot, make_plan
from catering.native_slots import solve_native
from catering.decode import decode


class NativeSlotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = {c["case_id"]:c for c in cases(include_scale=False)}
        cls.results = {name:solve_native(c["instance"],c["snapshot"],dict(wall_time_limit_s=3))
                       for name,c in cls.cases.items()}

    def test_all_small_cases_prove_optimum_and_pass_checker(self):
        for name,r in self.results.items():
            with self.subTest(case=name):
                self.assertEqual(r["reference_status"],"OPTIMAL")
                self.assertTrue(r["check"]["valid"])
                self.assertEqual(r["objective"],r["objective_bound"])

    def test_direct_model_agrees_with_frozen_complete_domains(self):
        root = Path(__file__).resolve().parents[2]/"output/catering-foundation-v2"
        for scenario in ("S0","S1","S2","S3"):
            reference = json.loads((root/scenario/"reference-complete.json").read_text())
            bundle = json.loads((root/scenario/"complete-qubo.json").read_text())
            checked = decode(bundle,reference["samples"][0]["bits"])
            self.assertTrue(checked["valid"])
            self.assertEqual(self.results["core-"+scenario]["check"]["metrics"],checked["check"]["metrics"])
        self.assertEqual(self.results["core-S2"]["check"]["metrics"],dict(U=1,W=0,B=0,R=1))
        self.assertEqual(self.results["core-S3"]["check"]["metrics"],dict(U=1,W=0,B=1,R=2))

    def test_causal_cases_have_expected_tradeoffs(self):
        expected = {"freshness-split":dict(U=0,W=0,B=2,R=2),
                    "unavoidable-surplus":dict(U=0,W=1,B=1,R=1),
                    "unreachable-handover":dict(U=1,W=0,B=0,R=0),
                    "priority-bottleneck":dict(U=1,W=0,B=1,R=1)}
        for name,metrics in expected.items():
            self.assertEqual(self.results[name]["check"]["metrics"],metrics)
        plan = self.results["priority-bottleneck"]["plan"]
        self.assertEqual([a["demand_group"] for a in plan["allocations"]],["B/priority-5"])

    def test_sharing_policy_has_a_measurable_batch_benefit(self):
        case = self.cases["core-S1"]
        separate = solve_native(case["instance"],case["snapshot"],dict(wall_time_limit_s=3),dict(allow_sharing=False))
        self.assertEqual(separate["reference_status"],"OPTIMAL")
        self.assertEqual(separate["check"]["metrics"],dict(U=0,W=0,B=2,R=1))
        self.assertEqual(self.results["core-S1"]["check"]["metrics"],dict(U=0,W=0,B=1,R=2))

    def test_complete_committed_demand_needs_no_new_slots(self):
        p = fixture();p["demand_groups"] = p["demand_groups"][:1]
        p["urgent_groups"] = [];p["previous_unstarted"] = []
        r = solve_native(p,snapshot(p,"S0"))
        self.assertEqual(r["model_size"]["batch_slots"],0)
        self.assertEqual(r["check"]["metrics"],dict(U=0,W=0,B=0,R=0))
        self.assertEqual(r["plan"],make_plan(p,p["fixed_batches"]))

    def test_raw_solver_does_not_call_option_generator_or_compiler(self):
        p = fixture()
        with patch("catering.options.enumerate_options",side_effect=AssertionError("No enumeration")), \
             patch("catering.qubo.compile_qubo",side_effect=AssertionError("No compilation")):
            r = solve_native(p,snapshot(p,"S1"))
        self.assertEqual(r["reference_status"],"OPTIMAL")
        self.assertFalse(r["program_enumeration"])

    def test_invalid_budget_and_committed_boundary_are_rejected(self):
        p = fixture();s = snapshot(p,"S0")
        with self.assertRaises(ValueError):solve_native(p,s,dict(wall_time_limit_s=0))
        s["fixed_batches"][0]["cook_start"] = 0
        with self.assertRaises(ValueError):solve_native(p,s)


if __name__ == "__main__":
    unittest.main()
