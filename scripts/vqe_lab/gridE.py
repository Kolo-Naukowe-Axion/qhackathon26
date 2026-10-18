import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lab, json
L2 = dict(layers=2, pairs="coupled", init_noise=0.2); L1 = dict(layers=1, pairs="coupled", init_noise=0.2)
asc3 = [dict(loss="cvar", alpha=0.1, maxfun=100), dict(loss="cvar", alpha=0.3, maxfun=100), dict(loss="mean", maxfun=100)]
asc6 = [dict(loss="cvar", alpha=a, maxfun=50) for a in (0.05, 0.1, 0.2, 0.4, 0.7)] + [dict(loss="mean", maxfun=50)]
cg = [dict(loss="cvar", alpha=0.1, maxfun=150), dict(loss="gibbs", eta=100, maxfun=150)]
ann = [dict(loss="gibbs", eta=3, maxfun=100), dict(loss="gibbs", eta=30, maxfun=100), dict(loss="gibbs", eta=300, maxfun=100)]
J = []
for c in ("S0", "S1", "cell"):
    for s in range(5, 10):
        J += [("M1 asc3 cvar.1>.3>mean", c, dict(L2, stages=asc3), s), ("M2 asc6 .05..1", c, dict(L2, stages=asc6), s),
              ("M10 cvar.1>gibbs100", c, dict(L2, stages=cg), s), ("M8 fvqe30", c, dict(L2, stages=[dict(loss="fvqe", tau=30, maxfun=300)]), s),
              ("M3 gibbs10", c, dict(L2, stages=[dict(loss="gibbs", eta=10, maxfun=300)]), s),
              ("C4 gibbs30 W0.2 adam.05", c, dict(L2, stages=[dict(loss="gibbs", eta=30, maxfun=300, opt="adam", lr=0.05)]), s)]
    for s in range(10):
        J += [("E1 anneal gibbs3>30>300", c, dict(L2, stages=ann), s), ("E2 asc3 L1", c, dict(L1, stages=asc3), s),
              ("E3 cvar.1>gibbs100 L1", c, dict(L1, stages=cg), s)]
J.sort(key=lambda j: j[1] == "cell")
json.dump(dict(n=len(J)), open("gridE_manifest.json", "w"))
df = lab.run_grid(J, "gridE_runs.csv", procs=9)
print("done", len(df))
