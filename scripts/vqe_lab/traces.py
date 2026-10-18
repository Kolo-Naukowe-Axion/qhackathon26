import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lab, json
L2 = dict(layers=2, pairs="coupled", init_noise=0.2)
M = {"CVaR 0.1 (current)": [dict(loss="cvar", alpha=0.1, maxfun=300)],
     "Gibbs eta=30": [dict(loss="gibbs", eta=30, maxfun=300)],
     "CVaR 0.1 then Gibbs eta=100": [dict(loss="cvar", alpha=0.1, maxfun=150), dict(loss="gibbs", eta=100, maxfun=150)],
     "ascending CVaR 0.1>0.3>mean": [dict(loss="cvar", alpha=0.1, maxfun=100), dict(loss="cvar", alpha=0.3, maxfun=100), dict(loss="mean", maxfun=100)]}
out = {}
for seed in (8, 0):
    for n, st in M.items():
        r = lab.train("S0", dict(L2, stages=st), seed, trace=True)
        out[f"{n}|{seed}"] = dict(trace=r["trace"], p_opt=r["p_opt"], nfev=r["nfev"], mode=bool(r["mode_is_opt"]))
        print(seed, n, r["nfev"], round(r["p_opt"], 4), r["mode_is_opt"], flush=True)
json.dump(out, open("traces_S0.json", "w"))
