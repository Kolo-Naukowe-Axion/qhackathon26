"""Scratch benchmark: angle-optimization strategies at an equal evaluation budget."""
import sys, json, math, time, warnings
import numpy as np
from scipy.optimize import minimize
from catering.contracts import load_bundle
from catering.methods import qaoa
warnings.filterwarnings("ignore")

class Stop(Exception): pass

def make_loss(b, space, variant, initial, scale, budget):
    E = space["energy"].astype(float); order = np.argsort(space["energy"], kind="stable")
    st = dict(n=0, best=math.inf, x=None)
    def f(x):
        if st["n"] >= budget: raise Stop
        p = np.abs(qaoa.evolve(b, space, variant, initial, x, scale))**2
        v = qaoa.cvar(p, E, order, 0.1); st["n"] += 1
        if v < st["best"]: st.update(best=v, x=np.array(x))
        return v
    return f, st

def rand_x(rng, per, depth):
    out=[]
    for _ in range(depth):
        out += [rng.uniform(0, math.pi)]*(per-2) + [rng.uniform(0, math.pi), rng.uniform(-math.pi/2, math.pi/2)]
    return np.array(out)

def run(strategy, b, space, variant, depth, budget, seed):
    rng = np.random.default_rng(seed); per = 3 if variant == "xy_multiangle_warm" else 2
    scale = qaoa.default_scale(b); initial = qaoa.initial_state(b, space, variant, qaoa.DEFAULTS)
    f, st = make_loss(b, space, variant, initial, scale, budget)
    try:
        if strategy == "random":
            while True: f(rand_x(rng, per, depth))
        elif strategy in ("COBYLA", "L-BFGS-B"):
            while True:
                opt = dict(maxiter=budget//4) if strategy == "COBYLA" else dict(maxfun=budget//4)
                minimize(f, rand_x(rng, per, depth), method=strategy, options=opt)
        elif strategy == "random+COBYLA":
            for _ in range(budget//4): f(rand_x(rng, per, depth))
            while True: minimize(f, st["x"], method="COBYLA", options=dict(maxiter=budget, rhobeg=0.3))
        elif strategy == "layerwise":   # INTERP-style: grow depth, reuse previous layer angles
            x = None
            for d in range(1, depth+1):
                share = budget*d//sum(range(1, depth+1)) if d < depth else budget
                if x is None: x = rand_x(rng, per, 1)
                else:
                    last = x[-per:]; x = np.concatenate([x, last*0.5])
                while st["n"] < min(share, budget):
                    r = minimize(f, x, method="COBYLA", options=dict(maxiter=share-st["n"], rhobeg=0.3))
                    x = st["x"] if len(st["x"]) == len(x) else r.x
                    if st["n"] < share: x = x + rng.normal(0, 0.2, len(x))  # restart near best
                if d < depth: st["best"] = math.inf  # report only the final depth's loss
            raise Stop
    except Stop: pass
    p = np.abs(qaoa.evolve(b, space, variant, initial, st["x"], scale))**2
    st["best"] = qaoa.cvar(p, space["energy"].astype(float), np.argsort(space["energy"], kind="stable"), 0.1)
    g = space["energy"] == space["energy"].min()
    return dict(loss=st["best"], pg=float(p[g].sum()), pv=float(p[space["valid"]].sum()), evals=st["n"])

# TRAIN cases only (cell, S0, S1); S2/S3 are held out for confirmation.
cases = [("v3-S0", "output/catering-foundation-v3/S0/quantum-qubo.json"),
         ("v3-S1", "output/catering-foundation-v3/S1/quantum-qubo.json")]
strategies = ["random", "COBYLA", "L-BFGS-B", "random+COBYLA", "layerwise"]
rows = []
for name, path in cases:
    b = load_bundle(path)
    for variant in ("xy", "xy_multiangle_warm"):
        space = qaoa._sector_space(b)
        for depth in (1, 2, 3):
            for budget in (64, 256):
                for strategy in strategies:
                    if strategy == "layerwise" and depth == 1: continue
                    rs = [run(strategy, b, space, variant, depth, budget, seed) for seed in range(5)]
                    row = dict(case=name, variant=variant, depth=depth, budget=budget, strategy=strategy,
                               loss_median=float(np.median([r["loss"] for r in rs])),
                               pg_median=float(np.median([r["pg"] for r in rs])),
                               pv_median=float(np.median([r["pv"] for r in rs])))
                    rows.append(row); print(json.dumps(row), flush=True)
json.dump(rows, open(sys.argv[1], "w"), indent=1)
