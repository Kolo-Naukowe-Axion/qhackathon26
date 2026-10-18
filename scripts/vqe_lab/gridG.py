import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lab, json
cg = [dict(loss="cvar", alpha=0.1, maxfun=150), dict(loss="gibbs", eta=100, maxfun=150)]
J = [(f"G keep{k} cvar>gibbs100 L2", c, dict(layers=2, pairs="coupled", init_noise=0.2, keep=k, stages=cg), s)
     for c in ("S0", "S1", "cell") for k in (0.05, 0.1, 0.25, 0.5) for s in range(10)]
J.sort(key=lambda j: j[1] == "cell")
df = lab.run_grid(J, "gridG_runs.csv", procs=5)
print("done", len(df))
