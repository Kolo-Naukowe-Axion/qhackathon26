"""Overnight VQE lab: published objectives/ansatz variants on the frozen catering bundles.

Reuses the repository engine (catering/methods/vqe.py: Problem, SectorAnsatz, block_pairs,
cvar_loss) unchanged; adds losses (Gibbs, staged/ascending CVaR, filtering VQE) and
QAOA-style cost-phase layers. Exact one-hot-sector simulation, adjoint gradients.
"""
import os, sys, json, math, time, hashlib
os.environ.setdefault("OMP_NUM_THREADS", "1"); os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
import numpy as np
from scipy.optimize import minimize
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
sys.path.insert(0, ROOT)
from catering.methods import vqe as V

CASES = {"cell": "output/catering-complete-cell-v3/quantum-qubo.json",
         **{s: f"output/catering-foundation-v3/{s}/quantum-qubo.json" for s in ("S0", "S1", "S2", "S3")}}
_PROB = {}
def problem(case):
    if case not in _PROB:
        _PROB[case] = V.Problem(json.load(open(os.path.join(ROOT, CASES[case]))))
        _PROB[case].sector
    return _PROB[case]

# ---------------- losses of the probabilities p (internal energy unit = w_U) -------------
def L_mean(E):
    return lambda p: (float(p @ E), E)
def L_cvar(E, a):
    return V.cvar_loss(E, a)
def L_gibbs(E, eta):
    e = E - E.min()           # shift for numerics only: gradient and argmin unchanged
    w = np.exp(-eta * e)
    def f(p):
        Z = float(p @ w)
        return -math.log(max(Z, 1e-300)), -w / max(Z, 1e-300)
    return f
def make_loss(E, cfg):
    k = cfg["loss"]
    if k == "mean": return L_mean(E)
    if k == "cvar": return L_cvar(E, cfg["alpha"])
    if k == "gibbs": return L_gibbs(E, cfg["eta"])
    raise ValueError(k)

# ---------------- ansatz ----------------
def build_ansatz(prob, cfg, rng):
    """cfg: layers, pairs (none|coupled|random|all), cross (cgiv|zz), inblock (giv|xy),
    cost_layers: k>0 inserts a QAOA cost-phase gate exp(-i g E/scale) before each sweep."""
    pairs = V.block_pairs(prob, cfg.get("pairs", "coupled"), rng)
    a = V.SectorAnsatz(prob, cfg.get("layers", 2), pairs, cfg.get("cross", "cgiv"), cfg.get("inblock", "giv"), cfg.get("z_phases", False))
    a.pairs = pairs
    if cfg.get("cost_phase"):
        # QAOA-style diagonal cost phase exp(-i t Ehat) at the start of every layer l = 1..L,
        # Ehat = sector energy rescaled to [0, 1]. The 'ph' gate applies exp(-0.5j t z), so z = 2 Ehat.
        Ehat = (a.E - a.E.min()) / (a.E.max() - a.E.min())
        z = 2.0 * Ehat
        n0 = sum(k - 1 for k in prob.dims)
        L = cfg.get("layers", 2)
        per = (len(a.gates) - n0) // L if L else 0
        assert n0 + per * L == len(a.gates)
        starts = {n0 + l * per for l in range(L)}
        new, p = [], len(a.w0)
        for idx, g in enumerate(a.gates):
            if idx in starts:
                for _ in range(cfg.get("cost_per_layer", 1)):
                    new.append(dict(kind="ph", p=p, z=z, qubits=(), label="cost")); p += 1
            new.append(g)
        a.gates = new; a.w0 = np.concatenate([a.w0, np.zeros(p - len(a.w0))]); a.n_params = len(a.w0); a.complex = True
    a.counts["cost"] = sum(g["label"] == "cost" for g in a.gates)
    bo = prob.block_of
    a.cross_couplers = int(sum(1 for i, j in zip(*np.nonzero(prob.Q)) if bo[i] != bo[j]))
    return a

def value_grad_amp(ans, w, f):
    """Adjoint gradient for a loss of the amplitudes: f(psi) -> (value, lam) with
    grad_k = 2 Re <lam| d psi / d w_k>."""
    psi = ans.state(w)
    val, lam = f(psi)
    lam = lam.astype(complex) if (ans.complex and not np.iscomplexobj(lam)) else lam
    grad = np.zeros_like(w)
    for g in reversed(ans.gates):
        t = w[g["p"]]
        ans._apply(g, -t, psi)
        grad[g["p"]] += 2.0 * ans._dot_deriv(g, t, lam, psi)
        ans._apply(g, -t, lam)
    return float(val), grad

# ---------------- training ----------------
def train(case, cfg, seed, shots=1024, trace=False):
    """cfg keys: ansatz params (see build_ansatz), init_noise, stages: list of dicts
    {loss: mean|cvar|gibbs|fvqe, alpha, eta, tau, maxfun, inner}, stop_maxprob."""
    prob = problem(case); sec = prob.sector
    rng = np.random.default_rng(seed)
    t0 = time.perf_counter()
    if cfg.get("keep") is not None:
        ans = pruned_ansatz(prob, cfg, rng, cfg.get("init_noise", 0.2))
    else:
        ans = build_ansatz(prob, cfg, rng)
    if cfg.get("keep") is not None:
        x = ans.x_start.copy()
    elif cfg.get("init") == "random":
        x = rng.uniform(0, 2 * np.pi, ans.n_params)
    else:
        x = ans.w0 + cfg.get("init_noise", 0.2) * rng.standard_normal(ans.n_params)
    E = ans.E; opt = sec["opt"]; valid = sec["valid"]
    stop_mp = cfg.get("stop_maxprob", 0.995)
    calls = dict(n=0); log = []
    def record(p, stage):
        if trace:
            log.append(dict(n=calls["n"], stage=stage, p_opt=float(p[opt].sum()), p_valid=float(p[valid].sum()),
                            mean=float(p @ E), maxp=float(p.max())))
    for si, st in enumerate(cfg["stages"]):
        budget = st.get("maxfun", 300)
        if st["loss"] == "fvqe":
            tau, inner = st["tau"], st.get("inner", 5)
            e = E - E.min()
            filt = np.exp(-tau * e)
            start = calls["n"]
            while calls["n"] - start < budget:
                psi_t = ans.state(x)
                if float(np.abs(psi_t).max() ** 2) > stop_mp: break
                phi = filt * psi_t; phi = phi / np.linalg.norm(phi)
                def fg(w):
                    calls["n"] += 1
                    def f(psi):
                        c = np.vdot(phi, psi)
                        return 1.0 - abs(c) ** 2, -c * phi
                    v, g = value_grad_amp(ans, w, f)
                    return v, g
                res = minimize(fg, x, jac=True, method="L-BFGS-B", options=dict(maxiter=inner, maxfun=inner + 3, ftol=1e-12, gtol=1e-9))
                x = res.x
                record(ans.probs(x), si)
            continue
        lossf = make_loss(E, st)
        def fg(w):
            calls["n"] += 1
            v, g = ans.value_grad(w, lossf)
            if trace: record(np.abs(ans.state(w)) ** 2, si)
            return v, g
        def cb(_):
            if getattr(ans, "last_maxprob", 0.0) > stop_mp: raise StopIteration
        if st.get("opt", "lbfgs") == "lbfgs":
            res = minimize(fg, x, jac=True, method="L-BFGS-B", callback=cb,
                           options=dict(maxiter=2000, maxfun=budget, ftol=1e-11, gtol=1e-7))
            x = res.x
        elif st["opt"] == "adam":
            m1 = np.zeros_like(x); m2 = np.zeros_like(x); lr = st.get("lr", 0.05)
            for it in range(1, budget + 1):
                _, g = fg(x)
                m1 = .9 * m1 + .1 * g; m2 = .999 * m2 + .001 * g * g
                x = x - lr * (m1 / (1 - .9 ** it)) / (np.sqrt(m2 / (1 - .999 ** it)) + 1e-8)
                if ans.last_maxprob > stop_mp: break
        if float((np.abs(ans.state(x)) ** 2).max()) > stop_mp: break
    t_opt = time.perf_counter() - t0
    ps = np.abs(ans.state(x)) ** 2
    draw = rng.choice(len(ps), size=shots, p=ps / ps.sum())
    hit = bool(opt[draw].any())
    mode = int(np.argmax(ps))
    cnot = (2 * sum(1 for g in ans.gates if g["kind"] in ("giv", "xy") and g.get("ctrl") is None)
            + 9 * sum(1 for g in ans.gates if g.get("ctrl") is not None) + 2 * ans.cross_couplers * ans.counts["cost"])
    out = dict(case=case, seed=seed, n_params=int(ans.n_params), n_pairs=len(ans.pairs), nfev=calls["n"],
               p_opt=float(ps[opt].sum()), p_valid=float(ps[valid].sum()), mode_is_opt=bool(opt[mode]) and ps[mode] > 0.5,
               mode_opt=bool(opt[mode]), mode_prob=float(ps[mode]), shot_hit_opt=hit, shot_valid=float(valid[draw].mean()),
               shot_opt_frac=float(opt[draw].mean()), mean_gap=float(ps @ E - E.min()), t=t_opt, cnot_est=cnot,
               hw_circuits=calls["n"] * (2 * int(ans.n_params) + 1), cross_kept=ans.counts.get("cross_kept"))
    if trace: out["trace"] = log
    return out

def job(args):
    name, case, cfg, seed = args
    try:
        r = train(case, cfg, seed)
    except Exception as ex:  # keep the grid alive, but record the failure
        r = dict(case=case, seed=seed, error=repr(ex)[:300])
    r["method"] = name; r["cfg"] = json.dumps(cfg, sort_keys=True)
    return r

def run_grid(jobs, out_csv, procs=9):
    import multiprocessing as mp, pandas as pd
    rows = []
    ctx = mp.get_context("fork")
    with ctx.Pool(procs) as pool:
        for r in pool.imap_unordered(job, jobs):
            rows.append(r)
            pd.DataFrame(rows).to_csv(out_csv, index=False)
    return pd.DataFrame(rows)

# ---------------- gradient-selected cross-block gates (ADAPT-style selection at the start state) ------------
def pruned_ansatz(prob, cfg, rng, x0_noise=0.2):
    """Build the full coupled ansatz, start at W + noise, compute |d CVaR_0.1 / d theta| for every cross-block
    (controlled-Givens) gate, keep the top fraction cfg['keep'] of them (all sweep gates kept)."""
    full = build_ansatz(prob, dict(cfg, cost_phase=False), rng)
    x0 = full.w0 + x0_noise * rng.standard_normal(full.n_params)
    _, g = full.value_grad(x0, V.cvar_loss(full.E, cfg.get("select_alpha", 0.1)))
    cross = [i for i, gt in enumerate(full.gates) if gt.get("ctrl") is not None]
    k = int(round(cfg["keep"] * len(cross)))
    top = set(sorted(cross, key=lambda i: -abs(g[full.gates[i]["p"]]))[:k])
    keep = [i for i, gt in enumerate(full.gates) if gt.get("ctrl") is None or i in top]
    new = []; w0 = []; xs = []
    for i in keep:
        gt = dict(full.gates[i]); w0.append(full.w0[gt["p"]]); xs.append(x0[gt["p"]]); gt["p"] = len(new); new.append(gt)
    full.gates = new; full.w0 = np.array(w0); full.n_params = len(new); full.x_start = np.array(xs)
    full.counts["cross_kept"] = k; full.counts["cross_pool"] = len(cross)
    return full
