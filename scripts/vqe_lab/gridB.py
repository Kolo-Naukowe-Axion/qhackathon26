import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lab, json
G = lambda eta, mf=300: [dict(loss="gibbs", eta=eta, maxfun=mf)]
A = {
 "B0 coupled-L2": dict(layers=2, pairs="coupled"),
 "B1 coupled-L1": dict(layers=1, pairs="coupled"),
 "B2 block-L1": dict(layers=1, pairs="none"),
 "B3 block-L2": dict(layers=2, pairs="none"),
 "B4 block+cost-L2": dict(layers=2, pairs="none", cost_phase=True),
 "B5 block+cost-L4": dict(layers=4, pairs="none", cost_phase=True),
 "B6 xy+cost-L4": dict(layers=4, pairs="none", inblock="xy", cost_phase=True),
 "B7 random-L2": dict(layers=2, pairs="random"),
}
jobs = []
for c in ("S0", "S1", "cell"):
    for n, a in A.items():
        for eta in (30,):
            for s in range(5):
                jobs.append((f"{n} gibbs{eta}", c, dict(a, init_noise=0.2, stages=G(eta)), s))
json.dump(dict(ansatz=A, loss="gibbs30 maxfun300", cases=["cell","S0","S1"], seeds=list(range(5))), open("gridB_manifest.json", "w"), indent=1)
df = lab.run_grid(jobs, "gridB_runs.csv", procs=9)
print("done", len(df))
