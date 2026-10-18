"""Finite-shot training of sector ansatze (S shots per circuit).

spsa      : SPSA on a loss estimated from S samples (CVaR or Gibbs).
ps-adam   : Adam on the Gibbs loss. Gradient = exact adjoint gradient of <W> plus Gaussian
            noise with the variance of the 4-term parameter-shift estimator at S shots per
            shifted circuit (sum c_r^2 = 0.375, Var(w) evaluated at the current state):
            a noise-model EMULATION of hardware parameter shift, not a per-circuit simulation.
Shift m for exp(-eta (E - m)) = lowest energy sampled so far (known on hardware).
Stop when one plan holds >= stop_freq of the S samples of the current state.
"""
import sys, os, math, time, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import lab

def train_shots(case, cfg, seed, S=1024, method="spsa", loss="gibbs", eta=30, alpha=0.1,
                iters=2000, lr=0.05, stop_freq=0.95, final_shots=1024):
    prob = lab.problem(case); sec = prob.sector
    rng = np.random.default_rng(seed)
    ans = lab.build_ansatz(prob, cfg, rng)
    x = ans.w0 + cfg.get("init_noise", 0.2) * rng.standard_normal(ans.n_params)
    E = ans.E; opt = sec["opt"]; valid = sec["valid"]
    best = [np.inf]; circuits = [0]; t0 = time.perf_counter()
    def sample(w):
        p = np.abs(ans.state(w)) ** 2
        d = rng.choice(len(p), size=S, p=p / p.sum()); circuits[0] += 1
        best[0] = min(best[0], float(E[d].min()))
        return p, d
    def est(d, m):
        Es = E[d]
        if loss == "cvar":
            k = max(1, int(math.ceil(alpha * S))); return float(np.sort(Es)[:k].mean())
        return -math.log(max(float(np.mean(np.exp(-eta * (Es - m)))), 1e-300))
    it = 0; stop = "iters"
    if method == "spsa":
        c0, A, a_, g_ = 0.1, 10.0, 0.602, 0.101
        _, d = sample(x); m = best[0]
        mags = []
        for _ in range(5):
            dl = rng.choice([-1.0, 1.0], len(x))
            _, dp = sample(x + c0 * dl); _, dm = sample(x - c0 * dl)
            mags.append(abs(est(dp, m) - est(dm, m)) / (2 * c0))
        a0 = 0.2 * (A + 1) ** a_ / max(np.mean(mags), 1e-12)
        for it in range(1, iters + 1):
            m = best[0]
            ak, ck = a0 / (it + A) ** a_, c0 / it ** g_
            dl = rng.choice([-1.0, 1.0], len(x))
            _, dp = sample(x + ck * dl); _, dm = sample(x - ck * dl)
            x = x - ak * (est(dp, m) - est(dm, m)) / (2 * ck) * dl
            if it % 10 == 0:
                _, d = sample(x)
                if np.bincount(d).max() >= stop_freq * S: stop = "freq"; break
    elif method == "ps-adam":
        m1 = np.zeros_like(x); m2 = np.zeros_like(x)
        for it in range(1, iters + 1):
            p, d = sample(x); m = best[0]
            if np.bincount(d).max() >= stop_freq * S: stop = "freq"; break
            m = float(E[d].min())          # per-step shift: -grad log Z is shift-invariant, and Zhat >= 1/S
            w = np.exp(-eta * (E - m))
            Zhat = float(np.mean(w[d]))
            _, gZ = ans.value_grad(x, lambda pp: (float(pp @ w), w))
            varw = float(p @ (w * w) - (p @ w) ** 2)
            gZ = gZ + math.sqrt(0.375 * max(varw, 0.0) / S) * rng.standard_normal(len(x))
            circuits[0] += 4 * len(x)
            g = -gZ / Zhat
            m1 = .9 * m1 + .1 * g; m2 = .999 * m2 + .001 * g * g
            x = x - lr * (m1 / (1 - .9 ** it)) / (np.sqrt(m2 / (1 - .999 ** it)) + 1e-8)
    ps = np.abs(ans.state(x)) ** 2
    d = rng.choice(len(ps), size=final_shots, p=ps / ps.sum())
    mode = int(np.argmax(ps))
    return dict(case=case, seed=seed, method=method, loss=loss, eta=eta, alpha=alpha, S=S, iters=it, stop=stop,
                circuits=circuits[0], shots_total=circuits[0] * S, n_params=int(ans.n_params),
                p_opt=float(ps[opt].sum()), p_valid=float(ps[valid].sum()), mode_is_opt=bool(opt[mode]) and ps[mode] > 0.5,
                shot_hit_opt=bool(opt[d].any()), best_sampled_is_opt=bool(best[0] <= E.min() + 1e-12), t=time.perf_counter() - t0)

def job(a):
    name, case, cfg, seed, kw = a
    try: r = train_shots(case, cfg, seed, **kw)
    except Exception as ex: r = dict(case=case, seed=seed, error=repr(ex)[:300])
    r["name"] = name; r["cfg"] = json.dumps(cfg); return r

if __name__ == "__main__":
    for kw in (dict(method="spsa", loss="gibbs", iters=600), dict(method="spsa", loss="cvar", iters=600), dict(method="ps-adam", loss="gibbs", iters=200)):
        r = train_shots("cell", dict(layers=1, pairs="none"), 0, **kw)
        print({k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()})

def train_shots_staged(case, cfg, seed, stages, S=1024, lr=0.05, stop_freq=0.95, final_shots=1024):
    """Adam with emulated parameter-shift gradients; stages = [dict(loss=cvar|gibbs, alpha|eta, iters)].
    CVaR gradient = grad <G> with G(x) = (E(x) - VaR)/alpha for E(x) < VaR (VaR = sampled alpha-quantile), else 0;
    Gibbs gradient = -grad <W> / What with W = exp(-eta (E - m)). Noise: 4-term shift rule, S shots per circuit."""
    prob = lab.problem(case); sec = prob.sector
    rng = np.random.default_rng(seed)
    ans = lab.build_ansatz(prob, cfg, rng)
    x = ans.w0 + cfg.get("init_noise", 0.2) * rng.standard_normal(ans.n_params)
    E = ans.E; opt = sec["opt"]; valid = sec["valid"]
    best = np.inf; circuits = 0; t0 = time.perf_counter(); it_total = 0; stop = "iters"; best_plan_hits = False
    m1 = np.zeros_like(x); m2 = np.zeros_like(x); k = 0; clips = 0; stage_end = []
    for st in stages:
        for it in range(st["iters"]):
            p = np.abs(ans.state(x)) ** 2
            d = rng.choice(len(p), size=S, p=p / p.sum()); circuits += 1; it_total += 1
            best = min(best, float(E[d].min())); best_plan_hits |= bool(opt[d].any())
            if np.bincount(d).max() >= stop_freq * S: stop = "freq"; break
            if st["loss"] == "cvar":
                a = st["alpha"]; var = float(np.quantile(E[d], a))
                G = np.where(E < var, (E - var) / a, 0.0)
                _, g = ans.value_grad(x, lambda pp: (float(pp @ G), G))
                vg = float(p @ (G * G) - (p @ G) ** 2)
                g = g + math.sqrt(0.375 * max(vg, 0) / S) * rng.standard_normal(len(x))
            else:
                # gradient of -log Z with Z = <exp(-eta (E - shift))>: shift-invariant. Exact part uses the
                # sector minimum b (weights <= 1, no overflow); Zhat uses the batch minimum mt (Zhat >= 1/S);
                # the factor exp(eta (mt - b)) / Zhat is applied in log scale; norm clipped at 1e3 if it would overflow.
                eta_ = st["eta"]; mt = float(E[d].min()); b = float(E.min())
                wb = np.exp(-eta_ * (E - b))
                Zhat_mt = float(np.mean(np.exp(-eta_ * (E[d] - mt))))
                _, gZ = ans.value_grad(x, lambda pp: (float(pp @ wb), wb))
                vw = float(p @ (wb * wb) - (p @ wb) ** 2)
                gb = gZ + math.sqrt(0.375 * max(vw, 0) / S) * rng.standard_normal(len(x))
                logscale = eta_ * (mt - b) - math.log(Zhat_mt)
                nrm = float(np.linalg.norm(gb))
                if nrm > 0 and math.log(nrm) + logscale > math.log(1e3):
                    g = -gb * (1e3 / nrm); clips += 1
                else:
                    g = -gb * math.exp(logscale)
            circuits += 4 * len(x); k += 1
            m1 = .9 * m1 + .1 * g; m2 = .999 * m2 + .001 * g * g
            x = x - st.get("lr", lr) * (m1 / (1 - .9 ** k)) / (np.sqrt(m2 / (1 - .999 ** k)) + 1e-8)
        pe = np.abs(ans.state(x)) ** 2; stage_end.append(round(float(pe[opt].sum()), 4))
        if stop == "freq": break
    ps = np.abs(ans.state(x)) ** 2
    d = rng.choice(len(ps), size=final_shots, p=ps / ps.sum()); mode = int(np.argmax(ps))
    return dict(case=case, seed=seed, method="ps-adam-staged", stage_end_p_opt=json.dumps(stage_end), stages=json.dumps(stages), S=S, iters=it_total, stop=stop,
                circuits=circuits, shots_total=circuits * S, n_params=int(ans.n_params),
                p_opt=float(ps[opt].sum()), p_valid=float(ps[valid].sum()), mode_is_opt=bool(opt[mode]) and ps[mode] > 0.5,
                shot_hit_opt=bool(opt[d].any()), optimum_seen_in_training=best_plan_hits, grad_clips=clips, t=time.perf_counter() - t0)

def job_staged(a):
    name, case, cfg, seed, stages, kw = a
    try: r = train_shots_staged(case, cfg, seed, stages, **kw)
    except Exception as ex: r = dict(case=case, seed=seed, error=repr(ex)[:300])
    r["name"] = name; r["cfg"] = json.dumps(cfg); return r
