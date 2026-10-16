import importlib.util
import unittest


@unittest.skipUnless(importlib.util.find_spec("iqm"), "Install requirements-odra.txt for IQM compilation tests")
class IQMCompilationTests(unittest.TestCase):
    def test_star_routing_preserves_classical_probabilities_with_physical_ancilla(self):
        import json
        from iqm.qiskit_iqm import IQMFakeAdonis
        from solver.stage1 import ROOT, build_qubo
        from solver.quantum import qaoa_circuit
        from solver.odra import compile_candidate
        instance = json.loads((ROOT / "instances/instance_2x2.json").read_text())
        model = build_qubo(instance, 4, "domain-wall")
        circuit, parameters, _ = qaoa_circuit(model, 1)
        circuit = circuit.assign_parameters(dict(zip(parameters, [0.731, 0.297])))
        circuit.measure_all()
        compiled, seed, error = compile_candidate(circuit, IQMFakeAdonis(), seeds=2)
        self.assertEqual(compiled.num_clbits, 4)
        self.assertEqual(compiled.num_qubits, 5)
        self.assertLess(error, 1e-10)
        self.assertTrue(set(compiled.count_ops()) <= {"r", "cz", "barrier", "measure", "delay", "id"})

    def test_counts_decode_uses_classical_bit_order(self):
        from solver.odra import counts_records
        self.assertEqual(counts_records({"00 11": 5}, 4), [dict(bits=[1, 1, 0, 0], count=5)])
        with self.assertRaises(ValueError):
            counts_records({"00011": 5}, 4)


if __name__ == "__main__":
    unittest.main()
