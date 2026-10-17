"""Recheck saved solver evidence and optionally export an official schedule."""

import argparse
import json
from pathlib import Path

from .artifacts import assess_samples, digest, write_json
from .stage1 import ROOT, decode, exact_reference, validate


def verify_quantum_evidence(directory, model, records, metadata):
    """Reconstruct the optimized quantum state and reconcile actual shot counts."""
    import numpy as np
    from qiskit.quantum_info import Statevector
    from .quantum import feasible_mask, qaoa_circuit
    from .stage1 import energy
    circuit, parameters, scale = qaoa_circuit(model, metadata["layers"], metadata.get("mixer", "x"))
    angles = metadata["optimized_parameters"]
    if len(angles) != len(parameters) or not np.isfinite(angles).all():
        raise ValueError("Invalid saved quantum parameters")
    bound = circuit.assign_parameters(dict(zip(parameters, angles)))
    probabilities = Statevector.from_instruction(bound).probabilities()
    n = len(model["variables"])
    costs = np.array([energy(model, [(state >> i) & 1 for i in range(n)]) for state in range(1 << n)])
    if not np.isclose(float(probabilities @ costs), metadata["expected_energy"], atol=1e-9, rtol=0):
        raise ValueError("Saved expected energy differs from the reconstructed quantum circuit")
    if not np.isclose(float(probabilities[feasible_mask(model, costs)].sum()), metadata["ideal_feasible_probability"], atol=1e-9, rtol=0):
        raise ValueError("Saved ideal probability differs from the reconstructed quantum circuit")
    if metadata["cost_scale"] != scale:
        raise ValueError("Saved quantum cost scale differs from the model")
    if "ideal_ground_probability" in metadata and not np.isclose(
            float(probabilities[costs == costs.min()].sum()), metadata["ideal_ground_probability"], atol=1e-9, rtol=0):
        raise ValueError("Saved optimal probability differs from the reconstructed quantum circuit")
    raw = json.loads((directory / "raw-counts.json").read_text())
    counts = {}
    for text, count in raw.items():
        text = text.replace(" ", "")
        if len(text) != n or any(c not in "01" for c in text) or type(count) is not int or count < 1:
            raise ValueError("Malformed retained quantum counts")
        bits = tuple(int(c) for c in text[::-1])
        counts[bits] = counts.get(bits, 0) + count
    retained = {}
    for row in records:
        bits = tuple(row["bits"])
        retained[bits] = retained.get(bits, 0) + row["count"]
    if counts != retained or sum(counts.values()) != metadata["shots"]:
        raise ValueError("Raw quantum counts, retained samples and shot budget disagree")


def verify_run(directory):
    directory = Path(directory)
    report, model, records, schedule = [json.loads((directory / name).read_text()) for name in
                                        ("run.json", "model.json", "samples.json", "schedule.json")]
    name = report["instance"]
    if name not in ("instance_2x2", "instance_3x3"):
        raise ValueError("Unknown instance")
    instance = json.loads((ROOT / "instances" / f"{name}.json").read_text())
    if report["model_sha256"] != digest(model) or report["instance_sha256"] != digest(instance):
        raise ValueError("Model or instance hash mismatch")
    from .stage1 import build_qubo
    if model["encoding"] == "pairwise-order":
        from .sequence import build_sequence_qubo
        canonical = build_sequence_qubo(instance)
    else:
        canonical = build_qubo(instance, model["horizon"], model["encoding"])
    if model != canonical:
        raise ValueError("Saved model differs from the formulation rebuilt from the official input")
    recomputed = assess_samples(instance, model, records)
    if recomputed != records:
        raise ValueError("Stored sample diagnostics differ from recomputed checks")
    feasible = [r for r in recomputed if r["feasible"]]
    if not feasible or not report["accepted"]:
        raise ValueError("No accepted feasible sample")
    selected = min(feasible, key=lambda r: (r["makespan"], -r["count"], r["bits"]))
    if schedule != dict(instance=name, method=report["method"], makespan=selected["makespan"], schedule=decode(model, selected["bits"])):
        raise ValueError("Official schedule differs from the selected actual sample")
    if validate(instance, schedule["schedule"], schedule["makespan"]):
        raise ValueError("Official schedule failed independent feasibility checking")
    total, accepted = sum(r["count"] for r in recomputed), sum(r["count"] for r in feasible)
    if report["total_samples"] != total or report["feasible_samples"] != accepted or report["feasible_rate"] != accepted / total:
        raise ValueError("Reported sample counts differ from retained samples")
    if report.get("metadata", {}).get("simulator") == "Qiskit Aer statevector + measured shots":
        verify_quantum_evidence(directory, model, records, report["metadata"])
    optimum = exact_reference(instance)["makespan"]
    return schedule, dict(verified=True, instance=name, method=report["method"], makespan=schedule["makespan"],
                          exact_reference=optimum, optimality_gap=schedule["makespan"] - optimum,
                          model_sha256=digest(model), scope="Saved evidence consistency and independent feasibility; not external authentication")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--export", type=Path, help="Write the verified official schedule here")
    args = parser.parse_args()
    schedule, report = verify_run(args.run)
    if args.export:
        write_json(args.export, schedule)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
