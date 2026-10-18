import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lab, json
base = dict(layers=2, pairs="coupled")
R = {
 "C0 gibbs30 W0.2 lbfgs": dict(base, init_noise=0.2, stages=[dict(loss="gibbs", eta=30, maxfun=300)]),
 "C1 gibbs30 W1.0 lbfgs": dict(base, init_noise=1.0, stages=[dict(loss="gibbs", eta=30, maxfun=300)]),
 "C2 gibbs30 random lbfgs": dict(base, init="random", stages=[dict(loss="gibbs", eta=30, maxfun=300)]),
 "C3 cvar0.1 random lbfgs": dict(base, init="random", stages=[dict(loss="cvar", alpha=0.1, maxfun=300)]),
 "C4 gibbs30 W0.2 adam.05": dict(base, init_noise=0.2, stages=[dict(loss="gibbs", eta=30, maxfun=300, opt="adam", lr=0.05)]),
 "C5 cvar0.1 W0.2 adam.05": dict(base, init_noise=0.2, stages=[dict(loss="cvar", alpha=0.1, maxfun=300, opt="adam", lr=0.05)]),
}
jobs = [(n, c, cfg, s) for c in ("S0", "S1", "cell") for n, cfg in R.items() for s in range(5)]
json.dump(dict(configs=R, cases=["cell","S0","S1"], seeds=list(range(5))), open("gridC_manifest.json", "w"), indent=1)
df = lab.run_grid(jobs, "gridC_runs.csv", procs=9)
print("done", len(df))
