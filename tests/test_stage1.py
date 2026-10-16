import itertools
import json
import random
import unittest

from solver.stage1 import ROOT, build_qubo, decode, energy, exact_reference, validate


def load(size):
    return json.loads((ROOT / "instances" / f"instance_{size}.json").read_text())


class FormulationTests(unittest.TestCase):
    def test_3x3_conflict_penalties_match_direct_interval_checker(self):
        instance = load("3x3")
        model = build_qubo(instance, 8)
        groups = {}
        for i, variable in enumerate(model["variables"]):
            groups.setdefault((variable["job"], variable["machine"]), []).append(i)
        rng = random.Random(2026)
        for _ in range(1000):
            selected = {rng.choice(group) for group in groups.values()}
            sample = [int(i in selected) for i in range(len(model["variables"]))]
            schedule = decode(model, sample)
            errors = validate(instance, schedule, max(s["end"] for s in schedule))
            self.assertEqual(energy(model, sample), len(errors))

    def test_all_2x2_bitstrings_match_independent_feasibility(self):
        instance = load("2x2")
        for horizon in (3, 4):
            model = build_qubo(instance, horizon)
            feasible = 0
            for sample in itertools.product((0, 1), repeat=len(model["variables"])):
                schedule = decode(model, sample)
                makespan = max((s["end"] for s in schedule), default=0)
                valid = not validate(instance, schedule, makespan) and makespan <= horizon
                self.assertEqual(energy(model, sample) == 0, valid)
                self.assertGreaterEqual(energy(model, sample), 0)
                feasible += valid
            self.assertEqual(feasible > 0, horizon == 4)

    def test_exact_references_and_3x3_roundtrip(self):
        for size, optimum, combinations in (("2x2", 4, 4), ("3x3", 8, 216)):
            instance = load(size)
            reference = exact_reference(instance)
            self.assertEqual(reference["makespan"], optimum)
            self.assertEqual(reference["order_combinations"], combinations)
            self.assertEqual(validate(instance, reference["schedule"], optimum), [])
            model = build_qubo(instance, optimum)
            selected = {(s["job"], s["machine"], s["start"]) for s in reference["schedule"]}
            sample = [int((v["job"], v["machine"], v["start"]) in selected) for v in model["variables"]]
            self.assertEqual(energy(model, sample), 0)
            self.assertEqual(validate(instance, decode(model, sample), optimum), [])
        self.assertEqual(len(model["variables"]), 39)

    def test_checker_rejects_corrupt_schedules(self):
        instance = load("3x3")
        schedule = exact_reference(instance)["schedule"]
        self.assertTrue(validate(instance, schedule[:-1], 8))
        self.assertTrue(validate(instance, schedule + [schedule[0]], 8))
        self.assertTrue(validate(instance, schedule, 9))
        conflict = [dict(s, start=0, end=s["end"] - s["start"]) for s in schedule]
        errors = validate(instance, conflict, max(s["end"] for s in conflict))
        self.assertIn("machine overlap", errors)
        self.assertIn("precedence violation", errors)
        bad_duration = [dict(s) for s in schedule]
        bad_duration[0]["end"] += 1
        self.assertIn("invalid start or duration", validate(instance, bad_duration, 8))

    def test_rejects_invalid_samples_and_horizons(self):
        instance = load("2x2")
        with self.assertRaises(ValueError):
            build_qubo(instance, 0)
        model = build_qubo(instance, 4)
        for sample in ([], [2] * 8):
            with self.assertRaises(ValueError):
                decode(model, sample)


if __name__ == "__main__":
    unittest.main()
