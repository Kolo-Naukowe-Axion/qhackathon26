"""Reproducible LOCAL encoding comparison, never a VeloxQ performance claim."""

import argparse
import json
from pathlib import Path
import statistics

from .artifacts import assess_samples, digest, versions, write_json
from .local import anneal
from .stage1 import ROOT, build_qubo, exact_reference


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "output/stage1/local-benchmark.json")
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--reads", type=int, default=256)
    parser.add_argument("--sweeps", type=int, default=2000)
    args = parser.parse_args()
    if min(args.seeds, args.reads, args.sweeps) < 1:
        parser.error("Positive budgets required")
    if args.output.exists():
        parser.error("Choose a fresh output file to preserve benchmark history")
    instance = json.loads((ROOT / "instances/instance_3x3.json").read_text())
    optimum = exact_reference(instance)["makespan"]
    results = []
    # H=7 is independently known infeasible; it checks honest failure reporting.
    for horizon in (7, 8):
        for encoding in ("onehot", "domain-wall"):
            model = build_qubo(instance, horizon, encoding)
            runs = []
            for seed in range(args.seeds):
                records, metadata = anneal(model, reads=args.reads, sweeps=args.sweeps, seed=seed)
                checked = assess_samples(instance, model, records)
                feasible = [r for r in checked if r["feasible"]]
                runs.append(dict(seed=seed, feasible_rate=sum(r["count"] for r in feasible) / args.reads,
                                 best_energy=min(r["energy"] for r in checked),
                                 best_makespan=min((r["makespan"] for r in feasible), default=None),
                                 wall_seconds=metadata["elapsed_wall_seconds"]))
            values = [abs(q) for q in model["linear"] if q] + [abs(q) for _, _, q in model["quadratic"] if q]
            results.append(dict(encoding=encoding, horizon=horizon, variables=len(model["variables"]),
                                couplings=len(model["quadratic"]), coefficient_range=[min(values), max(values)],
                                wall_penalty=model.get("wall_penalty"), model_sha256=digest(model),
                                mean_feasible_rate=statistics.mean(r["feasible_rate"] for r in runs),
                                min_feasible_rate=min(r["feasible_rate"] for r in runs),
                                max_feasible_rate=max(r["feasible_rate"] for r in runs),
                                successful_runs=sum(r["best_makespan"] is not None for r in runs),
                                median_wall_seconds=statistics.median(r["wall_seconds"] for r in runs), runs=runs))
    report = dict(scope="Local simulated annealing only; VeloxQ performance unknown", reference_optimum=optimum,
                  reads=args.reads, sweeps=args.sweeps, seeds=args.seeds, versions=versions(), results=results)
    write_json(args.output, report)
    for row in results:
        print(f"H={row['horizon']} {row['encoding']}: n={row['variables']}, feasible={row['mean_feasible_rate']:.3%}, successful runs={row['successful_runs']}/{args.seeds}, max coefficient={row['coefficient_range'][1]}")


if __name__ == "__main__":
    main()
