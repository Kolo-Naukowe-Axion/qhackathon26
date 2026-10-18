import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shots, multiprocessing as mp, pandas as pd
L2 = dict(layers=2, pairs="coupled", init_noise=0.2)
J = [("F1L psAdam gibbs30 L2 500it", "S0", L2, s, [dict(loss="gibbs", eta=30, iters=500)], {}) for s in range(10)]
rows = []
with mp.get_context("fork").Pool(5) as pool:
    for r in pool.imap_unordered(shots.job_staged, J):
        rows.append(r); pd.DataFrame(rows).to_csv("gridF4_runs.csv", index=False)
print("done", len(rows))
