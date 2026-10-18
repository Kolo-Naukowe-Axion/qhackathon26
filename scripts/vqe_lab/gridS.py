import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shots, multiprocessing as mp, pandas as pd
L2 = dict(layers=2, pairs="coupled", init_noise=0.2)
C = {"S-ref cvar100>gibbs100x200": ([dict(loss="cvar", alpha=0.1, iters=100), dict(loss="gibbs", eta=100, iters=200)], {}),
     "S-a cvar200>gibbs100x200": ([dict(loss="cvar", alpha=0.1, iters=200), dict(loss="gibbs", eta=100, iters=200)], {}),
     "S-b cvar100>gibbs30x200": ([dict(loss="cvar", alpha=0.1, iters=100), dict(loss="gibbs", eta=30, iters=200)], {}),
     "S-c S4096 cvar100>gibbs100x200": ([dict(loss="cvar", alpha=0.1, iters=100), dict(loss="gibbs", eta=100, iters=200)], dict(S=4096)),
     "S-d lr.02 cvar200>gibbs100x200": ([dict(loss="cvar", alpha=0.1, iters=200), dict(loss="gibbs", eta=100, iters=200)], dict(lr=0.02))}
J = [(n, "S0", L2, s, st, kw) for n, (st, kw) in C.items() for s in range(5)]
rows = []
with mp.get_context("fork").Pool(6) as pool:
    for r in pool.imap_unordered(shots.job_staged, J):
        rows.append(r); pd.DataFrame(rows).to_csv("gridS_runs.csv", index=False)
print("done", len(rows))
