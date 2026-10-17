"""Reproducible, offline Stage 1 compact-QUBO experiments and bundle.

python -m solver.compact --phase screen --output output/new-compact-screen
python -m solver.compact --phase validate --output output/new-compact-validation
python -m solver.compact --phase bundle --output output/new-compact --export-final
"""
import argparse
import gzip
import json
from pathlib import Path
import statistics
from unittest.mock import patch

from .artifacts import save_run, write_json
from .sequence import build_sequence_qubo
from .stage1 import ROOT, decode, energy, exact_reference
import itertools
from .verify import verify_run


SCREEN = [
    dict(size="2x2", kind="quantum", layers=1, mixer="x", restarts=1),
    *[dict(size="3x3", kind="quantum", layers=p, mixer=mixer, restarts=restarts)
      for p, mixer, restarts in ((1, "x", 8), (1, "local-x", 8), (2, "x", 8),
                                (2, "local-x", 2), (2, "local-x", 4),
                                (2, "local-x", 8), (3, "local-x", 4))],
    *[dict(size="3x3", kind="anneal", sweeps=sweeps, schedule="geometric")
      for sweeps in (16, 64, 256)],
]
# Fixed after screening. Validation uses fresh optimizer/sampling seeds.
SELECTED = [SCREEN[0], SCREEN[6], SCREEN[-1]]


def certificates():
    result = {}
    for size in ("2x2", "3x3"):
        instance = json.loads((ROOT / "instances" / f"instance_{size}.json").read_text())
        model = build_sequence_qubo(instance)
        states = []
        for bits in itertools.product((0, 1), repeat=len(model["variables"])):
            try:
                schedule = decode(model, bits)
                makespan = max(row["end"] for row in schedule)
            except ValueError:
                makespan = None
            states.append(dict(bits=list(bits), energy=energy(model, bits), makespan=makespan))
        reference = exact_reference(instance)
        result[size] = dict(states=states, independent_reference=reference,
                            permutation_optimum=min(row["makespan"] for row in states if row["makespan"] is not None),
                            represented_orders=len(model["order_costs"]), logical_bits=len(model["variables"]),
                            minimality_scope="Distinct states for ALL earliest-start common job orders only",
                            gap_to_full_machine_order_optimum=min(row["energy"] for row in states) - reference["makespan"])
    return result


def refresh_public_evidence(selected, verified):
    summary = {}
    for size, official in verified.items():
        name = f"instance_{size}"
        directory = Path(selected[name])
        if not directory.is_absolute():
            directory = ROOT / directory
        report = json.loads((directory / "run.json").read_text())
        samples = json.loads((directory / "samples.json").read_text())
        row = {key: report[key] for key in ("method", "timestamp", "encoding", "variables", "total_samples",
                                           "feasible_samples", "feasible_rate")}
        row["source"] = selected[name]
        row["metadata"] = {key: report["metadata"][key] for key in (
            "mixer", "trainable_parameters", "layers", "shots", "seed", "restarts", "maxiter",
            "elapsed_wall_seconds", "ideal_ground_probability", "circuit_operations")}
        row["optimal_samples"] = sum(sample["count"] for sample in samples
                                      if sample["feasible"] and sample["makespan"] == official["makespan"])
        summary[name] = row
    (ROOT / "presentation/problem-explanation/evidence.js").write_text(
        "// Selected verified local runs; generated from output/stage1-selected.json and retained samples.\n"
        + "export const selectedEvidence = " + json.dumps(summary, indent=2, allow_nan=False) + ";\n")


def execute(config, seed, directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    name = f"instance_{config['size']}"
    instance = json.loads((ROOT / "instances" / f"{name}.json").read_text())
    model = build_sequence_qubo(instance)
    options = {key: value for key, value in config.items() if key not in ("size", "kind")}
    with patch("socket.socket.connect", side_effect=AssertionError("Offline run attempted network")):
        if config["kind"] == "quantum":
            from qiskit import qasm3
            from .quantum import run_qaoa
            records, metadata, history, counts, circuit = run_qaoa(model, seed=seed, shots=4096, **options)
            with gzip.open(directory / "optimization-history.json.gz", "wt") as file:
                json.dump(history, file, allow_nan=False)
            write_json(directory / "raw-counts.json", counts)
            (directory / "circuit.qasm").write_text(qasm3.dumps(circuit))
            (directory / "circuit.txt").write_text(str(circuit.draw(output="text")) + "\n")
            method = f"QAOA p={options['layers']}, {options['mixer']} mixer, pairwise-order QUBO (Qiskit Aer statevector simulator)"
        else:
            from .local import anneal
            records, metadata = anneal(model, seed=seed, reads=512, **options)
            method = "Classical pairwise-order QUBO simulated annealing (dwave-samplers)"
        metadata.update(network_blocked_during_run=True, reference_warm_start=False,
                        cost_construction="All n! permutation costs; no reference optimum/horizon input")
        official, report = save_run(directory, name, instance, model, records, method, metadata)
        # Full independent machine orders are assessed AFTER sampling.
        _, reference = verify_run(directory)
        write_json(directory / "verification.json", reference)
    samples = json.loads((directory / "samples.json").read_text())
    optimal = sum(row["count"] for row in samples if row["feasible"] and row["makespan"] == reference["exact_reference"])
    return dict(seed=seed, feasible_rate=report["feasible_rate"], optimal_rate=optimal / report["total_samples"],
                optimal_samples=optimal, total_samples=report["total_samples"],
                makespan=official["makespan"], optimality_gap=reference["optimality_gap"],
                ideal_ground_probability=metadata.get("ideal_ground_probability"),
                expected_energy=metadata.get("expected_energy"),
                wall_seconds=metadata["elapsed_wall_seconds"],
                circuit_operations=metadata.get("circuit_operations"), directory=str(directory.relative_to(ROOT))
                    if directory.is_relative_to(ROOT) else str(directory))


def summarize(config, rows):
    return dict(config=config, runs=rows, mean_optimal_rate=statistics.mean(r["optimal_rate"] for r in rows),
                min_optimal_rate=min(r["optimal_rate"] for r in rows),
                mean_feasible_rate=statistics.mean(r["feasible_rate"] for r in rows),
                median_wall_seconds=statistics.median(r["wall_seconds"] for r in rows),
                total_samples=sum(r["total_samples"] for r in rows),
                optimal_samples=sum(r["optimal_samples"] for r in rows),
                all_runs_optimal=all(r["optimality_gap"] == 0 for r in rows))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("screen", "validate", "bundle"), default="bundle")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--export-final", action="store_true")
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() and any(output.iterdir()):
        parser.error("Use a fresh output directory to retain all prior evidence")
    if args.export_final and args.phase != "bundle":
        parser.error("Only a verified bundle can be exported")
    output.mkdir(parents=True, exist_ok=True)
    # Retain the source itself as well as per-run hashes, including uncommitted code.
    for source in sorted((ROOT / "solver").glob("*.py")):
        target = output / "source_snapshot/solver" / source.name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
    configs = SCREEN if args.phase == "screen" else [SCREEN[i] for i in (0, 4, 5, 6, 8, 9, 10)] if args.phase == "validate" else SELECTED
    seeds = [0, 1, 2] if args.phase == "screen" else list(range(200, 220)) if args.phase == "validate" else [2026]
    summaries = []
    for index, config in enumerate(configs):
        rows = []
        label = f"{config['kind']}-{config['size']}"
        directory = output / (f"candidate-{index:02d}" if args.phase != "bundle" else label)
        for seed in seeds:
            rows.append(execute(config, seed, directory / f"seed-{seed}" if args.phase != "bundle" else directory))
        summary = summarize(config, rows)
        summaries.append(summary)
        write_json(output / "results.json", dict(phase=args.phase, seeds=seeds, results=summaries,
                    scope="Fixed official instances only; random optimizer/sampler seeds, not unseen-instance evaluation",
                    remote_backends_on_hold=["ODRA5", "VeloxQ"]))
        print(json.dumps({key: value for key, value in summary.items() if key != "runs"}), flush=True)
    if args.phase == "bundle":
        write_json(output / "formulation-certificates.json", certificates())
        selected = {f"instance_{size}": str((output / f"quantum-{size}").relative_to(ROOT))
                    if output.is_relative_to(ROOT) else str(output / f"quantum-{size}") for size in ("2x2", "3x3")}
        manifest = dict(status="Both official instances solved optimally by simulator QAOA on compact order QUBOs",
                        selected_runs=selected, classical_comparison=str(output / "anneal-3x3"),
                        veloxq_remote_executed=False, odra5_hardware_executed=False,
                        remote_backends_on_hold=["VeloxQ", "ODRA5"],
                        note="Permutation-cost tabulation is factorial classical preprocessing; no quantum advantage claimed")
        # Verify both before mutating either official output.
        verified = {size: verify_run(output / f"quantum-{size}")[0] for size in ("2x2", "3x3")}
        if any(row["makespan"] != exact_reference(json.loads((ROOT / "instances" / f"instance_{size}.json").read_text()))["makespan"]
               for size, row in verified.items()):
            raise RuntimeError("Bundle failed exact optimality guard")
        write_json(output / "selected-runs.json", manifest)
        if args.export_final:
            for size, official in verified.items():
                write_json(ROOT / f"schedule_{size}.json", official)
            write_json(ROOT / "output/stage1-selected.json", manifest)
            refresh_public_evidence(selected, verified)


if __name__ == "__main__":
    main()
