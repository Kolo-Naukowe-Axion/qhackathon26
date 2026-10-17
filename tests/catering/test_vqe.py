"""Tests for the catering VQE adapter (exact simulation engines)."""
import itertools
import math
import unittest

import numpy as np

from catering.contracts import load_bundle
from catering.decode import decode
from catering.qubo import energy
from catering.methods import vqe as V

CELL = "output/catering-complete-cell-v3/quantum-qubo.json"


def toy_bundle(seed=0, groups=((0, 1), (2, 3, 4))):
    rng = np.random.default_rng(seed)
    n = sum(len(g) for g in groups)
    lin = rng.integers(-20, 20, n)
    quad = [dict(i=i, j=j, value=str(int(rng.integers(-15, 15))))
            for i in range(n) for j in range(i + 1, n)]
    return dict(variable_order=[f"x{i}" for i in range(n)], constant="7",
                linear=[str(int(v)) for v in lin], quadratic=quad,
                objective=dict(constant="7", linear=[str(int(v)) for v in lin], quadratic=quad,
                               weights=dict(U=10, W=1, B=1, R=1)),
                onehot_groups=[dict(indices=list(g)) for g in groups])


def dense_probs(prob, ans, w):
    """Apply the same gates on a dense 2^n qubit statevector (bit i = qubit i, MSB first)."""
    n = prob.n
    states = np.array(list(itertools.product((0, 1), repeat=n)))
    index = {tuple(s): k for k, s in enumerate(states)}
    psi = np.zeros(2 ** n, dtype=complex)
    start = np.zeros(n, dtype=int)
    for g in prob.groups:
        start[g[0]] = 1
    psi[index[tuple(start)]] = 1.0
    z = 1 - 2 * states
    for g in ans.gates:
        t = w[g["p"]]
        if g["kind"] == "ph":
            psi = psi * np.exp(-0.5j * t * np.prod(z[:, list(g["qubits"])], axis=1))
            continue
        qu, qv = g["qubits"]
        c, s = math.cos(t / 2), math.sin(t / 2)
        new = psi.copy()
        for k, st in enumerate(states):
            if st[qu] == 1 and st[qv] == 0 and (g["ctrl"] is None or st[g["ctrl"]] == 1):
                other = st.copy(); other[qu], other[qv] = 0, 1
                kv = index[tuple(other)]
                a, b = psi[k], psi[kv]
                if g["kind"] == "giv":
                    new[k], new[kv] = c * a - s * b, s * a + c * b
                else:
                    new[k], new[kv] = c * a - 1j * s * b, -1j * s * a + c * b
        psi = new
    return states, np.abs(psi) ** 2


def fd_error(ans, seed=1, h=1e-6):
    rng = np.random.default_rng(seed)
    w = ans.w0 + 0.5 * rng.standard_normal(ans.n_params)
    _, g = ans.value_grad(w)
    d = rng.standard_normal(ans.n_params)
    fd = (ans.value_grad(w + h * d)[0] - ans.value_grad(w - h * d)[0]) / (2 * h)
    return abs(fd - g @ d) / max(1.0, abs(fd))


class VQETest(unittest.TestCase):
    def test_contract_smoke_qubo(self):
        b = dict(variable_order=["A", "B"], constant="0", linear=["-4", "-3"],
                 quadratic=[dict(i=0, j=1, value="6")],
                 objective=dict(constant="0", linear=["-4", "-3"], quadratic=[dict(i=0, j=1, value="6")],
                                weights=dict(U=1)),
                 onehot_groups=[dict(indices=[0, 1])])
        prob = V.Problem(b)
        for spec in (V.Spec("product"), V.Spec("sector", layers=1)):
            r = V.run(prob, spec, seed=0, shots=64)
            self.assertGreater(r["p_opt"], 0.99)
            self.assertEqual(r["Emin"], -4)
        self.assertEqual(prob.sector["X"][prob.sector["opt"]].tolist(), [[1, 0]])

    def test_gradients_match_finite_differences(self):
        prob = V.Problem(toy_bundle())
        rng = np.random.default_rng(0)
        specs = [V.Spec("product"), V.Spec("block_hea", layers=2), V.Spec("sector", layers=2),
                 V.Spec("sector", layers=2, pairs="all"), V.Spec("sector", layers=2, pairs="all", cross="zz"),
                 V.Spec("sector", layers=1, pairs="all", inblock="xy", z_phases=True)]
        for spec in specs:
            self.assertLess(fd_error(V.build(prob, spec, rng)), 1e-6, spec.name())

    def test_sector_engine_equals_dense_qubit_circuit(self):
        prob = V.Problem(toy_bundle(3))
        rng = np.random.default_rng(1)
        for spec in [V.Spec("sector", layers=2, pairs="all"),
                     V.Spec("sector", layers=2, pairs="all", cross="zz", inblock="xy", z_phases=True)]:
            ans = V.build(prob, spec, rng)
            w = rng.uniform(0, 2 * np.pi, ans.n_params)
            states, pd = dense_probs(prob, ans, w)
            ps = ans.sector_probs(w)
            lookup = {tuple(x): p for x, p in zip(prob.sector["X"].tolist(), ps)}
            for st, p in zip(states.tolist(), pd):
                self.assertAlmostEqual(lookup.get(tuple(st), 0.0), p, places=12)
            # mean energy = sum_x p(x) E(x) with central energy()
            E = np.array([energy(prob.bundle, list(map(int, x))) for x in states])
            val, _ = ans.value_grad(w)
            self.assertAlmostEqual(val * prob.scale + prob.const, float(pd @ E), places=6)

    def test_block_engines_exact_distribution(self):
        prob = V.Problem(toy_bundle(5))
        rng = np.random.default_rng(2)
        for spec in (V.Spec("product"), V.Spec("block_hea", layers=2)):
            ans = V.build(prob, spec, rng)
            w = rng.uniform(0, 2 * np.pi, ans.n_params)
            X = ans.sample(w, 200000, rng)
            emp = np.mean(prob.energy_bits(X))
            val, _ = ans.value_grad(w)
            self.assertLess(abs(val * prob.scale + prob.const - emp), 0.5)
            onehot = np.all([X[:, g].sum(1) == 1 for g in prob.groups], axis=0)
            self.assertLess(abs(onehot.mean() - ans.sector_probs(w).sum()), 0.01)

    def test_frozen_cell_energies_and_optimum(self):
        bundle = load_bundle(CELL)
        prob = V.Problem(bundle)
        sec = prob.sector
        rng = np.random.default_rng(4)
        for k in rng.choice(len(sec["E"]), 40, replace=False):
            self.assertEqual(int(sec["E"][k]), energy(bundle, list(map(int, sec["X"][k]))))
        best = [list(map(int, x)) for x in sec["X"][sec["opt"]]]
        self.assertEqual(sec["Emin"], 68)              # reference-sector.json energy
        for bits in best:
            d = decode(bundle, bits)
            self.assertTrue(d["valid"])
            self.assertEqual(d["check"]["metrics"], dict(U=0, W=0, B=2, R=2))
        # validity mask agrees with the central decoder on a sample of sector states
        for k in rng.choice(len(sec["E"]), 30, replace=False):
            self.assertEqual(bool(sec["valid"][k]), decode(bundle, list(map(int, sec["X"][k])))["valid"])


if __name__ == "__main__":
    unittest.main()
