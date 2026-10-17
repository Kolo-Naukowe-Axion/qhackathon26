"""Exhaustive encoding checks and adversarial saved-evidence checks."""
import itertools
import json
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch

from solver.sequence import build_sequence_qubo, schedule_order
from solver.stage1 import ROOT, decode, energy, exact_reference, validate


class SequenceTests(unittest.TestCase):
    def test_every_bitstring_and_every_order_including_unseen_durations(self):
        rng = random.Random(763)
        instances = [json.loads((ROOT / "instances" / f"instance_{size}.json").read_text())
                     for size in ("2x2", "3x3")]
        instances += [dict(problem="erp_scheduling", jobs=[dict(id=f"J{j}", operations=[
            dict(machine=m, duration=rng.randrange(1, 12)) for m in ("T", "F", "S")])
            for j in range(n)]) for n in (2, 3) for _ in range(20)]
        for instance in instances:
            model = build_sequence_qubo(instance)
            seen, invalid = set(), []
            feasible_energies = []
            for bits in itertools.product((0, 1), repeat=len(model["variables"])):
                try:
                    schedule = decode(model, bits)
                except ValueError:
                    invalid.append(energy(model, bits))
                    continue
                makespan = max(row["end"] for row in schedule)
                self.assertEqual(validate(instance, schedule, makespan), [])
                self.assertEqual(energy(model, bits), makespan)
                route = instance["jobs"][0]["operations"][0]["machine"]
                seen.add(tuple(row["job"] for row in schedule if row["machine"] == route))
                feasible_energies.append(makespan)
            self.assertEqual(seen, set(itertools.permutations(job["id"] for job in instance["jobs"])))
            self.assertTrue(all(cost > max(feasible_energies) for cost in invalid))
            self.assertEqual(len(invalid), 2 if len(instance["jobs"]) == 3 else 0)

    def test_official_models_match_full_machine_order_reference_without_reference_input(self):
        for size, bits, optimum in (("2x2", 1, 4), ("3x3", 3, 8)):
            instance = json.loads((ROOT / "instances" / f"instance_{size}.json").read_text())
            with patch("solver.stage1.exact_reference", side_effect=AssertionError("Reference used to construct QUBO")):
                model = build_sequence_qubo(instance)
            self.assertEqual(len(model["variables"]), bits)
            self.assertEqual(min(energy(model, b) for b in itertools.product((0, 1), repeat=bits)), optimum)
            self.assertEqual(exact_reference(instance)["makespan"], optimum)

    def test_invalid_orders_and_unsupported_sizes_fail_closed(self):
        instance = json.loads((ROOT / "instances/instance_3x3.json").read_text())
        for order in ([], ["Z1"] * 3, ["Z1", "Z2", "missing"]):
            with self.assertRaises(ValueError):
                schedule_order(instance, order)
        instance["jobs"] = instance["jobs"][:1]
        with self.assertRaises(ValueError):
            build_sequence_qubo(instance)

    def test_nonoptimal_feasible_samples_are_not_misreported_as_invalid(self):
        from solver.artifacts import assess_samples
        instance = json.loads((ROOT / "instances/instance_3x3.json").read_text())
        model = build_sequence_qubo(instance)
        rows = assess_samples(instance, model, [dict(bits=list(b), count=1)
                for b in itertools.product((0, 1), repeat=3)])
        self.assertEqual(sum(row["feasible"] for row in rows), 6)
        self.assertEqual(sum(row["feasible"] and row["makespan"] == 8 for row in rows), 4)
        self.assertEqual(sum(row["feasible"] and row["makespan"] == 9 for row in rows), 2)

    def test_full_quantum_cost_phase_for_sequence_models(self):
        import numpy as np
        from qiskit.quantum_info import Statevector
        from solver.quantum import qaoa_circuit
        for size in ("2x2", "3x3"):
            model = build_sequence_qubo(json.loads((ROOT / "instances" / f"instance_{size}.json").read_text()))
            n = len(model["variables"])
            circuit, params, scale = qaoa_circuit(model, 1)
            gamma = .731
            actual = Statevector.from_instruction(circuit.assign_parameters(dict(zip(params, [gamma, 0])))).data
            expected = np.array([np.exp(-1j * gamma * energy(model, [(s >> i) & 1 for i in range(n)]) / scale)
                                 / np.sqrt(1 << n) for s in range(1 << n)])
            np.testing.assert_allclose(actual, expected * actual[0] / expected[0], atol=1e-12)

    def test_model_tampering_rejected_even_after_hash_is_recomputed(self):
        from solver.artifacts import digest, save_run, write_json
        from solver.verify import verify_run
        instance = json.loads((ROOT / "instances/instance_3x3.json").read_text())
        model = build_sequence_qubo(instance)
        with tempfile.TemporaryDirectory() as tmp:
            save_run(tmp, "instance_3x3", instance, model, [dict(bits=[1, 1, 1], count=1)], "test fixture", {})
            verify_run(tmp)
            model["linear"][0] += 1
            write_json(Path(tmp) / "model.json", model)
            report = json.loads((Path(tmp) / "run.json").read_text())
            report["model_sha256"] = digest(model)
            write_json(Path(tmp) / "run.json", report)
            with self.assertRaisesRegex(ValueError, "rebuilt from the official input"):
                verify_run(tmp)

    def test_saved_compact_quantum_qasm_and_ground_probability_are_checked(self):
        import shutil
        from solver.verify import verify_run
        source = ROOT / "output/stage1-compact-ready/quantum-3x3"
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "run"
            shutil.copytree(source, directory)
            verify_run(directory)
            qasm = (directory / "circuit.qasm").read_text()
            (directory / "circuit.qasm").write_text(qasm + "// altered retained circuit\n")
            with self.assertRaisesRegex(ValueError, "Saved QASM"):
                verify_run(directory)
            (directory / "circuit.qasm").write_text(qasm)
            report = json.loads((directory / "run.json").read_text())
            report["metadata"]["ideal_ground_probability"] = 0.5
            (directory / "run.json").write_text(json.dumps(report))
            with self.assertRaisesRegex(ValueError, "optimal probability"):
                verify_run(directory)


if __name__ == "__main__":
    unittest.main()
