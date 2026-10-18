"""VQE on the frozen catering v3 one-hot QUBO bundles (exact ideal simulation).

The cost is the literal bundle energy E(x); it is diagonal, so every quantity
below is computed from exact computational-basis probabilities. Three engines:

* ``product``   - RY on every qubit, no entangler. Bits are independent, so the
                  mean energy is the multilinear extension of the QUBO.
* ``block_hea`` - generic RY + CNOT-chain layers inside each one-hot block only
                  (blocks stay mutually unentangled). Leaves the one-hot sector.
* ``sector``    - gates that preserve one-hot in every block: Givens (or XY)
                  rotations between two choices of a block, controlled Givens
                  across blocks and diagonal ZZ / Z phases. The state is stored
                  only on the one-hot sector (prod_b k_b amplitudes), which is
                  exact for these gates, not an approximation.

Gradients are adjoint (one forward + one backward sweep). The contract labels
these runs ``quantum_simulation`` with exact expectations; no shots are used in
training. Final samples are drawn from the exact distribution.
"""
from __future__ import annotations

import itertools
import hashlib
import math
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path

import numpy as np
from scipy.optimize import minimize

# Capture at import, so edits on disk during optimization cannot relabel a run.
SOURCE_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


# --------------------------------------------------------------------------
# Problem data
# --------------------------------------------------------------------------
class Problem:
    def __init__(self, bundle):
        self.bundle = bundle
        n = self.n = len(bundle["variable_order"])
        self.const = int(bundle["constant"])
        self.lin = np.array([int(v) for v in bundle["linear"]], dtype=np.int64)
        Q = np.zeros((n, n), dtype=np.int64)
        for t in bundle["quadratic"]:
            Q[t["i"], t["j"]] = int(t["value"])
        self.Q = Q                       # upper triangular, i < j
        self.S = Q + Q.T                 # symmetric, zero diagonal
        self.obj_const = int(bundle["objective"]["constant"])
        self.obj_lin = np.array([int(v) for v in bundle["objective"]["linear"]], dtype=np.int64)
        Qo = np.zeros((n, n), dtype=np.int64)
        for t in bundle["objective"].get("quadratic", []):
            Qo[t["i"], t["j"]] = int(t["value"])
        self.Qo = Qo
        self.groups = [list(g["indices"]) for g in bundle["onehot_groups"]]
        covered = sorted(i for g in self.groups for i in g)
        if covered != list(range(n)):
            raise ValueError("onehot_groups must partition the variables")
        self.dims = [len(g) for g in self.groups]
        self.B = len(self.groups)
        self.block_of = np.empty(n, dtype=int)
        self.local_of = np.empty(n, dtype=int)
        for b, g in enumerate(self.groups):
            for l, i in enumerate(g):
                self.block_of[i], self.local_of[i] = b, l
        self.scale = float(bundle["objective"]["weights"]["U"])   # internal energy unit
        self._sector = None

    # exact integer energies for a batch of bit rows
    def energy_bits(self, X):
        X = np.asarray(X, dtype=np.int64)
        return self.const + X @ self.lin + np.einsum("si,ij,sj->s", X, self.Q, X)

    def objective_bits(self, X):
        X = np.asarray(X, dtype=np.int64)
        return self.obj_const + X @ self.obj_lin + np.einsum("si,ij,sj->s", X, self.Qo, X)

    @property
    def sector(self):
        """Choice table C (sector x B), bit rows X, energies E, validity mask."""
        if self._sector is None:
            C = np.array(list(itertools.product(*[range(k) for k in self.dims])), dtype=np.int16)
            X = np.zeros((len(C), self.n), dtype=np.int8)
            for b, g in enumerate(self.groups):
                X[np.arange(len(C)), np.array(g)[C[:, b]]] = 1
            E = self.energy_bits(X)
            valid = E == self.objective_bits(X)          # no penalty term active
            self._sector = dict(C=C, X=X, E=E, valid=valid, Emin=int(E.min()),
                                opt=E == E.min())
        return self._sector


# --------------------------------------------------------------------------
# Sector engine
# --------------------------------------------------------------------------
@dataclass
class Gate:
    kind: str            # 'giv' (real Givens), 'xy' (XX+YY), 'ph' (diagonal phase)
    p: int               # parameter index
    iu: np.ndarray = None
    iv: np.ndarray = None
    z: np.ndarray = None  # +-1 vector for 'ph'
    label: str = ""


class SectorAnsatz:
    """Sweeps of in-block two-choice rotations, optional cross-block entanglers.

    Layout for depth L:  sweep_0 (W-state cascade), then [cross_l, sweep_l] for l=1..L.
    A sweep applies rotations between adjacent choices (u,u+1), u = 0..k-2, in every block.
    cross = 'cgiv': for every chosen block pair (a<b), every choice p of a and every
            adjacent choice pair (u,u+1) of b, a Givens on b controlled by "block a chose p".
    cross = 'zz'  : exp(-i t/2 Z_p Z_q) for every qubit p in a and q in b.
    The state is a tensor over block choices; gates act on reshaped views (exact).
    """

    def __init__(self, prob: Problem, layers: int, pairs=(), cross="cgiv", inblock="giv",
                 z_phases=False):
        self.prob, self.layers, self.cross, self.inblock = prob, layers, cross, inblock
        dims = prob.dims
        self.dim = int(np.prod(dims))
        self.shapes = {}
        C = None

        def shape_for(b, ctrl):
            key = (b, ctrl)
            if key not in self.shapes:
                if ctrl is None:
                    shp = (int(np.prod(dims[:b])), dims[b], int(np.prod(dims[b + 1:])))
                else:
                    a = ctrl
                    shp = (int(np.prod(dims[:a])), dims[a], int(np.prod(dims[a + 1:b])), dims[b],
                           int(np.prod(dims[b + 1:])))
                self.shapes[key] = shp
            return self.shapes[key]

        zcache = {}

        def zvec(qs):
            nonlocal C
            if C is None:
                C = prob.sector["C"]
            z = np.ones(self.dim, dtype=np.int8)
            for q in qs:
                z = z * (1 - 2 * (C[:, prob.block_of[q]] == prob.local_of[q]).astype(np.int8))
            return z

        gates, w_init = [], []

        def add(kind, init=0.0, **kw):
            gates.append(dict(kind=kind, p=len(w_init), **kw))
            w_init.append(init)

        def sweep(first):
            for b, k in enumerate(dims):
                for u in range(k - 1):
                    init = 2 * math.acos(math.sqrt(1.0 / (k - u))) if first else 0.0
                    add("giv" if first else inblock, init, shape=shape_for(b, None),
                        sl=((slice(None), u, slice(None)), (slice(None), u + 1, slice(None))),
                        qubits=(prob.groups[b][u], prob.groups[b][u + 1]), ctrl=None,
                        label=f"s{b}:{u}")
            if z_phases and not first:
                for q in range(prob.n):
                    add("ph", 0.0, z=zvec([q]), qubits=(q,), label=f"z{q}")

        sweep(True)
        for _ in range(layers):
            for (a, b) in pairs:
                if cross == "cgiv":
                    for pch in range(dims[a]):
                        for u in range(dims[b] - 1):
                            s = slice(None)
                            add("giv", 0.0, shape=shape_for(b, a),
                                sl=((s, pch, s, u, s), (s, pch, s, u + 1, s)),
                                qubits=(prob.groups[b][u], prob.groups[b][u + 1]),
                                ctrl=prob.groups[a][pch], label=f"c{a}={pch}->{b}:{u}")
                elif cross == "zz":
                    for p in prob.groups[a]:
                        for q in prob.groups[b]:
                            add("ph", 0.0, z=zvec([p, q]), qubits=(p, q), label=f"zz{p},{q}")
                else:
                    raise ValueError(cross)
            sweep(False)
        self.gates, self.w0 = gates, np.array(w_init)
        self.complex = any(g["kind"] in ("xy", "ph") for g in gates)
        self.E = (prob.sector["E"] - prob.const) / prob.scale         # internal units
        self.n_params = len(self.w0)
        self.counts = {k: sum(g["kind"] == k for g in gates) for k in ("giv", "xy", "ph")}
        self.counts["cross_cgiv"] = sum(g["label"].startswith("c") for g in gates)

    # ----- gate application (in place on views) -----
    @staticmethod
    def _apply(g, t, psi):
        if g["kind"] == "ph":
            psi *= np.exp(-0.5j * t * g["z"])
            return
        v = psi.reshape(g["shape"])
        su, sv = g["sl"]
        a, b = v[su].copy(), v[sv].copy()
        c, s = math.cos(t / 2), math.sin(t / 2)
        if g["kind"] == "giv":
            v[su], v[sv] = c * a - s * b, s * a + c * b
        else:  # xy: exp(-i t/2 (XX+YY)/2) on the two-level subspace {u, v}
            v[su], v[sv] = c * a - 1j * s * b, -1j * s * a + c * b

    @staticmethod
    def _dot_deriv(g, t, lam, psi):
        """Re <lam| dU/dt |psi>  (psi = state before the gate)."""
        if g["kind"] == "ph":
            return float(np.real(np.vdot(lam, (-0.5j * g["z"]) * np.exp(-0.5j * t * g["z"]) * psi)))
        v, lv = psi.reshape(g["shape"]), lam.reshape(g["shape"])
        su, sv = g["sl"]
        a, b = v[su], v[sv]
        c, s = math.cos(t / 2), math.sin(t / 2)
        if g["kind"] == "giv":
            du, dv = 0.5 * (-s * a - c * b), 0.5 * (c * a - s * b)
        else:
            du, dv = 0.5 * (-s * a - 1j * c * b), 0.5 * (-1j * c * a - s * b)
        return float(np.real(np.vdot(lv[su], du) + np.vdot(lv[sv], dv)))

    def state(self, w):
        psi = np.zeros(self.dim, dtype=complex if self.complex else float)
        psi[0] = 1.0
        for g in self.gates:
            self._apply(g, w[g["p"]], psi)
        return psi

    def value_grad(self, w, loss=None):
        """Mean energy (default) or loss(p) -> (value, dvalue/dp) with exact adjoint gradient."""
        psi = self.state(w)
        p = np.abs(psi) ** 2
        self.last_maxprob = float(p.max())
        if loss is None:
            lam = self.E * psi
            val = float(p @ self.E)
        else:
            val, gdiag = loss(p)
            lam = gdiag * psi
        grad = np.zeros_like(w)
        for g in reversed(self.gates):
            t = w[g["p"]]
            self._apply(g, -t, psi)
            grad[g["p"]] += 2.0 * self._dot_deriv(g, t, lam, psi)
            self._apply(g, -t, lam)
        return float(val), grad

    def probs(self, w):
        return np.abs(self.state(w)) ** 2

    def sector_probs(self, w):
        return self.probs(w)


# --------------------------------------------------------------------------
# Product (RY on each qubit) engine
# --------------------------------------------------------------------------
class ProductAnsatz:
    def __init__(self, prob: Problem):
        self.prob = prob
        self.lin = prob.lin / prob.scale
        self.S = prob.S / prob.scale
        k = np.array([prob.dims[prob.block_of[i]] for i in range(prob.n)])
        self.w0 = 2 * np.arcsin(np.sqrt(1.0 / k))     # same marginals as the W start
        self.n_params = prob.n
        self.counts = {"ry": prob.n, "cnot": 0}

    def value_grad(self, w):
        p = np.sin(w / 2) ** 2
        val = float(self.lin @ p + 0.5 * p @ self.S @ p)
        g = (self.lin + self.S @ p) * 0.5 * np.sin(w)
        return val, g

    def bit_marginals(self, w):
        return np.sin(w / 2) ** 2

    def sector_probs(self, w):
        """Exact probability of every one-hot-sector state (sums to P(sector))."""
        p = self.bit_marginals(w)
        X = self.prob.sector["X"].astype(bool)
        logp = np.where(X, np.log(np.clip(p, 1e-300, None)), np.log(np.clip(1 - p, 1e-300, None)))
        return np.exp(logp.sum(1))

    def sample(self, w, shots, rng):
        p = self.bit_marginals(w)
        return (rng.random((shots, self.prob.n)) < p).astype(np.int8)


# --------------------------------------------------------------------------
# Block-local hardware-efficient engine (RY + CNOT chain inside each block)
# --------------------------------------------------------------------------
class BlockHEAAnsatz:
    def __init__(self, prob: Problem, layers: int):
        self.prob, self.layers = prob, layers
        self.blocks = []
        off = 0
        w0 = []
        for b, g in enumerate(prob.groups):
            k = len(g)
            npar = k * (layers + 1)
            init = np.zeros(npar)
            init[:k] = 2 * math.asin(math.sqrt(1.0 / k))
            w0.append(init)
            # diag data: bit table for 2^k states (qubit l = bit l of the index, MSB = local 0)
            idx = np.arange(2 ** k)
            bits = ((idx[:, None] >> (k - 1 - np.arange(k))[None, :]) & 1).astype(np.int64)
            gi = np.array(g)
            within = bits @ prob.lin[gi] + np.einsum("si,ij,sj->s", bits, prob.Q[np.ix_(gi, gi)], bits)
            self.blocks.append(dict(b=b, k=k, off=off, npar=npar, idx=gi, bits=bits,
                                    within=within / prob.scale))
            off += npar
        self.w0 = np.concatenate(w0)
        self.n_params = off
        self.S = prob.S / prob.scale
        self.counts = {"ry": off, "cnot": sum((bl["k"] - 1) * layers for bl in self.blocks)}

    @staticmethod
    def _ry_apply(psi, k, q, t):
        psi = psi.reshape(2 ** q, 2, -1)
        c, s = math.cos(t / 2), math.sin(t / 2)
        a, b = psi[:, 0, :].copy(), psi[:, 1, :].copy()
        psi[:, 0, :], psi[:, 1, :] = c * a - s * b, s * a + c * b

    @staticmethod
    def _ry_deriv(psi, k, q, t):
        psi = psi.reshape(2 ** q, 2, -1)
        c, s = math.cos(t / 2), math.sin(t / 2)
        a, b = psi[:, 0, :], psi[:, 1, :]
        out = np.empty_like(psi)
        out[:, 0, :], out[:, 1, :] = 0.5 * (-s * a - c * b), 0.5 * (c * a - s * b)
        return out.reshape(-1)

    @staticmethod
    def _cnot(psi, k, ctl, tgt):
        v = psi.reshape([2] * k)
        sl = [slice(None)] * k
        sl[ctl] = 1
        sub = v[tuple(sl)]
        ax = tgt if tgt < ctl else tgt - 1
        sub[...] = np.flip(sub, axis=ax).copy()

    def _ops(self, k):
        ops = [("ry", q, q) for q in range(k)]
        pi = k
        for _ in range(self.layers):
            ops += [("cx", q, q + 1) for q in range(k - 1)]
            ops += [("ry", q, pi + q) for q in range(k)]
            pi += k
        return ops

    def _block_state(self, bl, wb):
        k = bl["k"]
        psi = np.zeros(2 ** k)
        psi[0] = 1.0
        for op, q, p in self._ops(k):
            if op == "ry":
                self._ry_apply(psi, k, q, wb[p])
            else:
                self._cnot(psi, k, q, p)
        return psi

    def block_probs(self, w):
        return [self._block_state(bl, w[bl["off"]:bl["off"] + bl["npar"]]) ** 2 for bl in self.blocks]

    def bit_marginals(self, w, P=None):
        P = P or self.block_probs(w)
        m = np.zeros(self.prob.n)
        for bl, pb in zip(self.blocks, P):
            m[bl["idx"]] = pb @ bl["bits"]
        return m

    def value_grad(self, w):
        states = [self._block_state(bl, w[bl["off"]:bl["off"] + bl["npar"]]) for bl in self.blocks]
        P = [s ** 2 for s in states]
        m = self.bit_marginals(w, P)
        bo = self.prob.block_of
        cross = self.S * (bo[:, None] != bo[None, :])
        field_ = cross @ m                                  # mean field from other blocks
        val = 0.5 * m @ cross @ m + sum(pb @ bl["within"] for bl, pb in zip(self.blocks, P))
        grad = np.zeros_like(w)
        for bl, psi in zip(self.blocks, states):
            k, wb = bl["k"], w[bl["off"]:bl["off"] + bl["npar"]]
            D = bl["within"] + bl["bits"] @ field_[bl["idx"]]    # effective diagonal
            lam = D * psi
            ops = self._ops(k)
            g = np.zeros(bl["npar"])
            for op, q, p in reversed(ops):
                if op == "ry":
                    self._ry_apply(psi, k, q, -wb[p])
                    g[p] = 2.0 * lam @ self._ry_deriv(psi, k, q, wb[p])
                    self._ry_apply(lam, k, q, -wb[p])
                else:
                    self._cnot(psi, k, q, p)
                    self._cnot(lam, k, q, p)
            grad[bl["off"]:bl["off"] + bl["npar"]] = g
        return float(val), grad

    def sector_probs(self, w):
        P = self.block_probs(w)
        C = self.prob.sector["C"]
        out = np.ones(len(C))
        for bl, pb in zip(self.blocks, P):
            k = bl["k"]
            onehot_index = np.array([1 << (k - 1 - l) for l in range(k)])   # local l -> state index
            out *= pb[onehot_index[C[:, bl["b"]]]]
        return out

    def sample(self, w, shots, rng):
        P = self.block_probs(w)
        X = np.zeros((shots, self.prob.n), dtype=np.int8)
        for bl, pb in zip(self.blocks, P):
            s = rng.choice(len(pb), size=shots, p=pb / pb.sum())
            X[:, bl["idx"]] = bl["bits"][s]
        return X


# --------------------------------------------------------------------------
# Runner
# --------------------------------------------------------------------------
def block_pairs(prob: Problem, mode: str, rng=None):
    allp = [(a, b) for a in range(prob.B) for b in range(a + 1, prob.B)]
    bo = prob.block_of
    coupled = sorted({(min(bo[i], bo[j]), max(bo[i], bo[j]))
                      for i, j in zip(*np.nonzero(prob.Q)) if bo[i] != bo[j]})
    if mode == "none":
        return []
    if mode == "coupled":
        return coupled
    if mode == "all":
        return allp
    if mode == "random":
        idx = rng.choice(len(allp), size=len(coupled), replace=False)
        return [allp[i] for i in sorted(idx)]
    raise ValueError(mode)


@dataclass
class Spec:
    ansatz: str                  # product | block_hea | sector
    layers: int = 1
    pairs: str = "none"          # none | coupled | random | all   (sector only)
    cross: str = "cgiv"          # cgiv | zz
    inblock: str = "giv"         # giv | xy
    z_phases: bool = False
    init_noise: float = 0.2
    init: str = "w"              # w (W-state marginals + noise) | random (uniform angles)
    maxiter: int = 2000
    stop_maxprob: float = 0.995  # sector engine: stop once one plan holds this probability
    loss: str = "mean"           # mean | cvar | gibbs | cvar_gibbs  (non-mean: exact distribution, sector engine)
    alpha: float = 0.1
    eta: float = 100.0           # Gibbs inverse temperature, energies in units of w_U (gibbs, cvar_gibbs)
    stage1_budget: int = 150     # cvar_gibbs: loss evaluations of the CVaR stage before switching to Gibbs
    optimizer: str = "lbfgs"     # lbfgs | adam | nft | spsa | cobyla
    budget: int = 0              # max loss evaluations (0 = optimizer default)
    train_shots: int = 0         # 0 = exact expectations; >0 = shot estimates (spsa/cobyla/nft)
    lr: float = 0.05             # adam step

    def name(self):
        if self.ansatz == "product":
            return "A0-product"
        if self.ansatz == "block_hea":
            return f"A1-blockHEA-L{self.layers}"
        tag = {"none": "A2-block", "coupled": "A3-coupled", "random": "A3r-random", "all": "A4-all"}[self.pairs]
        extra = "" if self.pairs == "none" else f"-{self.cross}"
        extra += "" if self.inblock == "giv" else f"-{self.inblock}"
        extra += "-zph" if self.z_phases else ""
        return f"{tag}{extra}-L{self.layers}"

    def tag(self):
        t = self.name() + f"|{self.optimizer}|{self.loss}"
        t += f"{self.alpha}" if self.loss in ("cvar", "cvar_gibbs") else ""
        t += f"-eta{self.eta:g}" if self.loss in ("gibbs", "cvar_gibbs") else ""
        t += f"|shots{self.train_shots}" if self.train_shots else "|exact"
        t += f"|init-{self.init}{self.init_noise if self.init == 'w' else ''}"
        return t


def build(prob, spec: Spec, rng):
    if spec.ansatz == "product":
        return ProductAnsatz(prob)
    if spec.ansatz == "block_hea":
        return BlockHEAAnsatz(prob, spec.layers)
    pairs = block_pairs(prob, spec.pairs, rng)
    a = SectorAnsatz(prob, spec.layers, pairs, spec.cross, spec.inblock, spec.z_phases)
    a.pairs = pairs
    return a


def cvar_loss(energies, alpha):
    """Exact lower-tail CVaR and its probability derivative (away from cut kinks).

    The fractional boundary state matters: averaging ceil(alpha * states)
    energies would weight states rather than probability mass.
    """
    if not 0 < alpha <= 1:
        raise ValueError("CVaR alpha must be in (0, 1]")
    energies = np.asarray(energies)
    order = np.argsort(energies, kind="stable")
    Es = energies[order]

    def loss(p):
        ps = p[order]
        cum = np.cumsum(ps)
        take = np.clip(alpha - (cum - ps), 0.0, ps)
        val = float(take @ Es) / alpha
        k = int(np.searchsorted(cum, alpha))
        Ecut = Es[min(k, len(Es) - 1)]
        grad = np.zeros_like(p)
        grad[order[:k]] = (Es[:k] - Ecut) / alpha
        return val, grad
    return loss


def gibbs_loss(energies, eta):
    """Gibbs objective -log sum_x p(x) exp(-eta E(x)) (Li et al., PRR 2, 023074, 2020) and dloss/dp.

    Computed as eta*m - log sum_x p(x) exp(-eta (E(x) - m)) with m = min E for numerical
    stability only. The shift adds a constant to the value: gradients and L-BFGS steps are
    unchanged, but scipy's relative ftol stopping test sees the offset and can stop earlier.
    """
    if not eta > 0:
        raise ValueError("Gibbs eta must be positive")
    energies = np.asarray(energies, dtype=float)
    m = float(energies.min())
    w = np.exp(-eta * (energies - m))

    def loss(p):
        Z = max(float(p @ w), 1e-300)
        return eta * m - math.log(Z), -w / Z
    return loss


def make_loss(spec, energies, stage=None):
    """Exact probability loss for the sector engine; None means the plain mean energy."""
    kind = spec.loss if stage is None else stage
    if kind == "cvar":
        return cvar_loss(energies, spec.alpha)
    if kind == "gibbs":
        return gibbs_loss(energies, spec.eta)
    return None


def validate_spec(spec, shots):
    if spec.ansatz not in {"product", "block_hea", "sector"}:
        raise ValueError("Unknown ansatz")
    if spec.loss not in {"mean", "cvar", "gibbs", "cvar_gibbs"}:
        raise ValueError("Unknown loss")
    if spec.loss in {"gibbs", "cvar_gibbs"} and (spec.ansatz != "sector" or spec.train_shots
                                                  or spec.optimizer not in {"lbfgs", "adam"}):
        raise ValueError("Gibbs losses use the exact sector distribution with an adjoint optimizer")
    if spec.loss == "cvar_gibbs" and spec.stage1_budget < 1:
        raise ValueError("cvar_gibbs needs a positive CVaR stage budget")
    if not 0 < spec.alpha <= 1:
        raise ValueError("CVaR alpha must be in (0, 1]")
    if shots <= 0 or spec.train_shots < 0 or spec.budget < 0 or spec.layers < 0:
        raise ValueError("Invalid shots, budget or layers")
    if spec.train_shots and spec.optimizer in {"lbfgs", "adam"}:
        raise ValueError("Adjoint optimizers use exact expectations; choose a shot-based optimizer")
    if spec.optimizer == "nft" and (spec.loss != "mean" or spec.ansatz == "sector"):
        raise ValueError("Three-point NFT needs a single-frequency mean loss; sector/CVaR is unsupported")


def replay_parameters(bundle, spec, seed, parameters):
    """Rebuild the exact final distribution without optimization or sampling.

    The seed also fixes random block pairs, so parameters alone are insufficient.
    """
    prob = Problem(bundle)
    ans = build(prob, spec, np.random.default_rng(seed))
    parameters = np.asarray(parameters, dtype=float)
    if parameters.shape != (ans.n_params,) or not np.isfinite(parameters).all():
        raise ValueError("Parameter vector does not match the circuit")
    return ans.sector_probs(parameters)


def run(prob: Problem, spec: Spec, seed: int, shots: int = 1024):
    validate_spec(spec, shots)
    rng = np.random.default_rng(seed)
    t0 = time.perf_counter()
    ans = build(prob, spec, rng)
    t_build = time.perf_counter() - t0
    if spec.init == "random":
        w0 = rng.uniform(0, 2 * np.pi, ans.n_params)
    else:
        w0 = ans.w0 + spec.init_noise * rng.standard_normal(ans.n_params)
    calls = {"n": 0, "grad": 0}
    if spec.loss == "cvar" and not spec.train_shots:
        if not isinstance(ans, SectorAnsatz):
            raise ValueError("exact CVaR needs the full distribution: sector engine only")
    staged = spec.loss == "cvar_gibbs"
    loss_fn = (None if spec.train_shots or spec.loss == "mean"
               else make_loss(spec, ans.E, "cvar" if staged else None))

    def fg(w):                                   # exact loss + adjoint gradient
        calls["n"] += 1; calls["grad"] += 1
        return ans.value_grad(w, loss_fn) if loss_fn else ans.value_grad(w)

    sec = prob.sector

    def shot_loss(w):
        ps = ans.sector_probs(w)
        if isinstance(ans, SectorAnsatz):
            draw = rng.choice(len(ps), size=spec.train_shots, p=ps / ps.sum())
            Es = (sec["E"][draw] - prob.const) / prob.scale
        else:
            X = ans.sample(w, spec.train_shots, rng)
            Es = (prob.energy_bits(X) - prob.const) / prob.scale
        if spec.loss == "cvar":
            m = max(1, int(math.ceil(spec.alpha * len(Es))))
            return float(np.sort(Es)[:m].mean())
        return float(Es.mean())

    def fval(w):                                 # loss value only (exact or shots)
        calls["n"] += 1
        if spec.train_shots:
            return shot_loss(w)
        if loss_fn is None:
            return ans.value_grad(w)[0] if not isinstance(ans, SectorAnsatz) else float(ans.probs(w) @ ans.E)
        return loss_fn(ans.probs(w))[0]

    def stop_now(w):
        if not isinstance(ans, SectorAnsatz):
            return False
        return float(ans.probs(w).max()) > spec.stop_maxprob

    def cb(intermediate_result):
        if getattr(ans, "last_maxprob", 0.0) > spec.stop_maxprob:
            raise StopIteration

    t1 = time.perf_counter()
    budget = spec.budget or 4000
    converged = False
    if spec.optimizer == "lbfgs":
        first = min(spec.stage1_budget, budget) if staged else budget
        res = minimize(fg, w0, jac=True, method="L-BFGS-B", callback=cb,
                       options=dict(maxiter=spec.maxiter, maxfun=first, ftol=1e-11, gtol=1e-7))
        x, message, nit = res.x, str(res.message), int(res.nit)
        converged = bool(res.success)
        if staged and calls["n"] < budget and getattr(ans, "last_maxprob", 0.0) <= spec.stop_maxprob:
            loss_fn = make_loss(spec, ans.E, "gibbs")        # stage 2: concentrate the found optimum
            res = minimize(fg, x, jac=True, method="L-BFGS-B", callback=cb,
                           options=dict(maxiter=spec.maxiter, maxfun=budget - calls["n"], ftol=1e-11, gtol=1e-7))
            x, message, nit = res.x, "stage2: " + str(res.message), nit + int(res.nit)
            converged = bool(res.success)
    elif spec.optimizer == "adam":
        x, m1, m2 = w0.copy(), np.zeros_like(w0), np.zeros_like(w0)
        b1, b2, eps = 0.9, 0.999, 1e-8
        message = "budget"
        for it in range(1, budget + 1):
            if staged and it == spec.stage1_budget + 1:
                loss_fn = make_loss(spec, ans.E, "gibbs")
            _, g = fg(x)
            m1 = b1 * m1 + (1 - b1) * g; m2 = b2 * m2 + (1 - b2) * g * g
            x = x - spec.lr * (m1 / (1 - b1 ** it)) / (np.sqrt(m2 / (1 - b2 ** it)) + eps)
            if getattr(ans, "last_maxprob", 0.0) > spec.stop_maxprob:
                message = "maxprob"; break
        nit = it
    elif spec.optimizer == "nft":
        # Single-frequency mean losses only (validated above).
        x = w0.copy(); f0 = fval(x); message = "budget"; nit = 0
        while calls["n"] + 2 <= budget:
            for j in rng.permutation(len(x)):
                if calls["n"] + 2 > budget:
                    break
                t = x[j]
                xp, xm = x.copy(), x.copy(); xp[j] = t + np.pi / 2; xm[j] = t - np.pi / 2
                fp, fm = fval(xp), fval(xm)
                a = 0.5 * (fp + fm)
                bcos, csin = f0 - a, 0.5 * (fp - fm)       # f(t+d) = a + bcos cos d + csin sin d
                d = math.atan2(-csin, -bcos)
                x[j] = t + d
                f0 = a - math.hypot(bcos, csin) if not spec.train_shots else fval(x)
            nit += 1
            if stop_now(x):
                message = "maxprob"; break
    elif spec.optimizer == "spsa":
        x = w0.copy(); message = "budget"; nit = 0
        c0, A, alpha_, gamma_ = 0.1, 10.0, 0.602, 0.101
        # calibrate a so the first step has size ~0.2 rad (5 probe pairs)
        mags = []
        for _ in range(5):
            dlt = rng.choice([-1.0, 1.0], len(x))
            mags.append(abs(fval(x + c0 * dlt) - fval(x - c0 * dlt)) / (2 * c0))
        a0 = 0.2 * (A + 1) ** alpha_ / max(np.mean(mags), 1e-12)
        k = 0
        while calls["n"] + 2 <= budget:
            ak, ck = a0 / (k + 1 + A) ** alpha_, c0 / (k + 1) ** gamma_
            dlt = rng.choice([-1.0, 1.0], len(x))
            gk = (fval(x + ck * dlt) - fval(x - ck * dlt)) / (2 * ck) * dlt
            x = x - ak * gk
            k += 1
            if k % 25 == 0 and stop_now(x):
                message = "maxprob"; break
        nit = k
    elif spec.optimizer == "cobyla":
        res = minimize(fval, w0, method="COBYLA", options=dict(maxiter=budget, rhobeg=0.5, tol=1e-8))
        x, message, nit = res.x, str(res.message), int(getattr(res, "nfev", 0))
        converged = bool(res.success)
    else:
        raise ValueError(spec.optimizer)

    class _R:  # minimal result shim for the reporting code below
        pass
    res = _R(); res.x = x; res.nit = nit; res.success = converged; res.message = message
    res.fun = (ans.value_grad(x)[0] if not isinstance(ans, SectorAnsatz) else float(ans.probs(x) @ ans.E))
    t_opt = time.perf_counter() - t1
    ps = ans.sector_probs(res.x)
    p_sector = float(ps.sum())
    p_opt = float(ps[sec["opt"]].sum())
    p_valid = float(ps[sec["valid"]].sum())
    # final samples from the exact distribution
    if isinstance(ans, SectorAnsatz):
        draw = rng.choice(len(ps), size=shots, p=ps / ps.sum())
        X = sec["X"][draw]
    else:
        X = ans.sample(res.x, shots, rng)
    E = prob.energy_bits(X)
    Eo = prob.objective_bits(X)
    onehot = np.all([X[:, g].sum(1) == 1 for g in prob.groups], axis=0)
    valid = onehot & (E == Eo)
    mode = int(np.argmax(ps))
    mean_E = float(res.fun) * prob.scale + prob.const
    return dict(spec=spec.name(), seed=seed, n_params=int(ans.n_params),
                gates=getattr(ans, "counts", {}), n_pairs=len(getattr(ans, "pairs", [])),
                mean_energy=mean_E, gap_mean=mean_E - sec["Emin"],
                p_opt=p_opt, p_valid=p_valid, p_sector=p_sector,
                mode_is_opt=bool(sec["opt"][mode]) and ps[mode] > 0.5, mode_prob=float(ps[mode]),
                shots=shots, shot_valid_rate=float(valid.mean()),
                shot_hit_opt=bool((valid & (E == sec["Emin"])).any()),
                best_valid_shot_energy=(int(E[valid].min()) if valid.any() else None),
                Emin=sec["Emin"], nfev=calls["n"], n_grad=calls["grad"], nit=int(res.nit), converged=bool(res.success),
                stop=str(res.message)[:60], tag=spec.tag(), optimizer=spec.optimizer, loss=spec.loss,
                alpha=spec.alpha, train_shots=spec.train_shots,
                train_shots_total=(calls["n"] * spec.train_shots),
                hw_circuits_equiv=(calls["grad"] * (2 * int(ans.n_params) + 1) + (calls["n"] - calls["grad"])),
                t_build=t_build, t_opt=t_opt, x=res.x, _samples=X)


# --------------------------------------------------------------------------
# Contract adapter (docs/CATERING_SOLVER_CONTRACT.md section 6)
# --------------------------------------------------------------------------
def solve_qubo(bundle, budget=None, method_config=None, output_dir=None):
    """Run one VQE configuration and return a normalized MethodResult.

    method_config: Spec fields (ansatz, layers, pairs, cross, inblock, loss, alpha,
    optimizer, budget, train_shots, init, init_noise) plus 'seed'.
    budget: dict with optional 'shots' (final samples, default 1024) and
    'max_objective_evaluations' (overrides Spec.budget).
    output_dir: fresh directory for result.json and its external hash manifest.
    Missing method_config selects RECOMMENDED; supplied configurations are explicit.
    """
    import platform
    from collections import Counter
    from pathlib import Path
    from catering.contracts import method_result, save_json
    budget = dict(budget or {})
    cfg = dict(RECOMMENDED if method_config is None else method_config)
    seed = int(cfg.pop("seed", 0))
    if budget.get("max_objective_evaluations"):
        cfg["budget"] = int(budget["max_objective_evaluations"])
    spec = Spec(**cfg)
    target = None
    if output_dir is not None:
        if Path(output_dir).exists():
            raise ValueError('Choose a fresh output directory; existing evidence is never overwritten')
        target = Path(output_dir) / 'result.json'
    prob = Problem(bundle)
    t0 = time.perf_counter()
    r = run(prob, spec, seed, shots=int(budget.get("shots", 1024)))
    total = time.perf_counter() - t0
    counts = Counter(tuple(int(v) for v in row) for row in r["_samples"])
    samples = [dict(bits=list(bits), count=m, reported_energy=str(int(prob.energy_bits([bits])[0])))
               for bits, m in sorted(counts.items(), key=lambda kv: -kv[1])]
    res = method_result(bundle, "catering-vqe", samples,
                        timings=dict(build_s=r["t_build"], optimize_s=r["t_opt"], total_s=total),
                        work=dict(objective_evaluations=r["nfev"], adjoint_gradient_evaluations=r["n_grad"],
                                  training_shots_total=r["train_shots_total"],
                                  legacy_two_shift_circuit_estimate=r["hw_circuits_equiv"],
                                  final_sample_shots=r["shots"], repeats=1, seed=seed))
    res.update(execution_kind="quantum_simulation", method_version=2,
               configuration=dict(spec=asdict(spec), tag=spec.tag(), n_params=r["n_params"], gates=r["gates"],
                                  expectation="exact ideal" if not spec.train_shots else f"{spec.train_shots}-shot estimates",
                                  gradient="adjoint" if r["n_grad"] else "none (gradient-free)",
                                  initializer=f"{spec.init} (no reference/teacher state)", seed_supported=True, repair=False),
               optimized_parameters=np.asarray(r["x"]).tolist(),
               adapter_sha256=SOURCE_SHA256,
               optimizer_status=dict(converged=r["converged"], stop=r["stop"]),
               environment=dict(python=platform.python_version(), numpy=np.__version__,
                                processor=platform.machine(), backend="numpy one-hot-sector / block statevector"),
               exact_distribution=dict(p_optimal=r["p_opt"], p_valid=r["p_valid"], p_onehot_sector=r["p_sector"],
                                       mean_energy=r["mean_energy"], sector_minimum_energy=r["Emin"],
                                       note="computed from the exact simulated state; reference minimum used only for reporting"))
    res["configuration"]["resource_note"] = (
        "Exact simulator adjoint gradients. Legacy 2P+1 arithmetic is not a validated "
        "hardware circuit count: Givens generators can require four shifts, and CVaR "
        "needs probability derivatives rather than shifting the scalar CVaR loss.")
    if target:
        target.parent.mkdir(parents=True)
        save_json(target, res)
        save_json(target.parent / 'artifacts.json', dict(files={
            'result.json': hashlib.sha256(target.read_bytes()).hexdigest()}))
    return res


RECOMMENDED = dict(ansatz="sector", pairs="coupled", cross="cgiv", inblock="giv", layers=2,
                   loss="cvar", alpha=0.1, optimizer="lbfgs", init="w", init_noise=0.2, seed=0)

# CVaR finds the optimum, then the Gibbs loss concentrates it (P(optimum) ~0.995 instead of ~0.12-0.18).
# Evidence: output/catering-methods/vqe/E6-concentration (dev cell/S0/S1, predeclared held-out S2/S3).
RECOMMENDED_CONCENTRATED = dict(RECOMMENDED, loss="cvar_gibbs", eta=100.0, stage1_budget=150, budget=300)
