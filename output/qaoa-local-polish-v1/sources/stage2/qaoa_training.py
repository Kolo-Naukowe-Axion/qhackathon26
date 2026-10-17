"""Local adjoint training of the existing assignment-sector XY QAOA circuit.

The backward pass reverses each unitary to reconstruct its input, retaining
only two sector vectors. It changes angle training, not the represented domain,
state preparation, cost Hamiltonian or mixer. SciPy is an optional fit dependency.
"""
from __future__ import annotations

import math
import time

import numpy as np


def cost_scale(sector):
    return max([1] + [abs(v) for v in sector.phase['linear']] +
               [abs(v) for v in sector.phase['quadratic'].values()])


def _rotate(state, sizes, axis, j, beta):
    view = np.moveaxis(state.reshape(sizes), axis, -1)
    a, b = view[..., j].copy(), view[..., j + 1].copy()
    c, s = math.cos(beta), -1j * math.sin(beta)
    view[..., j] = c * a + s * b
    view[..., j + 1] = c * b + s * a


class AdjointObjective:
    """Exact simulated expectation/CVaR and all 2p analytic derivatives.

    The CVaR derivative uses the moving quantile: (E-quantile)_-/alpha.
    Sorting energies is charged classical work; no argmin or optimum mask is
    used to train. Objective units are divided by the Hamiltonian scale.
    """

    def __init__(self, sector, layers, alpha=1.0):
        if type(layers) is not int or layers < 1 or not 0 < alpha <= 1:
            raise ValueError('Positive integer layers and 0<alpha<=1 required')
        self.sector, self.layers, self.alpha = sector, layers, alpha
        self.scale = cost_scale(sector)
        self.diagonal = (sector.energies.astype(float) - float(sector.energies[0])) / self.scale
        self.order = np.argsort(sector.energies, kind='stable') if alpha < 1 else None
        self.pairs = [(axis, j) for axis, size in enumerate(sector.sizes) for j in range(size - 1)]
        self.calls = 0
        self.history = []
        self.best = None

    def value_weights(self, probability):
        if self.order is None:
            return float(np.dot(probability, self.diagonal)), self.diagonal
        cumulative = np.cumsum(probability[self.order])
        index = min(int(np.searchsorted(cumulative, self.alpha)), len(cumulative) - 1)
        quantile = self.diagonal[self.order[index]]
        weights = np.minimum(self.diagonal - quantile, 0) / self.alpha
        return float(quantile + np.dot(probability, weights)), weights

    def __call__(self, angles):
        angles = np.asarray(angles, dtype=float)
        if angles.shape != (2 * self.layers,) or not np.isfinite(angles).all():
            raise ValueError('Exactly 2p finite angles required')
        gammas, betas = angles[:self.layers], angles[self.layers:]
        state = self.sector.evolve(gammas.tolist(), betas.tolist(), self.scale)
        probability = np.abs(state) ** 2
        value, weights = self.value_weights(probability)
        adjoint = weights * state
        gradient = np.zeros(2 * self.layers)
        for layer in reversed(range(self.layers)):
            for axis, j in reversed(self.pairs):
                psi = np.moveaxis(state.reshape(self.sector.sizes), axis, -1)
                lam = np.moveaxis(adjoint.reshape(self.sector.sizes), axis, -1)
                inner = np.vdot(lam[..., j], psi[..., j + 1]) + np.vdot(lam[..., j + 1], psi[..., j])
                gradient[self.layers + layer] += 2 * inner.imag
                _rotate(state, self.sector.sizes, axis, j, -betas[layer])
                _rotate(adjoint, self.sector.sizes, axis, j, -betas[layer])
            gradient[layer] = 2 * np.vdot(adjoint, self.diagonal * state).imag
            inverse = np.exp(1j * gammas[layer] * self.diagonal)
            state *= inverse
            adjoint *= inverse
        self.calls += 1
        self.history.append(dict(evaluation=self.calls, value=value,
                                 gradient_norm=float(np.linalg.norm(gradient))))
        if self.best is None or value < self.best[0]:
            self.best = (value, angles.copy())
        return value, gradient


def train(sector, layers=2, seed=7, evaluations=256, alpha=.25, initial=None):
    """A bounded L-BFGS-B start; every completed adjoint call is counted.

    Gamma is not wrapped modulo 2pi: scaled cost eigenvalues need not be
    integers. Beta has a 2pi period but remains unbounded during optimization.
    Angle starts depend only on seed or a declared shallower trained circuit.
    """
    from scipy.optimize import minimize

    if type(evaluations) is not int or evaluations < 1:
        raise ValueError('Positive integer evaluation budget required')
    began, cpu = time.perf_counter(), time.process_time()
    objective = AdjointObjective(sector, layers, alpha)
    if initial is None:
        rng = np.random.default_rng(seed)
        initial = np.r_[rng.uniform(0, 2 * math.pi, layers), rng.uniform(-math.pi / 2, math.pi / 2, layers)]
    initial = np.asarray(initial, dtype=float)
    stopped = False

    class BudgetExhausted(Exception):
        pass

    def bounded(angles):
        if objective.calls >= evaluations:
            raise BudgetExhausted
        return objective(angles)

    try:
        fit = minimize(bounded, initial, jac=True, method='L-BFGS-B',
                       options=dict(maxiter=evaluations, maxfun=evaluations, maxls=30,
                                    ftol=1e-13, gtol=1e-8, maxcor=12))
        status = str(fit.message)
    except BudgetExhausted:
        stopped, status = True, 'Declared objective/gradient evaluation budget exhausted'
    value, angles = objective.best
    return dict(gammas=angles[:layers].tolist(), betas=angles[layers:].tolist(),
                layers=layers, seed=seed, alpha=alpha, scale=objective.scale,
                objective='expectation' if alpha == 1 else 'CVaR', scaled_training_value=value,
                evaluations=objective.calls, max_evaluations=evaluations, budget_exhausted=stopped,
                optimizer='L-BFGS-B with exact reversible adjoint gradient', status=status,
                initial_angles=initial.tolist(), history=objective.history,
                wall_seconds=time.perf_counter() - began, process_cpu_seconds=time.process_time() - cpu,
                exact_reference_used_for_training=False, physical_qpu_calls=0)


def assess(sector, fit, seeds=(101, 103, 107), shots=512):
    """Post-training reference reporting and independent Born sampling replicas."""
    began = time.perf_counter()
    probability = np.abs(sector.evolve(fit['gammas'], fit['betas'], fit['scale'])) ** 2
    norm_error = abs(float(probability.sum()) - 1)
    if norm_error > 1e-9:
        raise AssertionError('State normalization failed')
    probability /= probability.sum()
    optimum = int(sector.energies.min())
    ground, feasible = sector.energies == optimum, sector.energies < sector.q.penalty
    runs = []
    for seed in seeds:
        counts = np.random.default_rng(seed).multinomial(shots, probability)
        seen = np.flatnonzero(counts)
        winner = min(seen, key=lambda i: (int(sector.energies[i]), int(i)))
        bits = sector.bits(winner)
        decoded = sector.q.decode(bits)
        if sector.q.energy(bits) != int(sector.energies[winner]):
            raise AssertionError('Measured sample energy mismatch')
        runs.append(dict(seed=seed, shots=shots, energy=int(sector.energies[winner]),
                         optimal_samples=int(counts[ground].sum()), feasible_samples=int(counts[feasible].sum()),
                         bits=bits, decoded=decoded,
                         observed_counts={str(int(i)): int(counts[i]) for i in seen}))
    return dict(exact_hit_probability=float(probability[ground].sum()),
                feasible_probability=float(probability[feasible].sum()), sector_exact_energy=optimum,
                ground_states=int(ground.sum()), sector_states=len(probability), logical_qubits=len(sector.q.linear),
                norm_error=norm_error, runs=runs, assessment_seconds=time.perf_counter() - began,
                qasm=sector.circuit(fit['gammas'], fit['betas'], fit['scale']), physical_qpu_calls=0)
