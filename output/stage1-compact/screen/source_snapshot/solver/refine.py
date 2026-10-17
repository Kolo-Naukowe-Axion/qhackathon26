"""Bounded, network-blocked Stage 1 experiments with real sample evidence.

Run: python -m solver.refine --output output/stage1-local/search
Every candidate gets the same seeds; each child has a five-minute time limit.
No candidate repairs samples, warm starts from an answer, or calls a service.
"""

import argparse
import json
from pathlib import Path
import statistics
import subprocess
import sys
import time
from unittest.mock import patch

from .artifacts import assess_samples, save_run, write_json
from .stage1 import ROOT, build_qubo, exact_reference

CANDIDATES = [
    dict(kind="quantum", label="shared p3, 32 restarts", layers=3, mixer="x", restarts=32),
    dict(kind="quantum", label="shared p4, 16 restarts", layers=4, mixer="x", restarts=16),
    dict(kind="quantum", label="local p2, 32 restarts", layers=2, mixer="local-x", restarts=32),
    dict(kind="quantum", label="local p3, 16 restarts", layers=3, mixer="local-x", restarts=16),
    dict(kind="quantum", label="local p4, 8 restarts", layers=4, mixer="local-x", restarts=8),
    dict(kind="quantum", label="shared p5, 16 restarts", layers=5, mixer="x", restarts=16),
    dict(kind="anneal", label="geometric 2000", sweeps=2000, schedule="geometric"),
    dict(kind="anneal", label="geometric 4000", sweeps=4000, schedule="geometric"),
    dict(kind="anneal", label="geometric 8000", sweeps=8000, schedule="geometric"),
    dict(kind="anneal", label="linear 2000", sweeps=2000, schedule="linear"),
    dict(kind="anneal", label="geometric 2000 beta .1..32", sweeps=2000, schedule="geometric", beta_range=[0.1,32]),
    dict(kind="anneal", label="linear 4000 beta .1..32", sweeps=4000, schedule="linear", beta_range=[0.1,32]),
    dict(kind="anneal", label="linear 8000", sweeps=8000, schedule="linear"),
    dict(kind="anneal", label="linear 16000", sweeps=16000, schedule="linear"),
    dict(kind="anneal", label="linear 32000", sweeps=32000, schedule="linear"),
    dict(kind="anneal", label="linear 64000", sweeps=64000, schedule="linear"),
    dict(kind="anneal", label="geometric 32000", sweeps=32000, schedule="geometric"),
    dict(kind="anneal", label="linear 16000 beta .1..8", sweeps=16000, schedule="linear", beta_range=[0.1,8]),
]


def measure(config, seed, directory):
    """Keep every actual sample and optimizer trace, including failed samples."""
    name = "instance_2x2" if config["kind"] == "quantum" else "instance_3x3"
    instance = json.loads((ROOT / "instances" / f"{name}.json").read_text())
    model = build_qubo(instance, 4 if name == "instance_2x2" else 8,
                       "domain-wall" if name == "instance_2x2" else "onehot")
    options = {k:v for k,v in config.items() if k not in ("kind", "label")}
    directory.mkdir(parents=True, exist_ok=False)
    if config["kind"] == "quantum":
        from qiskit import qasm3
        from .quantum import run_qaoa
        records, metadata, history, counts, circuit = run_qaoa(model, seed=seed, maxiter=500, shots=4096, **options)
        write_json(directory / "optimization-history.json", history)
        write_json(directory / "raw-counts.json", counts)
        (directory / "circuit.qasm").write_text(qasm3.dumps(circuit))
        (directory / "circuit.txt").write_text(str(circuit.draw(output="text")) + "\n")
        method = f"QAOA p={config['layers']}, {config['mixer']} mixer (Qiskit Aer statevector simulator)"
    else:
        from .local import anneal
        records, metadata = anneal(model, seed=seed, reads=512, **options)
        method = "Classical QUBO simulated annealing (dwave-samplers)"
    metadata["network_blocked_during_run"] = True
    official, report = save_run(directory, name, instance, model, records, method, metadata)
    # Independent reference is invoked AFTER sampling and is never a warm start.
    if official["makespan"] != exact_reference(instance)["makespan"]:
        raise ValueError("Candidate failed the exact-optimum guard")
    return dict(seed=seed, feasible_rate=report["feasible_rate"], makespan=official["makespan"],
                ideal_feasible_probability=metadata.get("ideal_feasible_probability"),
                expected_energy=metadata.get("expected_energy"),
                wall_seconds=metadata["elapsed_wall_seconds"],
                directory=str(directory.relative_to(ROOT)) if directory.is_relative_to(ROOT) else str(directory))


def worker(config, seeds, directory):
    with patch("socket.socket.connect", side_effect=AssertionError("Offline experiment attempted network")):
        rows = [measure(config, seed, directory / f"seed-{seed}") for seed in seeds]
    report = dict(config=config, seeds=seeds, runs=rows,
                  mean_feasible_rate=statistics.mean(r["feasible_rate"] for r in rows),
                  min_feasible_rate=min(r["feasible_rate"] for r in rows),
                  median_wall_seconds=statistics.median(r["wall_seconds"] for r in rows),
                  mean_ideal_feasible_probability=statistics.mean(r["ideal_feasible_probability"] for r in rows)
                    if config["kind"] == "quantum" else None)
    write_json(directory / "summary.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--worker", type=int, help="One candidate index, used by the bounded parent runner")
    parser.add_argument("--seeds", type=int, nargs="+", default=[0,1,2])
    parser.add_argument("--phase", choices=("screen", "anneal-followup"), default="screen")
    args = parser.parse_args()
    if not args.seeds or any(seed < 0 or seed >= 2**31 for seed in args.seeds):
        parser.error("Seeds must be integers in 0..2^31-1")
    if args.worker is not None and not 0 <= args.worker < len(CANDIDATES):
        parser.error("Unknown candidate index")
    output = args.output.resolve()
    if args.worker is not None:
        print(json.dumps(worker(CANDIDATES[args.worker], args.seeds, output)))
        return
    if output.exists():
        parser.error("Choose a fresh search directory to preserve prior evidence")
    output.mkdir(parents=True)
    rows, best = [], {}
    research = """# Stage 1 offline refinement

## Goal
Improve reliability of actual valid samples while retaining optimal makespans 4/8.
Prefer a shallower QAOA circuit if its validation probability remains at least 99.5%.

## Success Metric
Mean valid-sample fraction on fixed seeds; QAOA also reports exact statevector probability.
No statistical claim across different scheduling instances is made.

## Constraints
- Tier: 1, local foreground execution; pause_every: never (user requested continued iteration).
- max_iterations: 12; max_seconds_per_iteration: 300.
- Evaluator: python -m solver.refine (JSON summaries, independent feasibility and optimum guard).
- Keep policy: score_improvement, separately for quantum and classical candidates.
- noise_runs: 3 screening seeds; ten new seeds validate the selected settings.
- min_delta: 0.001; target: quantum >=99.5% valid with <=3 layers; classical >=99.5% valid.
- Guard: exact optimal makespan, real unmodified samples, no remote API/hardware, no answer warm start.
- Existing working tree is preserved; only settings change between trials, with no Git resets or automatic commits.

## Current Approach
Four-qubit domain-wall QAOA and 39-variable one-hot simulated annealing.

## Search Space
Shared or per-qubit X mixer; layers 2..5; 8..32 restarts.
Anneal with 2000..8000 sweeps, geometric/linear schedules, default/custom beta range.

## History
| Iteration | Candidate | Mean valid | Median seconds | Decision |
| --- | --- | --- | --- | --- |
"""
    indices = list(range(12)) if args.phase == "screen" else list(range(12,18))
    research = research.replace("max_iterations: 12", f"max_iterations: {len(indices)}")
    if args.phase == "anneal-followup":
        research += "\nFollow-up hypothesis: a slower cooldown can escape the remaining local minima; compare linear and geometric schedules at higher sweep budgets. Prior best: 98.372% valid, geometric 8000.\n\n"
    (output / "research.md").write_text(research)
    (output / "autoresearch-results.tsv").write_text("iteration\tkind\tlabel\tfeasible_rate\twall_seconds\tstatus\n")
    for iteration, i in enumerate(indices,1):
        config = CANDIDATES[i]
        directory = output / f"iteration-{iteration:02d}"
        started = time.perf_counter()
        try:
            child = subprocess.run([sys.executable, "-m", "solver.refine", "--worker", str(i),
                                    "--output", str(directory), "--seeds", *map(str,args.seeds)],
                                   cwd=ROOT, capture_output=True, text=True, timeout=300, check=True)
            row = json.loads((directory / "summary.json").read_text())
            score = row["mean_feasible_rate"]
            kept = config["kind"] not in best or score > best[config["kind"]]["mean_feasible_rate"] + 0.001
            row["status"] = "keep" if kept else "retain evidence; do not promote"
            if kept:
                best[config["kind"]] = row
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as exc:
            row = dict(config=config, status=type(exc).__name__, error=str(exc), mean_feasible_rate=0,
                       median_wall_seconds=time.perf_counter()-started)
        rows.append(row)
        write_json(output / "results.json", dict(scope="Local only; both remote backends on hold", iterations=rows, best=best))
        with (output / "research.md").open("a") as log:
            log.write(f"| {iteration} | {config['label']} | {row['mean_feasible_rate']:.5%} | {row['median_wall_seconds']:.4f} | {row['status']} |\n")
        with (output / "research_log.md").open("a") as log:
            log.write(f"\n## Iteration {iteration}: {config['label']}\n\nHypothesis: {config} changes sampling reliability under the same validation guard.\n\nResult: {json.dumps(row)}\n")
        with (output / "autoresearch-results.tsv").open("a") as log:
            log.write(f"{iteration}\t{config['kind']}\t{config['label']}\t{row['mean_feasible_rate']}\t{row['median_wall_seconds']}\t{row['status']}\n")
        plot_progress(rows, output / "progress.png")
        print(f"{iteration}/{len(indices)} {config['label']}: {row['mean_feasible_rate']:.3%}, {row['status']}", flush=True)
    write_json(output / "validation-plan.json", dict(new_seeds=list(range(100,110)), candidates=best,
                                                    note="Selected after screening; confirm before promotion"))
    (output / "final_report.md").write_text("# Local Stage 1 experiment report\n\n"
        f"Completed {len(rows)} iterations ({args.phase}). Raw evidence is retained for every attempted setting.\n\n"
        + "\n".join(f"- {kind}: {row['config']['label']}, mean valid {row['mean_feasible_rate']:.3%}, median {row['median_wall_seconds']:.3f} s."
                    for kind,row in best.items())
        + "\n\nScreening results require confirmation on the validation-plan seeds. These are local simulator/classical results on the two official instances, with no hardware or VeloxQ execution and no quantum-advantage claim.\n")


def plot_progress(rows, path):
    """Optional plot; the solver/evaluator has no plotting dependency."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return
    plt.rcParams.update({"font.family":"sans-serif", "figure.facecolor":"white", "axes.spines.top":False,
                         "axes.spines.right":False, "font.size":10})
    fig, ax = plt.subplots(figsize=(8,4))
    for kind, color in (("quantum", "#0072B2"),("anneal", "#D55E00")):
        points = [(i+1,r) for i,r in enumerate(rows) if r["config"]["kind"] == kind]
        if not points:
            continue
        envelope, current = [], 0
        for i,row in points:
            score = row["mean_feasible_rate"] * 100
            current = max(current,score)
            envelope.append(current)
            ax.scatter(i,score,c=color if row["status"]=="keep" else "white",edgecolors=color,zorder=3)
        ax.plot([i for i,_ in points], envelope, color=color, label=kind + " best observed")
    ax.axhline(99.5, color="#666666",linestyle="--",linewidth=1,label="99.5% target")
    ax.set(xlabel="Candidate iteration",ylabel="Valid samples (%)",title="Local screening: same three seeds per candidate")
    ax.legend(fontsize=9,loc="lower left")
    fig.tight_layout()
    fig.savefig(path,dpi=180)
    plt.close(fig)


if __name__ == "__main__":
    main()
