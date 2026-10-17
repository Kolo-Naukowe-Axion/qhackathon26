"""Frozen-protocol QAOA campaign: write the plan, run TRAIN or TEST, summarize.

The plan (settings, budgets, seeds, bundle hashes, adapter source hash) is
written once, after selection on TRAIN cases, and before any TEST run. ``run``
refuses to start if a bundle or the adapter source changed since freezing.
Samples are checked by the central decoder/checker; nothing is repaired.
Simulation only.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import statistics
import time

ROOT = Path(__file__).resolve().parents[2]
ADAPTER = ROOT / "catering/methods/qaoa.py"
CASES = {
    "cell": dict(split="train", bundle="output/catering-complete-cell-v3/quantum-qubo.json",
                 sector_reference="output/catering-complete-cell-v3/reference-sector.json",
                 raw_reference="output/catering-complete-cell-v3/reference-raw.json"),
    **{s: dict(split="train" if s in ("S0", "S1") else "test",
               bundle=f"output/catering-foundation-v3/{s}/quantum-qubo.json",
               sector_reference=f"output/catering-foundation-v3/{s}/quantum-sector-reference.json",
               raw_reference=f"output/catering-foundation-v3/{s}/raw-reference.json")
       for s in ("S0", "S1", "S2", "S3")},
}
CONFIGS = {
    "frozen": dict(variant="xy_multiangle_warm", depth=3, optimizer="layerwise"),
    "random_angles": dict(variant="xy_multiangle_warm", depth=3, optimizer="random"),
    "xy_layerwise": dict(variant="xy", depth=3, optimizer="layerwise"),
    "start_only": dict(variant="xy_multiangle_warm", depth=0),
    "uniform_sector": dict(variant="xy", depth=0),
}
TUPLE = ("U", "W", "B", "R")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_plan(path, selection_evidence):
    path = Path(path)
    if path.exists():
        raise ValueError("Plan already frozen; never overwrite it")
    bundles = {}
    for name, case in CASES.items():
        bundle = json.loads((ROOT / case["bundle"]).read_text())
        bundles[name] = dict(case, bundle_sha256=bundle["bundle_sha256"],
                             qubits=bundle["size"]["binary_variables"])
    plan = dict(schema_version="catering-qaoa-plan.v1",
                frozen_at=time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                selection="Chosen on TRAIN cases (cell, S0, S1) only, by mean rank of median P(optimum) "
                          "over 5 seeds at 64 and 256 evaluations; S2/S3 never inspected before freezing",
                selection_evidence=selection_evidence,
                cases=bundles, configs=CONFIGS, budgets=[256, 2048], seeds=list(range(2026, 2036)),
                shots=4096, loss="cvar", alpha=0.1, wall_time_limit_s=1800,
                initializer="xy_multiangle_warm: incumbent_ids=[] -> 85% weight on each block's idle qubit "
                            "(the release's all-idle witness plan as declared initializer); "
                            "xy: uniform one-hot sector",
                circuit_counting="Gradient-free optimizers: one training circuit per loss evaluation",
                adapter_sha256=sha(ADAPTER), regime="exact simulator probabilities for training; "
                                                    "4096 shot samples for returned plans")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n")
    return plan


def _job(args):
    case_name, case, config_name, config, budget, seed, plan, run_dir = args
    from catering.contracts import load_bundle
    from catering.decode import decode
    from catering.methods.qaoa import solve_qubo
    bundle = load_bundle(ROOT / case["bundle"])
    started = time.monotonic()
    result = solve_qubo(bundle, dict(training_objective_evaluations=max(budget, 1), shots=plan["shots"],
                                     wall_time_limit_s=plan["wall_time_limit_s"]),
                        dict(config, loss=plan["loss"], alpha=plan["alpha"], seed=seed, restarts=4),
                        run_dir)
    checked, valid_shots, best = [], 0, None
    for sample in result["samples"]:
        verdict = decode(bundle, sample["bits"])
        metrics = verdict["check"]["metrics"] if verdict["valid"] else None
        checked.append(dict(count=sample["count"], valid=verdict["valid"], energy=verdict["energy"],
                            metrics=metrics))
        if verdict["valid"]:
            valid_shots += sample["count"]
            score = tuple(metrics[k] for k in TUPLE)
            best = score if best is None or score < best else best
    (run_dir / "evaluation.json").write_text(json.dumps(dict(
        bundle_sha256=bundle["bundle_sha256"], checker="catering.decode.decode (central)", repair=False,
        samples=checked), sort_keys=True) + "\n")
    d = result["configuration"]["distribution"]
    return dict(case=case_name, config=config_name, budget=budget, seed=seed, status=result["status"],
                evaluations=result["work"]["training_objective_evaluations"],
                ground_probability=d["ground_probability"], valid_probability=d["valid_probability"],
                ground_states=d["ground_states"], sampled_valid_fraction=valid_shots/plan["shots"],
                best_valid_tuple=best, wall_s=time.monotonic()-started)


def run(plan_path, split, output, workers=8):
    plan = json.loads(Path(plan_path).read_text())
    if sha(ADAPTER) != plan["adapter_sha256"]:
        raise ValueError("Adapter source changed after the plan was frozen")
    output = Path(output)
    if output.exists():
        raise ValueError("Fresh output directory required")
    jobs = []
    for case_name, case in plan["cases"].items():
        if case["split"] != split:
            continue
        bundle = json.loads((ROOT / case["bundle"]).read_text())
        if bundle["bundle_sha256"] != case["bundle_sha256"]:
            raise ValueError(f"{case_name}: bundle changed after freezing")
        for config_name, config in plan["configs"].items():
            for budget in (plan["budgets"] if config["depth"] else [0]):
                for seed in plan["seeds"]:
                    run_dir = output / case_name / f"{config_name}-b{budget}-s{seed}"
                    jobs.append((case_name, case, config_name, config, budget, seed, plan, run_dir))
    output.mkdir(parents=True)
    rows = []
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(_job, job) for job in jobs]
        for future in as_completed(futures):
            row = future.result()
            rows.append(row)
            print(json.dumps(dict(n=len(rows), of=len(jobs), case=row["case"], config=row["config"],
                                  budget=row["budget"], seed=row["seed"], best=row["best_valid_tuple"])), flush=True)
    rows.sort(key=lambda r: (r["case"], r["config"], r["budget"], r["seed"]))
    summary = summarize(plan, rows, split)
    (output / "runs.json").write_text(json.dumps(rows, indent=1) + "\n")
    (output / "summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    (output / "manifest.json").write_text(json.dumps(dict(
        plan_sha256=sha(plan_path), adapter_sha256=sha(ADAPTER), split=split,
        files={str(p.relative_to(output)): sha(p) for p in sorted(output.rglob("*.json"))}), indent=1) + "\n")
    return summary


def summarize(plan, rows, split):
    references = {}
    for name, case in plan["cases"].items():
        if case["split"] != split:
            continue
        sector = json.loads((ROOT / case["sector_reference"]).read_text())
        sector_metrics = (sector.get("ground") or sector)["check"]["metrics"]
        raw = json.loads((ROOT / case["raw_reference"]).read_text())["check"]["metrics"]
        references[name] = dict(portfolio_optimum=[sector_metrics[k] for k in TUPLE],
                                raw_cp_optimum=[raw[k] for k in TUPLE])
    groups = {}
    for r in rows:
        groups.setdefault((r["case"], r["config"], r["budget"]), []).append(r)
    table = []
    for (case, config, budget), rs in sorted(groups.items()):
        target = tuple(references[case]["portfolio_optimum"])
        bests = [tuple(r["best_valid_tuple"]) if r["best_valid_tuple"] else None for r in rs]
        found = [b for b in bests if b is not None]
        table.append(dict(
            case=case, config=config, budget=budget, seeds=len(rs),
            success_rate=sum(b == target for b in bests)/len(rs),
            median_ground_probability=statistics.median(r["ground_probability"] for r in rs),
            median_valid_probability=statistics.median(r["valid_probability"] for r in rs),
            ground_states=rs[0]["ground_states"],
            best_tuple_over_seeds=list(min(found)) if found else None,
            median_seed_best_tuple=list(sorted(found)[len(found)//2]) if found else None,
            median_evaluations=statistics.median(r["evaluations"] for r in rs),
            median_wall_s=statistics.median(r["wall_s"] for r in rs),
            statuses=sorted({r["status"] for r in rs})))
    return dict(split=split, references=references, table=table,
                note="success = a seed's best checked plan equals the exact portfolio optimum; "
                     "raw_cp_optimum is the full-kitchen reference (portfolio restriction gap)")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("freeze")
    p.add_argument("--plan", type=Path, required=True)
    p.add_argument("--selection-evidence", required=True)
    p = sub.add_parser("run")
    p.add_argument("--plan", type=Path, required=True)
    p.add_argument("--split", choices=("train", "test"), required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    if args.command == "freeze":
        write_plan(args.plan, args.selection_evidence)
    else:
        run(args.plan, args.split, args.output, args.workers)


if __name__ == "__main__":
    main()
