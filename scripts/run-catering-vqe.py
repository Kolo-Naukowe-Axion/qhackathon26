"""Grid runner for the catering VQE experiments (exact ideal simulation, local CPU only).

    PYTHONPATH=. python scripts/run-catering-vqe.py --grid E1 --output output/catering-methods/vqe/E1-v1
"""
import argparse, csv, json, os, sys, time, hashlib
os.environ.setdefault("OMP_NUM_THREADS", "1"); os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
from multiprocessing import Pool
from pathlib import Path

CASES = {"cell": "output/catering-complete-cell-v3/quantum-qubo.json",
         **{f"S{s}": f"output/catering-foundation-v3/S{s}/quantum-qubo.json" for s in range(4)}}
_P = {}


def grid(name):
    from catering.methods.vqe import Spec
    jobs = []
    if name == "E1":
        for case in ("cell", "S0", "S1"):
            Ls = (1, 2, 4) if case == "cell" else (1, 2)
            specs = [Spec("product")]
            specs += [Spec("block_hea", layers=L, maxiter=400) for L in (1, 2)]
            specs += [Spec("sector", layers=L, pairs="none") for L in Ls]
            pm = ("coupled",) if case == "cell" else ("coupled", "random", "all")   # cell: all 3 pairs coupled
            specs += [Spec("sector", layers=L, pairs=m) for m in pm for L in Ls]
            jobs += [(case, s, seed) for s in specs for seed in range(10)]
    elif name == "E4":
        for case in ("cell", "S0", "S1"):
            specs = [Spec("product", init="random"), Spec("sector", layers=1, pairs="none", init="random"),
                     Spec("sector", layers=1, pairs="coupled", init="random")]
            specs += [Spec("sector", layers=1, pairs="none", init_noise=1.0),
                      Spec("sector", layers=1, pairs="coupled", init_noise=1.0)]
            jobs += [(case, s, seed) for s in specs for seed in range(10)]
    elif name == "E2":
        # optimiser x loss on the block ansatz (A2) and coupled cross-block ansatz (A3), depth 1
        for case in ("cell", "S0", "S1"):
            for pairs in ("none", "coupled"):
                base = dict(ansatz="sector", layers=1, pairs=pairs)
                specs = [Spec(**base),                                            # L-BFGS mean (adjoint)
                         *[Spec(**base, loss="cvar", alpha=a) for a in (0.05, 0.1, 0.25)],
                         Spec(**base, optimizer="adam", budget=500),
                         Spec(**base, optimizer="nft", budget=1500),
                         Spec(**base, optimizer="spsa", budget=1500, train_shots=1024),
                         Spec(**base, optimizer="spsa", budget=1500, train_shots=1024, loss="cvar", alpha=0.1)]
                if pairs == "none":                                               # COBYLA only for few params
                    specs += [Spec(**base, optimizer="cobyla", budget=1500),
                              Spec(**base, optimizer="cobyla", budget=1500, train_shots=1024, loss="cvar", alpha=0.1)]
                jobs += [(case, sp, seed) for sp in specs for seed in range(10)]
            if case != "cell":                                                    # generic block-local ansatz, shots only
                hea = dict(ansatz="block_hea", layers=1)
                specs = [Spec(**hea, optimizer="spsa", budget=1500, train_shots=1024),
                         Spec(**hea, optimizer="spsa", budget=1500, train_shots=1024, loss="cvar", alpha=0.1),
                         Spec(**hea, optimizer="cobyla", budget=1500, train_shots=1024, loss="cvar", alpha=0.1)]
                jobs += [(case, sp, seed) for sp in specs for seed in range(10)]
    elif name == "E3":
        # under the E2 winner (exact CVaR alpha=0.1, L-BFGS adjoint): entanglement re-test, gates, init, controls
        cv = dict(loss="cvar", alpha=0.1)
        for case in ("cell", "S0", "S1"):
            specs = [Spec("sector", layers=1, pairs="coupled", inblock="xy", **cv),           # gates: XY in-block
                     Spec("sector", layers=1, pairs="coupled", z_phases=True, **cv),          # gates: + Z phases
                     Spec("sector", layers=1, pairs="coupled", cross="zz", **cv),             # gates: ZZ cross
                     Spec("sector", layers=2, pairs="coupled", cross="zz", **cv),
                     Spec("sector", layers=2, pairs="coupled", **cv),                         # depth
                     Spec("sector", layers=1, pairs="none", init="random", **cv),             # init (E4)
                     Spec("sector", layers=1, pairs="coupled", init="random", **cv),
                     Spec("sector", layers=1, pairs="none", init_noise=1.0, **cv),
                     Spec("sector", layers=1, pairs="coupled", init_noise=1.0, **cv),
                     Spec("product", optimizer="cobyla", budget=1500, train_shots=1024, **cv), # no-entanglement control
                     Spec("product", optimizer="spsa", budget=1500, train_shots=1024, **cv)]
            if case != "cell":                                                                # cell: all pairs coupled
                specs += [Spec("sector", layers=1, pairs="random", **cv), Spec("sector", layers=1, pairs="all", **cv),
                          Spec("block_hea", layers=1, optimizer="spsa", budget=1500, train_shots=1024, **cv),
                          Spec("block_hea", layers=1, optimizer="cobyla", budget=1500, train_shots=1024, **cv)]
            jobs += [(case, sp, seed) for sp in specs for seed in range(10)]
    elif name == "E5":
        # held-out confirmation; configuration fixed in output/catering-methods/vqe/E5-predeclaration.json
        base = dict(ansatz="sector", pairs="coupled", layers=2, loss="cvar", alpha=0.1)
        specs = [Spec(**base), Spec(**{**base, "layers": 1, "alpha": 0.05}),
                 Spec(**{**base, "pairs": "none", "layers": 1}), Spec(**{**base, "pairs": "random"}),
                 Spec(**{**base, "loss": "mean"})]
        jobs = [(case, sp, seed) for case in ("S2", "S3") for sp in specs for seed in range(10)]
    else:
        raise SystemExit(f"unknown grid {name}")
    return jobs


def work(job):
    from catering.contracts import load_bundle
    from catering.methods.vqe import Problem, run
    case, spec, seed = job
    if case not in _P:
        _P[case] = Problem(load_bundle(CASES[case]))
    prob = _P[case]
    try:
        r = run(prob, spec, seed)
        r.pop("x"); r.pop("_samples", None)
        r["status"] = "completed"
    except Exception as e:  # keep failures
        r = dict(spec=spec.name(), tag=spec.tag(), seed=seed, status="failed", error=repr(e)[:200])
    r.update(case=case, bundle_sha256=prob.bundle["bundle_sha256"], init=spec.init,
             init_noise=spec.init_noise, layers=spec.layers, pairs=spec.pairs, cross=spec.cross,
             inblock=spec.inblock, z_phases=spec.z_phases, gates=json.dumps(r.get("gates", {})))
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--grid", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--workers", type=int, default=9)
    a = ap.parse_args()
    out = Path(a.output)
    out.mkdir(parents=True, exist_ok=False)
    jobs = grid(a.grid)
    # longest jobs first
    jobs.sort(key=lambda j: (j[0] == "cell" and j[1].ansatz != "block_hea", -j[1].layers, j[1].pairs == "none",
                             j[1].optimizer == "lbfgs"))
    t0 = time.time()
    fields = None
    with open(out / "runs.csv", "w", newline="") as fh, Pool(a.workers) as pool:
        for i, r in enumerate(pool.imap_unordered(work, jobs)):
            if fields is None:
                fields = sorted(set(r) | {"error", "status", "stop"})
                w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore"); w.writeheader()
            w.writerow(r); fh.flush()
            if i % 20 == 0:
                print(f"{i+1}/{len(jobs)} {time.time()-t0:.0f}s", flush=True)
    manifest = dict(grid=a.grid, jobs=len(jobs), wall_s=time.time() - t0,
                    execution_kind="quantum_simulation", expectation="exact (ideal statevector on one-hot sector / block product)",
                    gradients="adjoint (exact); see tag column for optimizer|loss|training shots|init",
                    optimizer_note="L-BFGS-B ftol=1e-11 gtol=1e-7; all sector runs stop once one plan holds >0.995",
                    final_samples=1024, physical_qpu_calls=0, veloxq_calls=0,
                    cases={c: CASES[c] for c in sorted({j[0] for j in jobs})},
                    source_sha256=hashlib.sha256(Path("catering/methods/vqe.py").read_bytes()).hexdigest())
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("done", time.time() - t0)


if __name__ == "__main__":
    main()
