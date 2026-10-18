import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lab, json
exec(open("gridC.py").read().split("jobs =")[0].split("import lab, json")[1])   # defines base, R
G = lambda eta, mf=300: [dict(loss="gibbs", eta=eta, maxfun=mf)]
jobs = []
for c in ("S0", "S1", "cell"):
    for s in range(5, 10):
        jobs.append(("B1 coupled-L1 gibbs30", c, dict(layers=1, pairs="coupled", init_noise=0.2, stages=G(30)), s))
        jobs.append(("B0 coupled-L2 gibbs30", c, dict(layers=2, pairs="coupled", init_noise=0.2, stages=G(30)), s))
        jobs.append(("M0 cvar0.1", c, dict(layers=2, pairs="coupled", init_noise=0.2, stages=[dict(loss="cvar", alpha=0.1, maxfun=300)]), s))
    for s in range(10):
        for eta in (3, 10):
            jobs.append((f"B2 block-L1 gibbs{eta}", c, dict(layers=1, pairs="none", init_noise=0.2, stages=G(eta)), s))
            jobs.append((f"B4 block+cost-L2 gibbs{eta}", c, dict(layers=2, pairs="none", cost_phase=True, init_noise=0.2, stages=G(eta)), s))
        if s >= 5:
            jobs.append(("B2 block-L1 gibbs30", c, dict(layers=1, pairs="none", init_noise=0.2, stages=G(30)), s))
            jobs.append(("B4 block+cost-L2 gibbs30", c, dict(layers=2, pairs="none", cost_phase=True, init_noise=0.2, stages=G(30)), s))
    for n, cfg in R.items():
        for s in range(5):
            jobs.append((n, c, cfg, s))
# expensive first for load balance
jobs.sort(key=lambda j: (j[1] == "cell", "block" in j[0]))
json.dump(dict(n=len(jobs)), open("gridD_manifest.json", "w"))
df = lab.run_grid(jobs, "gridD_runs.csv", procs=9)
print("done", len(df))
