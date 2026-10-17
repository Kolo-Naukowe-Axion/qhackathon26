"""A genuine local QAOA circuit, optimized by mean QUBO energy, then sampled."""

import argparse
import json
from pathlib import Path
import time

import numpy as np
from qiskit import QuantumCircuit, transpile, qasm3
from qiskit.circuit import ParameterVector
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator
from scipy.optimize import minimize

from .artifacts import save_run, write_json
from .stage1 import ROOT, build_qubo, decode, energy, to_dimod


def feasible_mask(model, costs):
    if model.get("objective") != "makespan":
        return costs == 0
    valid = []
    for state in range(len(costs)):
        try:
            decode(model, [(state >> i) & 1 for i in range(len(model["variables"]))])
            valid.append(True)
        except ValueError:
            valid.append(False)
    return np.array(valid)


def qaoa_circuit(model, layers, mixer="x"):
    """U_C=exp(-i gamma E/scale), U_B=exp(-i beta sum X).

    dimod uses s=2x-1; Qiskit's Z eigenvalue is 1-2x, so h*s=-h*Z.
    RZ(-2 gamma h/scale), RZZ(2 gamma J/scale) implement the cost.
    """
    if not 1 <= layers <= 8:
        raise ValueError("QAOA layers must be in 1..8")
    if mixer not in ("x", "local-x"):
        raise ValueError("Mixer must be x or local-x")
    h, couplings, offset = to_dimod(model).to_ising()
    scale = max([1.0] + [abs(v) for v in h.values()] + [abs(v) for v in couplings.values()])
    n = len(model["variables"])
    circuit = QuantumCircuit(n)
    gamma = ParameterVector("gamma", layers)
    beta = ParameterVector("beta", layers if mixer == "x" else layers * n)
    circuit.h(range(n))
    for layer in range(layers):
        for i, field in h.items():
            if field:
                circuit.rz(-2 * gamma[layer] * field / scale, i)
        for (i, j), coupling in couplings.items():
            if coupling:
                circuit.rzz(2 * gamma[layer] * coupling / scale, i, j)
        for i in range(n):
            circuit.rx(2 * beta[layer if mixer == "x" else layer * n + i], i)
    return circuit, list(gamma) + list(beta), scale


def run_qaoa(model, *, layers=3, restarts=16, maxiter=500, shots=4096, seed=2026, optimizer="BFGS", mixer="local-x"):
    n = len(model["variables"])
    if n > 12:
        raise ValueError("Local QAOA runner is limited to 12 qubits")
    if min(restarts, maxiter, shots) < 1:
        raise ValueError("Positive optimizer budgets and shot count required")
    circuit, parameters, scale = qaoa_circuit(model, layers, mixer)
    # Full cost diagonal defines the expectation; it does not choose the answer.
    costs = np.array([energy(model, [(state >> i) & 1 for i in range(n)]) for state in range(1 << n)])
    rng, history, attempts = np.random.default_rng(seed), [], []
    best = None
    started = time.perf_counter()
    for restart in range(restarts):
        def objective(theta):
            bound = circuit.assign_parameters(dict(zip(parameters, theta)))
            probabilities = Statevector.from_instruction(bound).probabilities()
            value = float(probabilities @ costs)
            history.append(dict(restart=restart, mean_energy=value, parameters=[float(x) for x in theta]))
            return value / scale

        initial = rng.uniform(-np.pi, np.pi, len(parameters))
        options = dict(maxiter=maxiter, tol=1e-7, rhobeg=0.5) if optimizer == "COBYLA" else dict(maxiter=maxiter, gtol=1e-8)
        result = minimize(objective, initial, method=optimizer, options=options)
        attempts.append(dict(restart=restart, expected_energy=float(result.fun * scale),
                             evaluations=int(result.nfev), converged=bool(result.success), message=str(result.message)))
        if best is None or result.fun < best.fun:
            best = result
    bound = circuit.assign_parameters(dict(zip(parameters, best.x)))
    ideal = Statevector.from_instruction(bound).probabilities()
    measured = bound.copy()
    measured.measure_all()
    simulator = AerSimulator(method="statevector", seed_simulator=seed)
    compiled = transpile(measured, simulator, seed_transpiler=seed)
    counts = simulator.run(compiled, shots=shots).result().get_counts()
    records = [dict(bits=[int(x) for x in bitstring[::-1]], count=int(count)) for bitstring, count in counts.items()]
    metadata = dict(algorithm="QAOA with transverse-X mixer" if mixer == "x" else "QAOA with independently parameterized single-qubit X mixers",
                    mixer=mixer, trainable_parameters=len(parameters),
                    simulator="Qiskit Aer statevector + measured shots",
                    layers=layers, shots=shots, seed=seed, restarts=restarts, maxiter=maxiter,
                    cost_scale=scale, optimized_parameters=[float(x) for x in best.x],
                    parameter_order="all gamma, then all beta (layer-major qubit order for local-x)", optimizer=f"{optimizer}, mean QUBO energy",
                    expected_energy=float(ideal @ costs), ideal_feasible_probability=float(ideal[feasible_mask(model, costs)].sum()),
                    ideal_ground_probability=float(ideal[costs == costs.min()].sum()),
                    elapsed_wall_seconds=time.perf_counter() - started, attempts=attempts,
                    circuit_depth=bound.depth(), circuit_operations=dict(bound.count_ops()),
                    bit_order="sample[i] is qubit i; raw Qiskit strings reversed on decoding")
    return records, metadata, history, counts, bound


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "output/stage1/qaoa-2x2")
    parser.add_argument("--layers", type=int, default=3)
    parser.add_argument("--restarts", type=int, default=16)
    parser.add_argument("--maxiter", type=int, default=500)
    parser.add_argument("--shots", type=int, default=4096)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--optimizer", choices=("COBYLA", "BFGS"), default="BFGS")
    parser.add_argument("--mixer", choices=("x", "local-x"), default="local-x")
    args = parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        parser.error("Use an empty output directory to preserve previous evidence")
    instance = json.loads((ROOT / "instances/instance_2x2.json").read_text())
    model = build_qubo(instance, 4, "domain-wall")
    records, metadata, history, counts, circuit = run_qaoa(model, layers=args.layers, restarts=args.restarts,
                                                        maxiter=args.maxiter, shots=args.shots, seed=args.seed, optimizer=args.optimizer,
                                                        mixer=args.mixer)
    args.output.mkdir(parents=True, exist_ok=True)
    write_json(args.output / "optimization-history.json", history)
    write_json(args.output / "raw-counts.json", counts)
    (args.output / "circuit.qasm").write_text(qasm3.dumps(circuit))
    (args.output / "circuit.txt").write_text(str(circuit.draw(output="text")) + "\n")
    official, report = save_run(args.output, "instance_2x2", instance, model, records,
                                f"QAOA p={args.layers}, {args.mixer} mixer (Qiskit Aer statevector simulator)", metadata)
    print(json.dumps(dict(makespan=official["makespan"], feasible_rate=report["feasible_rate"],
                          ideal_feasible_probability=metadata["ideal_feasible_probability"], output=str(args.output)), indent=2))


if __name__ == "__main__":
    main()
