"""QAOA adapter tests. Worked numbers come from METHODS_TUTORIAL sections 6 and 8."""
import importlib.util
import json
import math
import tempfile
import unittest
from pathlib import Path

import numpy as np

from catering.contracts import save_json
from catering.domain import snapshot
from catering.meal_blocks import meal_fixture, compile_meal_blocks, sector_data, sector_bits
from catering.meal_search import portfolio, warm_state, evolve as pilot_evolve
from catering.methods import qaoa
from catering.options import enumerate_options
from catering.qubo import energy, ising
from catering.run import evaluate


def toy(constant, linear, quadratic=()):
    """Minimal hand-written bundle: only the fields the adapter and literal energy read."""
    return dict(case_id="toy", bundle_sha256="toy", representation_id="toy",
                constant=str(constant), linear=[str(c) for c in linear],
                quadratic=[dict(i=i, j=j, value=str(v)) for i, j, v in quadratic],
                variable_order=[f"x{i}" for i in range(len(linear))])


def meal_bundle():
    p = meal_fixture(1)
    s = snapshot(p, "S0")
    return compile_meal_blocks(p, s, portfolio(enumerate_options(p, s), [], 3, np.random.default_rng(1)))


class TutorialWorkedNumbers(unittest.TestCase):
    def test_example_A_energy_table_bit_order_and_ising(self):
        # Section 2.2/6.0: E = 3x1 - 2x2 + 4x1x2 + 1, energies (00,01,10,11) = 1,-1,4,6
        # in the tutorial's |x1 x2> notation. Index bit i is x_(i+1) here.
        b = toy(1, [3, -2], [(0, 1, 4)])
        table = qaoa.energy_table(b["constant"], b["linear"], b["quadratic"], 2)
        self.assertEqual(table.tolist(), [1, 4, -1, 6])
        for index in range(4):
            self.assertEqual(table[index], energy(b, [index & 1, index >> 1]))
        # Section 6.0 step 4: H = 2.5 I - 2.5 Z1 + 0 Z2 + 1 Z1Z2. The repo helper returns 4H.
        z = ising(b)
        self.assertEqual(int(z["constant"])/4, 2.5)
        self.assertEqual([int(v)/4 for v in z["linear"]], [-2.5, 0.0])
        self.assertEqual([int(t["value"])/4 for t in z["quadratic"]], [1.0])

    def test_two_job_toy_interference_at_exact_angles(self):
        # Section 8.1 step 7: E = 1 - yA - yB + 2 yA yB, gamma=pi/2, beta=3pi/8
        # gives -(|01> + |10>)/sqrt(2): the clashing bitstrings cancel exactly.
        b = toy(1, [-1, -1], [(0, 1, 2)])
        space = qaoa._full_space(b)
        plus = np.full(4, 0.5, dtype=complex)
        state = qaoa.evolve(b, space, "standard", plus, np.array([math.pi/2, 3*math.pi/8]), 1.0)
        np.testing.assert_allclose(state, [0, -1/math.sqrt(2), -1/math.sqrt(2), 0], atol=1e-12)

    def test_one_qubit_probability_formula(self):
        # Section 6.2: H = hZ, so E(0)=+h, E(1)=-h, i.e. E = h - 2h x.
        # From |+>, P(1) = (1 - sin(2 beta) sin(2 gamma h)) / 2.
        for h in (1, 2):
            b = toy(h, [-2*h])
            space = qaoa._full_space(b)
            for gamma, beta in ((0.0, 0.4), (0.3, 0.0), (math.pi/(4*h), -math.pi/4), (0.37, 1.1), (-0.8, 0.25)):
                state = qaoa.evolve(b, space, "standard", np.full(2, 1/math.sqrt(2), dtype=complex),
                                    np.array([gamma, beta]), 1.0)
                expected = 0.5*(1 - math.sin(2*beta)*math.sin(2*gamma*h))
                self.assertAlmostEqual(abs(state[1])**2, expected, places=12)
        # gamma*h = pi/4, beta = -pi/4 gives the answer with certainty.
        state = qaoa.evolve(toy(1, [-2]), qaoa._full_space(toy(1, [-2])), "standard",
                            np.full(2, 1/math.sqrt(2), dtype=complex), np.array([math.pi/4, -math.pi/4]), 1.0)
        self.assertAlmostEqual(abs(state[1])**2, 1.0, places=12)

    @unittest.skipUnless(importlib.util.find_spec("qiskit"), "Qiskit optional")
    def test_numpy_kernel_matches_tutorial_gate_list_in_qiskit(self):
        # Section 8.0: H on every qubit, RZ(2 gamma h_i), RZZ(2 gamma J_ij), RX(2 beta) per layer.
        from qiskit import QuantumCircuit
        from qiskit.quantum_info import Statevector
        rng = np.random.default_rng(3)
        n = 5
        quadratic = [(i, j, int(rng.integers(-4, 5))) for i in range(n) for j in range(i+1, n) if rng.random() < 0.6]
        b = toy(int(rng.integers(-3, 4)), [int(v) for v in rng.integers(-5, 6, n)], quadratic)
        z = ising(b)
        h = [int(v)/4 for v in z["linear"]]
        J = {(t["i"], t["j"]): int(t["value"])/4 for t in z["quadratic"]}
        params = [0.31, 0.47, -0.22, 0.9]
        qc = QuantumCircuit(n)
        qc.h(range(n))
        for gamma, beta in np.reshape(params, (-1, 2)):
            for i, value in enumerate(h):
                if value:
                    qc.rz(2*gamma*value, i)
            for (i, j), value in J.items():
                if value:
                    qc.rzz(2*gamma*value, i, j)
            qc.rx(2*beta, range(n))
        reference = Statevector.from_instruction(qc).data
        space = qaoa._full_space(b)
        ours = qaoa.evolve(b, space, "standard", np.full(1 << n, 2**(-n/2), dtype=complex), np.array(params), 1.0)
        # The constant c' only contributes a global phase.
        self.assertAlmostEqual(abs(np.vdot(reference, ours)), 1.0, places=10)


class SectorVariants(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = meal_bundle()
        cls.space = qaoa._sector_space(cls.bundle)

    def test_sector_energies_match_full_literal_table(self):
        full = qaoa._full_space(self.bundle)
        for index in range(self.space["states"]):
            bits = sector_bits(self.bundle, self.space["sector"], index)
            mask = sum(x << i for i, x in enumerate(bits))
            self.assertEqual(self.space["energy"][index], full["energy"][mask])
            self.assertEqual(self.space["valid"][index], full["valid"][mask])

    def test_single_gamma_xy_equals_multiangle_with_tied_conflict_angle(self):
        scale = qaoa.default_scale(self.bundle)
        penalty = int(self.bundle["penalty"])
        uniform = qaoa.initial_state(self.bundle, self.space, "xy", qaoa.DEFAULTS)
        params = [0.41, 0.33, -0.27, -0.12]
        single = qaoa.evolve(self.bundle, self.space, "xy", uniform, np.array(params), scale)
        tied = []
        for gamma, beta in np.reshape(params, (-1, 2)):
            tied += [gamma, gamma*penalty/scale, beta]
        multi = qaoa.evolve(self.bundle, self.space, "xy_multiangle_warm", uniform, np.array(tied), scale)
        np.testing.assert_allclose(single, multi, atol=1e-12)

    def test_multiangle_reproduces_pilot_evolution(self):
        scale = float(self.bundle["objective"]["weights"]["U"])
        initial = warm_state(self.bundle, self.space["sector"], set(), 0.15)
        params = [(0.27, 0.39, 0.41), (-0.13, 0.51, -0.23)]
        ours = qaoa.evolve(self.bundle, self.space, "xy_multiangle_warm", initial.astype(complex),
                           np.array(params).reshape(-1), scale)
        np.testing.assert_allclose(ours, pilot_evolve(initial, self.space["sector"], params, scale), atol=1e-12)

    def test_depth_zero_returns_the_initial_distribution(self):
        for variant, bundle in (("standard", self.bundle), ("xy", self.bundle)):
            result = qaoa.solve_qubo(bundle, dict(shots=64), dict(variant=variant, depth=0))
            d = result["configuration"]["distribution"]
            self.assertAlmostEqual(d["ground_probability"], d["ground_states"]/d["simulated_states"], places=12)
            self.assertEqual(result["work"]["training_objective_evaluations"], 0)

    def test_xy_variants_never_leave_the_onehot_sector(self):
        for variant in ("xy", "xy_multiangle_warm"):
            result = qaoa.solve_qubo(self.bundle, dict(training_objective_evaluations=12, shots=256),
                                     dict(variant=variant, depth=2, restarts=2, seed=5))
            for sample in result["samples"]:
                for group in self.bundle["onehot_groups"]:
                    self.assertEqual(sum(sample["bits"][i] for i in group["indices"]), 1)
            self.assertAlmostEqual(result["configuration"]["distribution"]["norm"], 1.0, places=10)


class AdapterContract(unittest.TestCase):
    def test_contract_smoke_case_is_solved_and_labelled(self):
        # Solver contract section 5: E = -4 xA - 3 xB + 6 xA xB, unique optimum [1, 0] at -4.
        b = toy(0, [-4, -3], [(0, 1, 6)])
        result = qaoa.solve_qubo(b, dict(training_objective_evaluations=40, shots=512),
                                 dict(variant="standard", depth=1, restarts=2, loss="expectation"))
        best = min(result["samples"], key=lambda s: int(s["reported_energy"]))
        self.assertEqual(best["bits"], [1, 0])
        self.assertEqual(best["reported_energy"], "-4")
        self.assertEqual(sum(s["count"] for s in result["samples"]), 512)
        self.assertEqual(result["execution_kind"], "quantum_simulation")
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["physical_qpu_calls"], 0)
        self.assertLessEqual(result["work"]["training_objective_evaluations"], 40)

    def test_budgets_are_enforced_and_random_baseline_counts_exactly(self):
        b = toy(0, [-4, -3, 2], [(0, 1, 6), (1, 2, -3)])
        random = qaoa.solve_qubo(b, dict(training_objective_evaluations=7, shots=16),
                                 dict(variant="standard", optimizer="random"))
        self.assertEqual(random["work"]["training_objective_evaluations"], 7)
        for optimizer in ("COBYLA", "Nelder-Mead", "L-BFGS-B"):
            result = qaoa.solve_qubo(b, dict(training_objective_evaluations=10, shots=16),
                                     dict(variant="standard", optimizer=optimizer, restarts=3, depth=2))
            self.assertLessEqual(result["work"]["training_objective_evaluations"], 10)
            self.assertGreater(result["work"]["training_objective_evaluations"], 0)

    def test_layerwise_grows_depth_within_budget(self):
        bundle = meal_bundle()
        with tempfile.TemporaryDirectory() as tmp:
            result = qaoa.solve_qubo(bundle, dict(training_objective_evaluations=60, shots=64),
                                     dict(variant="xy_multiangle_warm", depth=3, optimizer="layerwise"),
                                     Path(tmp) / "run")
            trace = json.loads((Path(tmp) / "run" / "training.json").read_text())["trace"]
        self.assertEqual(result["work"]["training_objective_evaluations"], 60)
        self.assertEqual(len(result["configuration"]["best_params"]), 9)
        # Stages run in order 1, 2, 3 and each stage optimizes a circuit of that depth.
        stages = [t["start"] for t in trace]
        self.assertEqual(stages, sorted(stages))
        self.assertEqual(set(stages), {1, 2, 3})
        self.assertTrue(all(len(t["params"]) == 3*t["start"] for t in trace))
        with self.assertRaises(ValueError):
            qaoa.solve_qubo(bundle, dict(training_objective_evaluations=2), dict(depth=3, optimizer="layerwise"))

    def test_same_seed_reproduces_samples(self):
        b = toy(0, [-4, -3, 2], [(0, 1, 6), (1, 2, -3)])
        runs = [qaoa.solve_qubo(b, dict(training_objective_evaluations=15, shots=128),
                                dict(variant="standard", depth=2, seed=11)) for _ in range(2)]
        self.assertEqual(runs[0]["samples"], runs[1]["samples"])
        self.assertEqual(runs[0]["configuration"]["best_params"], runs[1]["configuration"]["best_params"])

    def test_central_evaluator_accepts_samples_from_every_variant(self):
        bundle = meal_bundle()
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            save_json(tmp / "bundle.json", bundle)
            for variant in qaoa.VARIANTS:
                result = qaoa.solve_qubo(bundle, dict(training_objective_evaluations=10, shots=128),
                                         dict(variant=variant, depth=1, restarts=2), tmp / f"run-{variant}")
                self.assertTrue((tmp / f"run-{variant}" / "result.json").exists())
                save_json(tmp / f"{variant}.json", result)
                checked = evaluate(tmp / "bundle.json", tmp / f"{variant}.json", tmp / f"{variant}-eval.json")
                self.assertEqual(sum(r["count"] for r in checked), 128)
                if variant != "standard":
                    self.assertTrue(all(r["onehot_valid"] for r in checked))

    def test_refusals(self):
        with self.assertRaises(ValueError):
            qaoa.solve_qubo(toy(0, [1]*(qaoa.MAX_STANDARD_QUBITS+1)), None, dict(variant="standard"))
        with self.assertRaises(ValueError):
            qaoa.solve_qubo(toy(0, [1, 2]), None, dict(variant="nope"))
        with self.assertRaises(ValueError):
            qaoa.solve_qubo(toy(0, [1, 2]), dict(allowed_external_execution=True), dict(variant="standard"))
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                qaoa.solve_qubo(toy(0, [1, 2]), None, dict(variant="standard"), tmp)


if __name__ == "__main__":
    unittest.main()
