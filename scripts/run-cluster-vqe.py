#!/usr/bin/env python3
"""Cluster-entangled VQE grid on Instance B (domain wall, H=8, 30 qubits).

Run the grid:
    PYTHONPATH=. python scripts/run-cluster-vqe.py --layers 1 2 4 --seeds 100 \
        --out output/cluster-vqe-3x3-v1
Rebuild the summary table and figure from an existing runs.csv:
    PYTHONPATH=. python scripts/run-cluster-vqe.py --summarize output/cluster-vqe-3x3-v1

Exact noiseless simulation only. No QPU or VeloxQ call is made.
"""
import argparse
import json
import math
import platform
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from solver.cluster_vqe import factory_clusters, instance_b_setup, random_like, run_once  # noqa: E402

FAMILIES = ["per-operation", "per-machine", "per-job"]


def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def run_grid(args):
    import csv
    inst = json.loads((ROOT / "instances" / "instance_3x3.json").read_text())
    model, qubo, optimal, groups = instance_b_setup(inst, 8)
    schemes = factory_clusters(model)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    rows, t0 = [], time.time()
    fields = None
    with open(out / "runs.csv", "w", newline="") as fh:
        for L in args.layers:
            for name, cl in schemes.items():
                for s in range(args.seeds):
                    jobs = [(name, cl)]
                    if name != "product (k=1)":
                        jobs.append(("random ~" + name, random_like(cl, qubo.n, np.random.default_rng(500 + s))))
                    for label, c in jobs:
                        r = run_once(qubo, c, s, L, optimal, groups)
                        r = dict(scheme=label, **r)
                        if fields is None:
                            fields = list(r)
                            w = csv.DictWriter(fh, fieldnames=fields)
                            w.writeheader()
                        w.writerow(r)
                        fh.flush()
                        rows.append(r)
    (out / "manifest.json").write_text(json.dumps(dict(
        instance="instances/instance_3x3.json", encoding="domain-wall", horizon=8,
        qubits=qubo.n, optimal_bitstrings=int(len(optimal)), layers=args.layers, seeds=args.seeds,
        shots=1000, optimizer="scipy L-BFGS-B, maxiter 2000, adjoint gradients of the mean energy",
        init="theta ~ U(-pi, pi), numpy default_rng(seed)",
        random_cluster_seed="default_rng(500 + seed)", sampling_seed="default_rng(10000 + seed)",
        python=platform.python_version(), numpy=np.__version__,
        runtime_seconds=round(time.time() - t0, 1),
        execution="exact noiseless classical simulation; no QPU, no VeloxQ"), indent=2))
    return out


def summarize(out):
    import pandas as pd
    out = Path(out)
    df = pd.read_csv(out / "runs.csv")
    rows = []
    for (L, sch), g in df.groupby(["L", "scheme"], sort=False):
        k = int(g.hit_1000.sum())
        lo, hi = wilson(k, len(g))
        rows.append(dict(L=L, scheme=sch, k_max=int(g.k_max.iloc[0]), params=int(g.params.iloc[0]),
                         runs=len(g), successes=k, success_rate=round(k / len(g), 3),
                         ci95_low=round(lo, 3), ci95_high=round(hi, 3),
                         mean_P_opt=round(g.P_opt.mean(), 4), median_final_mean_E=g.mean_E.median(),
                         frac_best_E_le_1=round((g.best_E_1000 <= 1).mean(), 3),
                         mean_frac_valid=round(g.frac_valid.mean(), 3)))
    S = pd.DataFrame(rows)
    S.to_csv(out / "summary.csv", index=False)
    plot(df, out / "success.png")
    return S


def plot(df, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 7, "axes.spines.top": False, "axes.spines.right": False})
    kmax = {f: int(df[df.scheme == f].k_max.max()) for f in FAMILIES}
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.7), sharey=True, gridspec_kw=dict(wspace=0.06))
    layers = sorted(df.L.unique())
    series = [("factory clusters", "#1f5fa8", "{f}", -0.12, "o"),
              ("random clusters (same sizes)", "#9a9a9a", "random ~{f}", 0.0, "s"),
              ("no entanglement (k=1)", "#c27c0e", "product (k=1)", 0.12, "^")]
    for ax, f in zip(axes, FAMILIES):
        for lab, col, pat, dx, mk in series:
            sub = df[df.scheme == pat.format(f=f)]
            xs, ys, el, eh = [], [], [], []
            for i, L in enumerate(layers):
                g = sub[sub.L == L]
                if not len(g):
                    continue
                k = int(g.hit_1000.sum())
                lo, hi = wilson(k, len(g))
                p = k / len(g)
                xs.append(i + dx); ys.append(p); el.append(p - lo); eh.append(hi - p)
            ax.errorbar(xs, ys, yerr=[el, eh], color=col, marker=mk, ms=4, lw=1.2, capsize=2, label=lab)
        ax.set_xticks(range(len(layers)))
        ax.set_xticklabels([str(L) for L in layers])
        ax.set_xlabel("ansatz layers L")
        ax.set_title(f"{f} (k \u2264 {kmax[f]})", loc="left")
        ax.margins(x=0.12)
        missing = [L for L in layers if not len(df[(df.scheme == f) & (df.L == L)])]
        if missing:
            ax.text(layers.index(missing[0]), 0.09, f"L={missing[0]} clustered\nruns not done",
                    ha="center", fontsize=6, color="0.4")
    axes[0].set_ylabel("fraction of random starts\nreaching an optimal schedule")
    axes[0].legend(loc="upper left", frameon=False, fontsize=6)
    fig.suptitle("Instance B (30 domain-wall qubits): entangling each operation's own bits helps; "
                 "same-size random clusters do not", fontsize=7.5, x=0.01, ha="left", y=1.06)
    fig.savefig(path, dpi=300, bbox_inches="tight")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--layers", type=int, nargs="+", default=[1, 2, 4])
    ap.add_argument("--seeds", type=int, default=100)
    ap.add_argument("--out", default="output/cluster-vqe-3x3-v1")
    ap.add_argument("--summarize", metavar="DIR", help="only rebuild summary.csv and success.png")
    a = ap.parse_args()
    out = a.summarize or run_grid(a)
    print(summarize(out).to_string(index=False))


if __name__ == "__main__":
    main()
