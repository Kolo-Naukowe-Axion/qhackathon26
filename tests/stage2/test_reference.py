"""Exact tiny reference: scope guards, physical replay, and analytic certificate."""
from copy import deepcopy
import importlib.util
import unittest

from stage2.reference import activities, full_attendance_lower_bound, make_tiny, solve, validate_scope
from stage2.check import check_trace


class ReferenceScopeTests(unittest.TestCase):
    def test_complete_bom_has_16_operations_and_19_required_deliveries(self):
        instance=make_tiny(15)
        operations,moves=activities(instance)
        self.assertEqual((len(operations),len(moves)),(16,19))
        self.assertEqual(len(instance["machines"]),7)
        self.assertEqual(sum(m["target_op"]=="P01/pump/1/op0" for m in moves),3)
        validate_scope(instance)

    def test_changed_binding_features_are_rejected_instead_of_relaxed(self):
        changes=(
            lambda x:x["tools"][0].update(life=1),
            lambda x:x["maintenance"].update(wear_limit=1),
            lambda x:x["workers"][0].update(breaks=[[10,20]]),
            lambda x:x["energy"].update(normal_grid_cap_kw=15),
            lambda x:x["quality"].update(wear_risk_coefficient=.1),
            lambda x:next(m for m in x["machines"] if m["process"]=="HEAT").update(batch_capacity=4),
            lambda x:x["agvs"][0].update(initial_soc=1),
            lambda x:x["modes"]["T"].update(turbo=deepcopy(x["modes"]["T"]["standard"])),
            lambda x:x["tools"][0].update(portable=True),
        )
        for change in changes:
            with self.subTest(change=change):
                instance=make_tiny();change(instance)
                with self.assertRaises(ValueError):validate_scope(instance)

    def test_independent_full_attendance_certificate(self):
        bound=full_attendance_lower_bound(make_tiny(15,automatic_attendance=False))
        self.assertEqual(bound["components"],dict(processing_ticks=975,first_material_delivery=4,
            last_component_to_assembly=8,assembly_to_final_inspection=8,final_shipping=8,earlier_welding_worker_round_trip=4))
        self.assertEqual(bound["lower_bound_ticks"],1007)
        with self.assertRaises(ValueError):full_attendance_lower_bound(make_tiny(15))


@unittest.skipUnless(importlib.util.find_spec("ortools"),"OR-Tools is installed in .venv-stage2")
class ExactCpReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.automatic=solve(make_tiny(15),deterministic_limit=10,wall_limit=30)
        cls.full=solve(make_tiny(15,automatic_attendance=False),deterministic_limit=10,wall_limit=30)

    def test_actual_manufacturing_durations_have_a_proved_optimum(self):
        result=self.automatic
        self.assertEqual(result["status"],"OPTIMAL")
        self.assertEqual(result["objective_ticks"],566)
        self.assertEqual(result["best_bound_ticks"],566)
        self.assertTrue(result["validation"]["valid"],result["validation"]["issues"])
        self.assertTrue(result["validation"]["all_orders_fulfilled"])
        self.assertIsNone(result["flagship_global_gap"])

    def test_full_attendance_witness_meets_independent_analytic_bound(self):
        result=self.full
        self.assertEqual(result["status"],"OPTIMAL")
        lower_bound=full_attendance_lower_bound(result["trace"]["instance"])["lower_bound_ticks"]
        self.assertEqual(result["objective_ticks"],lower_bound)
        self.assertTrue(result["validation"]["valid"],result["validation"]["issues"])

    def test_early_empty_reposition_is_legal_but_pickup_waits_for_completion(self):
        trace=self.automatic["trace"]
        operations=trace["operations"]
        prepositioned=[]
        for move in trace["moves"]:
            prior=[op for op in operations if op["unit_id"]==move["unit_id"] and op["machine_id"]==move["from"] and op["end"]<=move["pickup_tick"]]
            if prior:
                completion=max(op["end"] for op in prior)
                self.assertGreaterEqual(move["pickup_tick"],completion)
                if move["start"]<completion:prepositioned.append(move["id"])
        self.assertTrue(prepositioned,"This witness should exercise the broader physical dispatch domain")

    def test_cost_is_constant_across_the_two_complete_schedules(self):
        self.assertAlmostEqual(self.automatic["validation"]["metrics"]["total_cost"],67.6)
        self.assertAlmostEqual(self.full["validation"]["metrics"]["total_cost"],67.6)

    def test_corrupting_a_cp_witness_does_not_inherit_its_optimality_flag(self):
        trace=deepcopy(self.automatic["trace"])
        trace["moves"][0]["soc_after"]+=1
        self.assertFalse(check_trace(trace)["valid"])

    def test_short_horizon_reports_model_infeasibility_without_inventing_a_global_gap(self):
        result=solve(make_tiny(15,horizon=120),deterministic_limit=1,wall_limit=5)
        self.assertEqual(result["status"],"INFEASIBLE")
        self.assertFalse(result["optimal"])
        self.assertIsNone(result["objective_ticks"])
        self.assertIsNone(result["flagship_global_gap"])
        self.assertFalse(result["global_infeasibility_proven"])


if __name__=="__main__":unittest.main()
