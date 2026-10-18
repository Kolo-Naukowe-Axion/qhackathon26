import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shots, multiprocessing as mp, pandas as pd, time
while len(pd.read_csv("gridF2_runs.csv")) < 60: time.sleep(20)
L2 = dict(layers=2, pairs="coupled", init_noise=0.2)
J = [("F1 psAdam gibbs30 L2", c, L2, s, [dict(loss="gibbs", eta=30, iters=300)], {}) for c in ("S0", "S1", "cell") for s in range(5)]
rows = []
with mp.get_context("fork").Pool(9) as pool:
    for r in pool.imap_unordered(shots.job_staged, J):
        rows.append(r); pd.DataFrame(rows).to_csv("gridF3_runs.csv", index=False)
print("done", len(rows))
