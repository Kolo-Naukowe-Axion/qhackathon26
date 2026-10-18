import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lab, json
base = dict(layers=2, pairs="coupled", init_noise=0.2)
M = {
 "M0 cvar0.1": [dict(loss="cvar", alpha=0.1, maxfun=300)],
 "M1 asc3 cvar.1>.3>mean": [dict(loss="cvar", alpha=0.1, maxfun=100), dict(loss="cvar", alpha=0.3, maxfun=100), dict(loss="mean", maxfun=100)],
 "M2 asc6 .05..1": [dict(loss="cvar", alpha=a, maxfun=50) for a in (0.05, 0.1, 0.2, 0.4, 0.7)] + [dict(loss="mean", maxfun=50)],
 "M3 gibbs10": [dict(loss="gibbs", eta=10, maxfun=300)],
 "M4 gibbs30": [dict(loss="gibbs", eta=30, maxfun=300)],
 "M5 gibbs100": [dict(loss="gibbs", eta=100, maxfun=300)],
 "M6 gibbs300": [dict(loss="gibbs", eta=300, maxfun=300)],
 "M7 fvqe10": [dict(loss="fvqe", tau=10, maxfun=300)],
 "M8 fvqe30": [dict(loss="fvqe", tau=30, maxfun=300)],
 "M9 fvqe100": [dict(loss="fvqe", tau=100, maxfun=300)],
 "M10 cvar.1>gibbs100": [dict(loss="cvar", alpha=0.1, maxfun=150), dict(loss="gibbs", eta=100, maxfun=150)],
 "M11 mean": [dict(loss="mean", maxfun=300)],
}
jobs = [(n, c, dict(base, stages=st), s) for c in ("S1", "S0", "cell") for n, st in M.items() for s in range(5)]
json.dump(dict(methods=M, base=base, cases=["cell","S0","S1"], seeds=list(range(5))), open("gridA_manifest.json", "w"), indent=1)
df = lab.run_grid(jobs, "gridA_runs.csv", procs=9)
print("done", len(df))
