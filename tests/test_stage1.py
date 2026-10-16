import itertools
import json
import random
import unittest

from solver.stage1 import ROOT, build_qubo, decode, energy, encode_schedule, exact_reference, validate


def load(size):
    return json.loads((ROOT / "instances" / f"instance_{size}.json").read_text())


class FormulationTests(unittest.TestCase):
    def test_domain_wall_exact_2x2_and_3x3_penalty_bound(self):
        for size, horizon, count in (("2x2", 4, 4), ("3x3", 8, 30)):
            instance = load(size)
            model = build_qubo(instance, horizon, "domain-wall")
            self.assertEqual(len(model["variables"]), count)
            reference = exact_reference(instance)
            self.assertEqual(energy(model, encode_schedule(model, reference["schedule"])), 0)
            rng = random.Random(2026)
            samples = (itertools.product((0, 1), repeat=count) if count <= 4 else
                       ([rng.randrange(2) for _ in range(count)] for _ in range(2000)))
            for sample in samples:
                sample = list(sample)
                violations = sum((1 - sample[i]) * sample[j] for i, j in model["monotone_pairs"])
                self.assertGreaterEqual(energy(model, sample), violations)
                try:
                    schedule = decode(model, sample)
                except ValueError:
                    self.assertGreater(energy(model, sample), 0)
                    continue
                makespan = max((s["end"] for s in schedule), default=0)
                self.assertEqual(energy(model, sample) == 0, not validate(instance, schedule, makespan))

    def test_domain_wall_matches_onehot_on_valid_domains(self):
        instance = load("3x3")
        onehot, compact = [build_qubo(instance, 8, encoding) for encoding in ("onehot", "domain-wall")]
        groups = {}
        for v in onehot["variables"]:
            groups.setdefault((v["job"], v["machine"]), []).append(v)
        rng = random.Random(17)
        for _ in range(1000):
            choices = [rng.choice(group) for group in groups.values()]
            schedule = [dict(job=v["job"], machine=v["machine"], start=v["start"], end=v["start"] + v["duration"]) for v in choices]
            self.assertEqual(energy(onehot, encode_schedule(onehot, schedule)), energy(compact, encode_schedule(compact, schedule)))
            self.assertEqual(decode(compact, encode_schedule(compact, schedule)), schedule)

    def test_every_invalid_wall_on_small_models_obeys_proven_penalty_bound(self):
        # More than two starts per operation is essential: the official 2x2 at
        # H=4 has no internal walls and cannot expose negative-indicator bugs.
        instance = dict(problem="erp_scheduling", jobs=[
            dict(id=f"J{i}", operations=[dict(machine="T", duration=1), dict(machine="F", duration=1)])
            for i in range(2)])
        for horizon in (4, 5):
            model = build_qubo(instance, horizon, "domain-wall")
            for bits in itertools.product((0, 1), repeat=len(model["variables"])):
                violations = sum((1 - bits[i]) * bits[j] for i, j in model["monotone_pairs"])
                self.assertGreaterEqual(energy(model, bits), violations)
                if violations:
                    with self.assertRaises(ValueError):
                        decode(model, bits)
                else:
                    schedule = decode(model, bits)
                    makespan = max(s["end"] for s in schedule)
                    self.assertEqual(energy(model, bits) == 0, not validate(instance, schedule, makespan))

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
