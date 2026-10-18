import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lab
cg = [dict(loss="cvar", alpha=0.1, maxfun=150), dict(loss="gibbs", eta=100, maxfun=150)]
J = [(n, "S0", dict(a, init_noise=0.2, stages=cg), s) for n, a in
     (("H block-L1 cvar>gibbs100", dict(layers=1, pairs="none")), ("H block-L2 cvar>gibbs100", dict(layers=2, pairs="none")),
      ("H block+cost-L2 cvar>gibbs100", dict(layers=2, pairs="none", cost_phase=True)), ("H block+cost-L4 cvar>gibbs100", dict(layers=4, pairs="none", cost_phase=True)))
     for s in range(10)]
df = lab.run_grid(J, "gridH_runs.csv", procs=3)
print(df.groupby("method").agg(mode=("mode_is_opt", "sum"), popt=("p_opt", "median"), cnot=("cnot_est", "first"), nfev=("nfev", "median")).to_string())
