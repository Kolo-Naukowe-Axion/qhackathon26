"""Compile the four-qubit Stage 1 QAOA for IQM Star; offline by default.

Use the separate requirements-odra.txt environment. --submit runs actual hardware
and requires IQM_SERVER_URL and your own IQM_TOKEN in the execution environment.
The same command works on a WCSS compute session reached via SSH.
"""

import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import time

import numpy as np
from qiskit import qasm3
from qiskit.quantum_info import Statevector
from iqm.qiskit_iqm import IQMFakeAdonis, IQMProvider, transpile_to_IQM

from .artifacts import digest, save_run, write_json
from .quantum import qaoa_circuit
from .stage1 import ROOT
from .verify import verify_run


def classical_probabilities(circuit):
    """Marginalize physical ancillas using the actual measurement wiring."""
    measured = {}
    for instruction in circuit.data:
        if instruction.operation.name == "measure":
            classical = circuit.find_bit(instruction.clbits[0]).index
            if classical in measured:
                raise ValueError("Repeated measurement of a classical bit")
            measured[classical] = instruction.qubits[0]
    if set(measured) != set(range(circuit.num_clbits)):
        raise ValueError("Each classical bit must be measured once")
    unmeasured = circuit.remove_final_measurements(inplace=False)
    # Circuit copying/removing classical registers can reorder the qubit list.
    # Resolve the retained qubit objects in the resulting circuit, not the old list.
    measured = {classical: unmeasured.find_bit(qubit).index for classical, qubit in measured.items()}
    state = Statevector.from_instruction(unmeasured)
    indices = np.arange(len(state.data))
    outcomes = sum(((indices >> physical) & 1) << classical for classical, physical in measured.items())
    return np.bincount(outcomes, weights=state.probabilities(), minlength=1 << circuit.num_clbits)


def compile_candidate(circuit, backend, seeds=8):
    candidates = []
    for seed in range(seeds):
        compiled = transpile_to_IQM(circuit, backend, optimization_level=3, seed_transpiler=seed)
        candidates.append((compiled.count_ops().get("cz", 0), compiled.depth(), seed, compiled))
    _, _, seed, compiled = min(candidates, key=lambda row: row[:3])
    ideal = classical_probabilities(circuit)
    routed = classical_probabilities(compiled)
    if not np.allclose(ideal, routed, atol=1e-10, rtol=0):
        raise ValueError("Compilation changed logical measurement probabilities")
    return compiled, seed, float(np.max(np.abs(ideal - routed)))


def counts_records(counts, variables):
    records = []
    for text, count in counts.items():
        text = text.replace(" ", "")
        if len(text) != variables or any(c not in "01" for c in text):
            raise ValueError("Returned classical register does not match logical variables")
        records.append(dict(bits=[int(c) for c in text[::-1]], count=int(count)))
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-run", type=Path, default=ROOT / "output/stage1-ready/qaoa-2x2")
    parser.add_argument("--output", type=Path, default=ROOT / "output/odra5-preparation")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--submit", action="store_true")
    mode.add_argument("--resume", action="store_true")
    parser.add_argument("--shots", type=int, default=1024)
    parser.add_argument("--timeout", type=float, default=300)
    args = parser.parse_args()
    if args.shots < 1 or not np.isfinite(args.timeout) or args.timeout <= 0:
        parser.error("Positive finite budgets required")
    if not args.resume and args.output.exists() and any(args.output.iterdir()):
        parser.error("Use an empty output directory to preserve evidence")
    if (args.output / "run.json").exists():
        parser.error("Completed evidence already exists; choose a new output directory")
    verify_run(args.source_run)
    source = json.loads((args.source_run / "run.json").read_text())
    if source["instance"] != "instance_2x2":
        parser.error("This hardware runner supports only the four-qubit 2x2 baseline")
    model = json.loads((args.source_run / "model.json").read_text())
    instance = json.loads((ROOT / "instances/instance_2x2.json").read_text())
    metadata = source["metadata"]
    circuit, parameters, _ = qaoa_circuit(model, metadata["layers"], metadata.get("mixer", "x"))
    if len(parameters) != len(metadata["optimized_parameters"]):
        parser.error("Saved QAOA parameter count does not match its circuit")
    circuit = circuit.assign_parameters(dict(zip(parameters, metadata["optimized_parameters"])))
    circuit.measure_all()
    live = args.submit or args.resume
    if live:
        url, token = os.environ.get("IQM_SERVER_URL"), os.environ.get("IQM_TOKEN")
        if not url or not token:
            parser.error("Set IQM_SERVER_URL and your own IQM_TOKEN on the execution host; SSH alone does not authenticate IQM")
        backend = IQMProvider(url, token=token, quantum_computer=os.environ.get("IQM_COMPUTER") or None).get_backend()
        if "mock" in backend.name.lower() or "facade" in backend.name.lower():
            parser.error("Refusing to label a mock/facade backend as physical ODRA5")
        if backend.num_qubits != 5:
            parser.error("Expected ODRA5's five-qubit backend; inspect the connection settings")
    else:
        backend = IQMFakeAdonis()
    args.output.mkdir(parents=True, exist_ok=True)
    if args.resume:
        submission = json.loads((args.output / "submission.json").read_text())
        if submission["source_model_sha256"] != digest(model) or submission["source_parameters"] != metadata["optimized_parameters"]:
            parser.error("Saved job does not match source QAOA model/parameters")
        plan = submission  # Preserve the original circuit/calibration on resume.
        job = backend.retrieve_job(submission["job_id"])
    else:
        compiled, layout_seed, max_error = compile_candidate(circuit, backend)
        plan = dict(scope="ODRA5 physical QPU" if live else "Local IQM Adonis proxy; NOT an ODRA5 calibration/result",
                    hardware_executed=False, source_model_sha256=digest(model), layers=metadata["layers"],
                    source_run=str(args.source_run), logical_qubits=4, physical_qubits=compiled.num_qubits,
                    operations=dict(compiled.count_ops()), depth=compiled.depth(), layout_seed=layout_seed,
                    logical_probability_max_error=max_error, iqm_client_version=importlib.metadata.version("iqm-client"),
                    backend_name=backend.name, calibration_set_id=str(getattr(backend, "_calibration_set_id", "proxy")),
                    shots=args.shots, optimization="Angles optimized locally by QAOA; hardware is used for final sampling")
        (args.output / "native-circuit.qasm").write_text(qasm3.dumps(compiled))
        write_json(args.output / "plan.json", plan)
        # Live runs are explicit and record intent before the only job submission.
        if live:
            write_json(args.output / "submission-intent.json", plan)
        options = dict(shots=args.shots)
        if not live:
            options["seed_simulator"] = 2026
        job = backend.run(compiled, **options)
        submission = dict(plan, job_id=job.job_id(), source_parameters=metadata["optimized_parameters"])
        if live:
            write_json(args.output / "submission.json", submission)
    started = time.perf_counter()
    try:
        result = job.result(timeout=args.timeout) if live else job.result()
    except Exception as exc:
        write_json(args.output / "retrieval-error.json", dict(error_type=type(exc).__name__, job_id=job.job_id()))
        raise RuntimeError(f"{type(exc).__name__}; saved job {job.job_id()} can be retrieved with --resume") from None
    counts = result.get_counts()
    records = counts_records(counts, 4)
    write_json(args.output / "raw-counts.json", counts)
    # Raw counts remain separate from simulator and classical reference evidence.
    run_metadata = dict(submission, hardware_executed=live, retrieval_wall_seconds=time.perf_counter() - started,
                        qaoa_source_parameters=metadata["optimized_parameters"])
    method = f"QAOA p={metadata['layers']} ({'ODRA5 physical IQM Spark QPU' if live else 'IQM Adonis noisy simulator; not physical ODRA5'})"
    official, report = save_run(args.output, "instance_2x2", instance, model, records, method, run_metadata)
    print(json.dumps(dict(scope=plan["scope"], makespan=official["makespan"], feasible_rate=report["feasible_rate"],
                          native_cz=plan["operations"].get("cz", 0), native_depth=plan["depth"], output=str(args.output)), indent=2))


if __name__ == "__main__":
    main()
