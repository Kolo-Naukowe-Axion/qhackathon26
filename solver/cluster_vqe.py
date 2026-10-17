"""Cluster-entangled VQE on the time-indexed domain-wall QUBO.

Question: how much entanglement, and in which places, does a VQE need to
find optimal schedules?

Ansatz (real amplitudes). Qubits are partitioned into clusters. Inside each
cluster: an RY layer, then L x [CZ chain + RY layer]. There are NO gates
between clusters, so the state is an exact tensor product of cluster states
|psi> = |psi_C1> (x) |psi_C2> (x) ...

That makes the model classically simulable by design: the cost is about
sum_c 2^|c| amplitudes instead of 2^n. Nothing here is a claim of quantum
advantage or of an unsimulable circuit. All runs are exact noiseless
simulations; no QPU or VeloxQ call is made.

Loss = mean QUBO energy <E> = offset + sum_i a_i <x_i>
       + sum_{i<j same cluster} b_ij <x_i x_j>
       + sum_{i<j different clusters} b_ij <x_i><x_j>.
The loss is linear in each cluster's distribution with the others held
fixed. Its gradient w.r.t. cluster c's angles is therefore the gradient of
<psi_c| diag(h_c) |psi_c> for the effective diagonal Hamiltonian
h_c(x) = sum_{i in c} (a_i + sum_{j not in c} b_ij <x_j>) x_i + intra_c(x).
That gradient is computed with adjoint differentiation
(one forward plus one backward sweep per cluster).

Qubit order inside a cluster: local qubit 0 is the most significant bit
of the basis index.
"""
from __future__ import annotations


import numpy as np

from .stage1 import build_qubo


# ---------------------------------------------------------------- QUBO side
class DenseQubo:
    """Dense symmetric view of a stage1 QUBO model (upper-triangular-once)."""

    def __init__(self, model):
        self.model = model
        self.n = len(model["variables"])
        self.a = np.array(model["linear"], float)
        self.offset = float(model["offset"])
        self.B = np.zeros((self.n, self.n))
        for i, j, q in model["quadratic"]:  # pair value b_ij stored on both sides
            self.B[i, j] += q
            self.B[j, i] += q

    def energies(self, X):
        X = np.asarray(X, float)
        return self.offset + X @ self.a + 0.5 * np.einsum("si,ij,sj->s", X, self.B, X)


def domain_wall_groups(model):
    """Bits of each operation (job, machine), in model order."""
    groups = {}
    for i, v in enumerate(model["variables"]):
        groups.setdefault((v["job"], v["machine"]), []).append(i)
    return groups


def all_valid_codewords(model):
    """Every monotone domain-wall assignment (one start per operation)."""
    n = len(model["variables"])
    X = np.zeros((1, n), np.int8)
    for g in domain_wall_groups(model).values():
        d = len(g)
        opts = np.array([[1] * t + [0] * (d - t) for t in range(d + 1)], np.int8)
        R = np.repeat(X, len(opts), 0)
        R[:, g] = np.tile(opts, (len(X), 1))
        X = R
    return X


# ---------------------------------------------------------------- circuits
def _ry(t):
    c, s = np.cos(t / 2), np.sin(t / 2)
    return np.array([[c, -s], [s, c]])


def _dry(t):
    c, s = np.cos(t / 2), np.sin(t / 2)
    return 0.5 * np.array([[-s, -c], [c, -s]])


def _apply1(psi, U, q, k):
    p = psi.reshape(2 ** q, 2, 2 ** (k - q - 1))
    return np.einsum("ab,ibj->iaj", U, p).reshape(-1)


class Cluster:
    def __init__(self, idx, layers, B):
        self.idx = np.array(idx)
        self.k = len(idx)
        self.L = layers
        self.npar = self.k * (layers + 1)
        basis = np.arange(2 ** self.k)
        self.bits = (basis[:, None] >> (self.k - 1 - np.arange(self.k))) & 1
        self.cz = np.ones(2 ** self.k)
        for q in range(self.k - 1):  # CZ chain q-(q+1)
            self.cz *= np.where(self.bits[:, q] & self.bits[:, q + 1], -1, 1)
        sub = B[np.ix_(self.idx, self.idx)]
        self.intra = 0.5 * np.einsum("xi,ij,xj->x", self.bits, sub, self.bits)

    def _gates(self, th):
        T = th.reshape(self.L + 1, self.k)
        g = []
        for layer in range(self.L + 1):
            if layer:
                g.append(("cz", None, None))
            for q in range(self.k):
                g.append(("ry", q, (layer, q)))
        return g, T

    def state(self, th):
        g, T = self._gates(th)
        psi = np.zeros(2 ** self.k)
        psi[0] = 1.0
        for typ, q, pi in g:
            psi = self.cz * psi if typ == "cz" else _apply1(psi, _ry(T[pi]), q, self.k)
        return psi

    def adjoint_grad(self, th, h):
        """d/dtheta <psi|diag(h)|psi> by adjoint differentiation."""
        g, T = self._gates(th)
        phi = self.state(th)
        lam = h * phi
        grad = np.zeros_like(T)
        for typ, q, pi in reversed(g):
            if typ == "cz":
                phi, lam = self.cz * phi, self.cz * lam
                continue
            U = _ry(T[pi])
            phi = _apply1(phi, U.T, q, self.k)
            grad[pi] = 2 * lam @ _apply1(phi, _dry(T[pi]), q, self.k)
            lam = _apply1(lam, U.T, q, self.k)
        return grad.reshape(-1)


class ClusterVQE:
    def __init__(self, qubo: DenseQubo, clusters, layers):
        self.q = qubo
        self.clusters = [Cluster(c, layers, qubo.B) for c in clusters]
        flat = sorted(np.concatenate([c.idx for c in self.clusters]).tolist())
        if flat != list(range(qubo.n)):
            raise ValueError("clusters must partition all qubits exactly once")
        self.slices = np.cumsum([0] + [c.npar for c in self.clusters])
        self.npar = int(self.slices[-1])
        self.Bcross = qubo.B.copy()
        for c in self.clusters:
            self.Bcross[np.ix_(c.idx, c.idx)] = 0

    def _parts(self, th):
        return zip(self.clusters, self.slices[:-1], self.slices[1:])

    def loss_grad(self, th, grad=True):
        m = np.zeros(self.q.n)
        intra = 0.0
        for c, a0, a1 in self._parts(th):
            p = c.state(th[a0:a1]) ** 2
            m[c.idx] = p @ c.bits
            intra += p @ c.intra
        loss = self.q.offset + self.q.a @ m + 0.5 * m @ self.Bcross @ m + intra
        if not grad:
            return loss
        field = self.q.a + self.Bcross @ m
        G = np.zeros(self.npar)
        for c, a0, a1 in self._parts(th):
            h = c.bits @ field[c.idx] + c.intra
            G[a0:a1] = c.adjoint_grad(th[a0:a1], h)
        return loss, G

    def sample(self, th, shots, rng):
        X = np.zeros((shots, self.q.n), np.int8)
        for c, a0, a1 in self._parts(th):
            p = c.state(th[a0:a1]) ** 2
            ix = rng.choice(len(p), shots, p=p / p.sum())
            X[:, c.idx] = c.bits[ix]
        return X

    def prob_of(self, th, X):
        """Exact probability of each bitstring row of X under the product state."""
        out = np.ones(len(X))
        for c, a0, a1 in self._parts(th):
            p = c.state(th[a0:a1]) ** 2
            weights = 2 ** (c.k - 1 - np.arange(c.k))
            out *= p[np.asarray(X)[:, c.idx] @ weights]
        return out


# ---------------------------------------------------------------- clusterings
def factory_clusters(model):
    """Factory-shaped partitions of the domain-wall bits."""
    var = model["variables"]

    def by(f):
        d = {}
        for i, v in enumerate(var):
            d.setdefault(f(v), []).append(i)
        return list(d.values())

    return {
        "product (k=1)": [[i] for i in range(len(var))],
        "per-operation": by(lambda v: (v["job"], v["machine"])),
        "per-machine": by(lambda v: v["machine"]),
        "per-job": by(lambda v: v["job"]),
    }


def random_like(clusters, n, rng):
    """Random partition with exactly the same multiset of cluster sizes."""
    p = rng.permutation(n)
    out, s = [], 0
    for c in clusters:
        out.append(p[s:s + len(c)].tolist())
        s += len(c)
    return out


# ---------------------------------------------------------------- one run
def run_once(qubo, clusters, seed, layers, optimal, groups, shots=1000, maxiter=2000):
    """Random-start L-BFGS-B on the mean energy; returns one result row."""
    from scipy.optimize import minimize
    import time

    vqe = ClusterVQE(qubo, clusters, layers)
    rng = np.random.default_rng(seed)
    th0 = rng.uniform(-np.pi, np.pi, vqe.npar)
    t = time.time()
    r = minimize(vqe.loss_grad, th0, jac=True, method="L-BFGS-B", options=dict(maxiter=maxiter))
    X = vqe.sample(r.x, shots, np.random.default_rng(10_000 + seed))
    Es = qubo.energies(X)
    head = X[:300]  # monotone-validity estimate on the first 300 shots
    valid = np.mean([all((np.diff(x[g]) <= 0).all() for g in groups) for x in head])
    return dict(seed=seed, L=layers, k_max=max(map(len, clusters)), params=vqe.npar,
                mean_E=float(r.fun), P_opt=float(vqe.prob_of(r.x, optimal).sum()),
                best_E_1000=float(Es.min()), hit_1000=bool((Es == 0).any()),
                frac_valid=float(valid), iters=int(r.nit), converged=bool(r.success),
                sec=time.time() - t)


def instance_b_setup(instance, horizon=8):
    model = build_qubo(instance, horizon, "domain-wall")
    qubo = DenseQubo(model)
    X = all_valid_codewords(model)
    E = qubo.energies(X)
    optimal = X[E == 0]
    groups = list(domain_wall_groups(model).values())
    return model, qubo, optimal, groups
