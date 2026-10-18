import sys, os, time; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shots, json, multiprocessing as mp, pandas as pd
L2 = dict(layers=2, pairs="coupled", init_noise=0.2); L1 = dict(layers=1, pairs="coupled", init_noise=0.2); B1 = dict(layers=1, pairs="none", init_noise=0.2)
cg = [dict(loss="cvar", alpha=0.1, iters=100), dict(loss="gibbs", eta=100, iters=200)]
g30 = [dict(loss="gibbs", eta=30, iters=300)]
J = []
for c in ("S0", "S1", "cell"):
    for s in range(5):
        J += [("F1 psAdam gibbs30 L2", c, L2, s, g30, {}), ("F2 psAdam cvar>gibbs100 L2", c, L2, s, cg, {}),
              ("F3 psAdam cvar>gibbs100 L1", c, L1, s, cg, {}), ("F4 psAdam cvar>gibbs100 block-L1", c, B1, s, cg, {})]
J.sort(key=lambda a: (a[1] == "cell", "block" in a[0]))
rows = []
with mp.get_context("fork").Pool(9) as pool:
    for r in pool.imap_unordered(shots.job_staged, J):
        rows.append(r); pd.DataFrame(rows).to_csv("gridF2_runs.csv", index=False)
print("done", len(rows))
