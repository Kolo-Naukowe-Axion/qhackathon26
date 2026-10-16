"""Library-boundary tests; install requirements-solver.txt to run these."""

import importlib.util
import itertools
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HAVE_LIBRARIES = all(importlib.util.find_spec(name) for name in ("dimod", "numpy", "qiskit", "veloxq_sdk"))


@unittest.skipUnless(HAVE_LIBRARIES, "Install the solver requirements for library-boundary tests")
class SolverBoundaryTests(unittest.TestCase):
    def setUp(self):
        from solver.stage1 import ROOT, build_qubo
        self.instance = json.loads((ROOT / "instances/instance_2x2.json").read_text())
        self.model = build_qubo(self.instance, 4, "domain-wall")

    def test_qaoa_cost_unitary_matches_every_qubo_basis_state(self):
        import numpy as np
        from qiskit.quantum_info import Statevector
        from solver.quantum import qaoa_circuit
        from solver.stage1 import energy
        circuit, parameters, scale = qaoa_circuit(self.model, 1)
        gamma = 0.731
        state = Statevector.from_instruction(circuit.assign_parameters(dict(zip(parameters, [gamma, 0])))).data
        expected = np.array([np.exp(-1j * gamma * energy(self.model, [(i >> j) & 1 for j in range(4)]) / scale) / 4 for i in range(16)])
        phase = state[0] / expected[0]
        np.testing.assert_allclose(state, phase * expected, atol=1e-12)

    def test_sdk_input_serialization_preserves_energy_and_labels(self):
        import h5py
        import numpy as np
        from solver.stage1 import to_dimod, energy
        from solver.velox import write_packet
        for model in (self.model,):
            with tempfile.TemporaryDirectory() as tmp, patch("socket.socket.connect", side_effect=AssertionError("Offline test attempted network")):
                path = Path(tmp) / "input.h5"
                write_packet(model, path)
                with h5py.File(path) as f:
                    group = f["Ising"]
                    n = len(model["variables"])
                    self.assertEqual(list(group["labels"].asstr()[:]), list(map(str, range(n))))
                    self.assertEqual(group.attrs["var_type"], "SPIN")
                    if isinstance(group["couplings"], h5py.Group):
                        sparse = group["couplings"]
                        matrix = np.zeros((n, n))
                        matrix[sparse["I"][:] - 1, sparse["J"][:] - 1] = sparse["V"][:]
                    else:
                        matrix = group["couplings"][:]
                    for bits in itertools.product((0, 1), repeat=n):
                        spins = 2 * np.array(bits) - 1
                        serialized_energy = group.attrs["offset"] + group["biases"][:] @ spins + 0.5 * spins @ matrix @ spins
                        self.assertAlmostEqual(serialized_energy, energy(model, bits))
                        self.assertAlmostEqual(to_dimod(model).spin.energy(dict(enumerate(spins))), energy(model, bits))

    def test_actual_sdk_result_parser_handles_shuffled_string_labels(self):
        import dimod
        import h5py
        import numpy as np
        from veloxq_sdk.api.jobs import VeloxSampleSet
        from solver.stage1 import energy
        from solver.velox import extract_samples
        bits = [0, 1, 1, 0]
        labels = ["3", "1", "0", "2"]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fixture.h5"
            with h5py.File(path, "w") as f:
                group = f.create_group("Spectrum")
                group.create_dataset("states", data=[[2 * bits[int(label)] - 1 for label in labels]])
                group.create_dataset("energies", data=[energy(self.model, bits)])
                group.create_dataset("metadata", data=json.dumps({"fixture": "synthetic boundary test, not a service result"}))
                group.create_dataset("labels", data=np.array(labels, dtype=h5py.string_dtype()))
            with h5py.File(path) as f:
                samples = VeloxSampleSet.from_result(f)
            self.assertEqual(samples.vartype, dimod.SPIN)
            records, convention = extract_samples(samples, self.model)
            self.assertEqual(records[0]["bits"], bits)
            self.assertEqual(convention["reported_minus_recomputed_energy"], 0)

    def test_result_parser_rejects_wrong_energy_or_variables(self):
        import dimod
        from solver.velox import extract_samples
        samples = dimod.SampleSet.from_samples({i: 1 for i in range(4)}, dimod.SPIN, energy=[999])
        with self.assertRaises(ValueError):
            extract_samples(samples, self.model)
        samples = dimod.SampleSet.from_samples({i: 1 for i in range(3)}, dimod.SPIN, energy=[0])
        with self.assertRaises(ValueError):
            extract_samples(samples, self.model)

    def test_failure_retains_diagnostics_without_accepted_schedule(self):
        from solver.artifacts import save_run
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(RuntimeError):
                save_run(tmp, "instance_2x2", self.instance, self.model, [dict(bits=[0] * 4)], "Synthetic failure fixture", {})
            self.assertTrue((Path(tmp) / "samples.json").exists())
            self.assertFalse((Path(tmp) / "schedule.json").exists())

    def test_failed_and_timed_out_remote_jobs_are_not_accepted(self):
        from solver.velox import wait_for_job
        from types import SimpleNamespace
        job = SimpleNamespace(status="failed", refresh=lambda: None)
        with self.assertRaises(RuntimeError):
            wait_for_job(job, 1)
        job.status = "running"
        with self.assertRaises(TimeoutError):
            wait_for_job(job, 0)


if __name__ == "__main__":
    unittest.main()
