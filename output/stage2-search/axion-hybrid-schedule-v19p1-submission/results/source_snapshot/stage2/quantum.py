"""Auditable <=5-total-variable QAOA start-action sampler (no hardware calls).

The statevector, training and shot sampler use Python's standard library.
Qiskit/SciPy are optional verification/optimization dependencies. A physical
device run requires a separate validated backend adapter and authorization.
"""
from __future__ import annotations

from collections import Counter
import cmath
import hashlib
import json
import math
from pathlib import Path
import random
import time

from .qubo import QUBO, anneal, exact_reference, greedy_reference


def _bits(state: int, n: int) -> list[int]:
    return [(state >> i) & 1 for i in range(n)]


def _energies(q: QUBO) -> list[float]:
    return [q.energy(_bits(state, q.size)) for state in range(1 << q.size)]


def _scale(q: QUBO) -> float:
    return max([1.0] + [abs(value) for value in q.linear]
               + [abs(value) for value in q.quadratic.values()])


def problem_metadata(q: QUBO) -> dict:
    data = dict(linear=q.linear, quadratic=[dict(i=i,j=j,value=value) for (i,j),value in sorted(q.quadratic.items())],
        offset=q.offset,penalty=q.penalty,
        candidates=[dict(id=c.id,reward=c.reward,resources=dict(c.resources)) for c in q.candidates],
        conflicts=[[q.candidates[i].id,q.candidates[j].id] for i,j in q.conflicts],
        capacities=q.capacities,slack={name:[list(term) for term in terms] for name,terms in q.slack.items()},
        resource_integer_gcd_scales=dict(getattr(q,"resource_scales",{})),
        convention="upper_triangular_once",variable_order="candidate bits in listed order, followed by slack bit indices")
    data["problem_sha256"] = hashlib.sha256(json.dumps(data,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return data


def _evolve(energies: list[float], n: int, gammas: list[float], betas: list[float],
            scale: float, offset: float = 0.0) -> list[complex]:
    state = [complex(1 / math.sqrt(1 << n))] * (1 << n)
    for gamma, beta in zip(gammas, betas):
        # Removing the constant only changes a global phase.
        state = [amplitude * cmath.exp(-1j * gamma * (energy-offset) / scale)
                 for amplitude, energy in zip(state, energies)]
        cosine, sine = math.cos(beta), -1j * math.sin(beta)
        for qubit in range(n):
            stride = 1 << qubit
            for block in range(0, 1 << n, stride * 2):
                for j in range(block, block + stride):
                    a, b = state[j], state[j + stride]
                    state[j] = cosine * a + sine * b
                    state[j + stride] = sine * a + cosine * b
    return state


def statevector(q: QUBO, gammas, betas, cost_scale=None) -> list[complex]:
    """exp(-i beta sum X) exp(-i gamma QUBO/scale), starting in |+>^n.

    Basis index bit i is variable/qubit i. This function intentionally permits
    only five *total* variables, including all encoded slack.
    """
    if q.size > 5:
        raise ValueError("Statevector runner limited to five total QUBO variables")
    if len(gammas) != len(betas) or len(gammas) not in (1, 2):
        raise ValueError("QAOA requires matching gamma/beta vectors of one or two layers")
    if not all(math.isfinite(value) for value in [*gammas, *betas]):
        raise ValueError("Angles must be finite")
    scale = _scale(q) if cost_scale is None else float(cost_scale)
    if not math.isfinite(scale) or scale <= 0:
        raise ValueError("Cost scale must be finite and positive")
    return _evolve(_energies(q), q.size, list(gammas), list(betas), scale, q.offset)


def _probabilities(state):
    values = [abs(amplitude)**2 for amplitude in state]
    norm = sum(values)
    if not math.isfinite(norm) or norm <= 0:
        raise ValueError("Invalid statevector normalization")
    return [value / norm for value in values]


def circuit_metadata(q: QUBO, gammas, betas, cost_scale=None) -> dict:
    """Portable logical circuit, with ZZ rotations decomposed into CX/RZ/CX.

    No backend connectivity, native gates, calibration or execution is assumed.
    """
    if q.size > 5 or q.size < 1:
        raise ValueError("Circuit export requires one to five total variables")
    if len(gammas) != len(betas) or len(gammas) not in (1, 2):
        raise ValueError("Matching one/two-layer angle vectors required")
    scale = _scale(q) if cost_scale is None else float(cost_scale)
    h = [-value / 2 for value in q.linear]
    couplings = {}
    constant = q.offset + sum(q.linear) / 2
    for (i, j), value in q.quadratic.items():
        h[i] -= value / 4
        h[j] -= value / 4
        couplings[(i, j)] = value / 4
        constant += value / 4
    gates = [dict(name="h", qubits=[i]) for i in range(q.size)]
    for gamma, beta in zip(gammas, betas):
        gates.extend(dict(name="rz", qubits=[i], angle=2 * gamma * field / scale)
                     for i, field in enumerate(h) if field)
        for (i, j), value in sorted(couplings.items()):
            gates.extend([dict(name="cx", qubits=[i, j]),
                          dict(name="rz", qubits=[j], angle=2 * gamma * value / scale),
                          dict(name="cx", qubits=[i, j])])
        gates.extend(dict(name="rx", qubits=[i], angle=2 * beta) for i in range(q.size))
    depth = [0] * q.size
    for gate in gates:
        moment = max(depth[i] for i in gate["qubits"]) + 1
        for i in gate["qubits"]:
            depth[i] = moment
    qasm = ['OPENQASM 2.0;', 'include "qelib1.inc";', f'qreg q[{q.size}];', f'creg c[{q.size}];']
    for gate in gates:
        args = ','.join(f'q[{i}]' for i in gate["qubits"])
        parameter = f'({gate["angle"]:.17g})' if "angle" in gate else ""
        qasm.append(f'{gate["name"]}{parameter} {args};')
    qasm.extend(f'measure q[{i}] -> c[{i}];' for i in range(q.size))
    source = "\n".join(qasm) + "\n"
    return dict(qubits=q.size, layers=len(gammas), cost_scale=scale,
                gamma=list(gammas), beta=list(betas),
                parameter_order="all gamma, then all beta",
                ising_z_fields=h, ising_zz_couplings=[dict(i=i, j=j, value=value)
                    for (i, j), value in sorted(couplings.items())],
                dropped_global_phase_constant=constant,
                logical_depth_without_measurement=max(depth),
                gate_counts=dict(Counter(gate["name"] for gate in gates)),
                logical_gate_sequence=gates, openqasm2=source,
                circuit_sha256=hashlib.sha256(source.encode()).hexdigest(),
                backend_status="logical_only_not_transpiled_not_submitted",
                bit_order="basis index bit i is qubit/variable i; count strings read q[n-1]...q[0]")


def _optimize(q, layers, seed, max_evaluations, restarts, optimizer):
    energies, scale = _energies(q), _scale(q)
    rng = random.Random(seed)
    cache, history = {}, []
    best_value, best_angles = math.inf, None
    started = time.perf_counter()

    class BudgetEnd(Exception):
        pass

    def objective(theta):
        nonlocal best_value, best_angles
        key = tuple(float(value) for value in theta)
        if key in cache:
            return cache[key]
        if len(cache) >= max_evaluations:
            raise BudgetEnd
        probs = _probabilities(_evolve(energies, q.size, list(key[:layers]),
                                       list(key[layers:]), scale, q.offset))
        value = sum(prob * energy for prob, energy in zip(probs, energies)) / scale
        cache[key] = value
        if value < best_value:
            best_value, best_angles = value, list(key)
            history.append(dict(evaluation=len(cache), expected_energy=value*scale,
                                angles=list(key)))
        return value

    if layers == 1:
        initial = [[gamma * math.pi/3, -math.pi/2 + beta * math.pi/6]
                   for gamma in range(6) for beta in range(6)]
    else:
        initial = [[rng.uniform(-math.pi, math.pi) for _ in range(layers)]
                   + [rng.uniform(-math.pi/2, math.pi/2) for _ in range(layers)] for _ in range(32)]
        initial += [[math.pi/2, 0, -math.pi/4, 0], [0] * (2*layers)]
    initial = initial[:max(1, min(len(initial), max_evaluations//2))]
    scored = sorted((objective(theta), theta) for theta in initial)
    attempts = []
    selected_optimizer = optimizer
    minimize = None
    if optimizer == "scipy":
        try:
            from scipy.optimize import minimize
        except ImportError:
            selected_optimizer = "coordinate_scipy_unavailable"
    budget_per_restart = max(8, (max_evaluations-len(cache))//max(1, restarts))
    for restart, (_, initial_theta) in enumerate(scored[:restarts]):
        before = len(cache)
        theta = list(initial_theta)
        value = objective(theta)
        if selected_optimizer == "scipy":
            try:
                result = minimize(objective, theta, method="L-BFGS-B",
                    bounds=[(-2*math.pi, 2*math.pi)]*layers+[(-math.pi/2, math.pi/2)]*layers,
                    options={"maxiter":40,"maxfun":budget_per_restart,"ftol":1e-11})
                attempts.append(dict(restart=restart,evaluations=len(cache)-before,
                                     status=str(result.message),expected_energy=float(result.fun)*scale))
            except BudgetEnd:
                break
        else:
            try:
                for step in (.7, .3, .12, .04, .012):
                    for _ in range(2):
                        improved = False
                        for index in range(2*layers):
                            for sign in (-1, 1):
                                candidate = theta[:]
                                candidate[index] += sign * step
                                if index >= layers:
                                    candidate[index] = (candidate[index] + math.pi/2) % math.pi - math.pi/2
                                else:
                                    candidate[index] = max(-2*math.pi, min(2*math.pi,candidate[index]))
                                trial = objective(candidate)
                                if trial < value - 1e-12:
                                    theta, value, improved = candidate, trial, True
                                if len(cache)-before >= budget_per_restart:
                                    break
                            if len(cache)-before >= budget_per_restart:
                                break
                        if not improved or len(cache)-before >= budget_per_restart:
                            break
                    if len(cache)-before >= budget_per_restart:
                        break
                attempts.append(dict(restart=restart,evaluations=len(cache)-before,
                                     expected_energy=value*scale,status="bounded_coordinate_search"))
            except BudgetEnd:
                break
    probabilities = _probabilities(_evolve(energies, q.size, best_angles[:layers],
                                           best_angles[layers:], scale, q.offset))
    return probabilities, dict(optimizer=selected_optimizer,
        objective="exact noiseless statevector expected QUBO energy",
        evaluations=len(cache), max_evaluations=max_evaluations, restarts=restarts,
        attempts=attempts, cost_scale=scale, expected_energy=best_value*scale,
        gamma=best_angles[:layers], beta=best_angles[layers:],
        history_best_improvements=history,
        elapsed_seconds=time.perf_counter()-started)


def _fallback(q, seed, reason, sweeps, restarts, started):
    raw = anneal(q, seed=seed, sweeps=sweeps, restarts=restarts)
    chosen = [i for i, bit in enumerate(raw["bits"][:len(q.candidates)]) if bit]
    raw_feasible = q.feasible(chosen)
    selected = chosen if raw_feasible else greedy_reference(q, chosen)
    return dict(selected=[q.candidates[i].id for i in selected],
        reward=sum(q.candidates[i].reward for i in selected),feasible=q.feasible(selected),
        method="sa", requested_method="qaoa", quantum_executed=False,quantum_algorithm_simulated=False,
        fallback_reason=reason,proven_optimal_within_pool=False,qubo=q.summary(),
        raw={**raw,"selected":[q.candidates[i].id for i in chosen],"feasible":raw_feasible},
        repaired=selected!=chosen,reference=None,problem=problem_metadata(q),elapsed_seconds=time.perf_counter()-started)


def select_qaoa(q: QUBO, seed=0, layers=1, shots=1024, max_qubits=5,
                max_evaluations=256, restarts=3, optimizer="coordinate",
                fallback_sweeps=100, fallback_restarts=4) -> dict:
    """Select actual sampled feasible cores, retaining all sampling provenance.

    Feasibility is QUBO.feasible(core), never inferred from energy zero. Exact
    enumeration is evaluation only; it does not choose the returned actions.
    """
    started = time.perf_counter()
    if not 1 <= max_qubits <= 5 or layers not in (1, 2):
        raise ValueError("Qubit cap must be 1..5; layers must be 1 or 2")
    if shots < 1 or max_evaluations < 8 or restarts < 1:
        raise ValueError("Positive shots/restarts and at least eight angle evaluations required")
    if optimizer not in ("coordinate", "scipy"):
        raise ValueError("Optimizer must be coordinate or scipy")
    if q.size > max_qubits:
        return _fallback(q,seed,f"{q.size} total variables exceed {max_qubits}-qubit cap (slack included)",
                         fallback_sweeps,fallback_restarts,started)
    if q.size == 0:
        return dict(selected=[],reward=0.0,feasible=True,method="classical_empty_pool",
                    requested_method="qaoa",quantum_executed=False,quantum_algorithm_simulated=False,
                    fallback_reason="No QUBO variables; no quantum circuit needed",
                    proven_optimal_within_pool=True,qubo=q.summary(),raw={"bits":[],"energy":0.0,"feasible":True},
                    repaired=False,reference=exact_reference(q),elapsed_seconds=time.perf_counter()-started)
    probabilities, optimization = _optimize(q,layers,seed,max_evaluations,restarts,optimizer)
    rng = random.Random(seed ^ 0x51A7)
    sampled = Counter(rng.choices(range(1 << q.size),weights=probabilities,k=shots))
    energies = _energies(q)
    reference = exact_reference(q,max_candidates=5)
    optimum_reward = reference["reward"]
    ground = min(energies)
    classifications = []
    for state in range(1 << q.size):
        bits = _bits(state,q.size)
        chosen = [i for i, bit in enumerate(bits[:len(q.candidates)]) if bit]
        feasible = q.feasible(chosen)
        reward = sum(q.candidates[i].reward for i in chosen)
        classifications.append(dict(state=state,bits=bits,indices=chosen,feasible=feasible,
            reward=reward,energy=energies[state],exact_hit=feasible and math.isclose(reward,optimum_reward,abs_tol=1e-8),
            zero_penalty=feasible and math.isclose(energies[state],-reward,abs_tol=1e-8)))
    observed_feasible = [row for row in classifications if sampled[row["state"]] and row["feasible"]]
    fallback_reason = None
    if observed_feasible:
        best = max(observed_feasible,key=lambda row:(row["reward"],-row["energy"],sampled[row["state"]],-row["state"]))
        chosen, raw_bits, raw_energy = best["indices"],best["bits"],best["energy"]
    else:
        # Preserve a safe fallback and disclose that its actions were not sampled.
        best_state = min(sampled,key=lambda state:energies[state])
        best = classifications[best_state]
        chosen, raw_bits, raw_energy = greedy_reference(q,best["indices"]),best["bits"],best["energy"]
        fallback_reason = "No physically feasible core sampled; classical greedy repair used"
    reward = sum(q.candidates[i].reward for i in chosen)
    ideal_feasible = sum(probabilities[row["state"]] for row in classifications if row["feasible"])
    ideal_exact = sum(probabilities[row["state"]] for row in classifications if row["exact_hit"])
    uniform_exact = sum(row["exact_hit"] for row in classifications)/(1 << q.size)
    uniform_feasible = sum(row["feasible"] for row in classifications)/(1 << q.size)
    uniform_sample = Counter(random.Random(seed ^ 0xB451).choices(range(1 << q.size),k=shots))
    uniform_valid = [row for row in classifications if uniform_sample[row["state"]] and row["feasible"]]
    samples = [dict(bitstring=format(state,f"0{q.size}b"),count=count,
                    **{k:v for k,v in classifications[state].items() if k not in ("state", "indices")})
               for state,count in sorted(sampled.items())]
    circuit = circuit_metadata(q,optimization["gamma"],optimization["beta"],optimization["cost_scale"])
    return dict(selected=[q.candidates[i].id for i in chosen],reward=reward,
        feasible=q.feasible(chosen),method="qaoa_statevector",requested_method="qaoa",
        quantum_executed=False,quantum_algorithm_simulated=True,physical_quantum_executed=False,
        fallback_reason=fallback_reason,proven_optimal_within_pool=False,
        sampled_selection_matches_pool_optimum=math.isclose(reward,optimum_reward,abs_tol=1e-8),
        qubo=q.summary(),problem=problem_metadata(q),raw=dict(bits=raw_bits,energy=raw_energy,
            selected=[q.candidates[i].id for i in best["indices"]],feasible=best["feasible"]),
        repaired=fallback_reason is not None,reference=reference,
        sampling=dict(shots=shots,seed=seed,backend="Python exact statevector + seeded Born sampling",
            ideal_basis_probabilities=probabilities,
            raw_counts={format(state,f"0{q.size}b"):count for state,count in sorted(sampled.items())},
            samples=samples,bit_order=circuit["bit_order"],
            ideal_core_feasible_probability=ideal_feasible,
            ideal_exact_reward_hit_probability=ideal_exact,
            ideal_qubo_ground_probability=sum(probabilities[s] for s,e in enumerate(energies) if math.isclose(e,ground,abs_tol=1e-8)),
            ideal_zero_penalty_probability=sum(probabilities[row["state"]] for row in classifications if row["zero_penalty"]),
            sampled_core_feasible_fraction=sum(count for state,count in sampled.items() if classifications[state]["feasible"])/shots,
            sampled_exact_reward_hit_fraction=sum(count for state,count in sampled.items() if classifications[state]["exact_hit"])/shots,
            sample_ground_energy=min(energies[state] for state in sampled),
            exact_ground_energy=ground,optimization=optimization,circuit=circuit,
            uniform_reference=dict(ideal_core_feasible_probability=uniform_feasible,
                ideal_exact_reward_hit_probability=uniform_exact,
                probability_at_least_one_exact_in_same_shots=1-(1-uniform_exact)**shots,
                sampled_best_feasible_reward=max((row["reward"] for row in uniform_valid),default=0.0),
                raw_counts={format(state,f"0{q.size}b"):count for state,count in sorted(uniform_sample.items())})),
        limitations=["This is a classical simulation of a quantum circuit, not a physical ODRA5 run.",
            "At most five total encoded variables are sampled; the full factory is handled by classical state/constraint machinery.",
            "Exact enumeration is an evaluation reference, not the source of the selected actions.",
            "Best feasible selection over many shots is classical postselection; the equal-shot uniform baseline is reported.",
            "The candidate pool and frozen boundary restrict available actions; pool-optimality is not global scheduling optimality."],
        elapsed_seconds=time.perf_counter()-started)


def audit(verify_qiskit=False) -> dict:
    """Small mechanical correctness checks; not factory-quality evidence."""
    from .qubo import build_qubo
    rng = random.Random(721)
    examined = 0
    qiskit_checked = 0
    for trial in range(20):
        n = rng.randrange(1, 6)
        candidates = [dict(id=str(i),reward=rng.randrange(-2,10),resources={}) for i in range(n)]
        conflicts = [(str(i),str(j)) for i in range(n) for j in range(i) if rng.random()<.4]
        q = build_qubo(candidates,conflicts)
        gammas,betas = [.37,-.83],[-.25,.41]
        for layers in (1,2):
            vector = statevector(q,gammas[:layers],betas[:layers])
            assert abs(sum(abs(a)**2 for a in vector)-1)<1e-12
            metadata = circuit_metadata(q,gammas[:layers],betas[:layers])
            for mask in range(1<<n):
                z = [1-2*bit for bit in _bits(mask,n)]
                value = (metadata["dropped_global_phase_constant"]
                    +sum(h*spin for h,spin in zip(metadata["ising_z_fields"],z))
                    +sum(row["value"]*z[row["i"]]*z[row["j"]] for row in metadata["ising_zz_couplings"]))
                assert math.isclose(value,q.energy(_bits(mask,n)),abs_tol=1e-8)
                examined += 1
            if verify_qiskit:
                from qiskit import QuantumCircuit
                from qiskit.quantum_info import Statevector
                circuit = QuantumCircuit.from_qasm_str(metadata["openqasm2"]).remove_final_measurements(inplace=False)
                independent = Statevector.from_instruction(circuit).probabilities()
                assert max(abs(abs(a)**2-b) for a,b in zip(vector,independent))<1e-12
                qiskit_checked += 1
        result = select_qaoa(q,seed=trial,shots=256,max_evaluations=64,restarts=2)
        assert result["feasible"] and sum(result["sampling"]["raw_counts"].values())==256
        assert result["reward"]<=result["reference"]["reward"]+1e-8
    # Core feasibility must not be confused with zero QUBO energy or slack validity.
    slack = build_qubo([dict(id=str(i),reward=i+1,resources={"power":1}) for i in range(3)],capacities={"power":2})
    assert slack.size==5 and slack.feasible([]) and slack.energy([0]*5)>0
    small = select_qaoa(slack,seed=83,shots=256,max_evaluations=64)
    replay = select_qaoa(slack,seed=83,shots=256,max_evaluations=64)
    assert small["sampling"]["raw_counts"]==replay["sampling"]["raw_counts"]
    assert small["selected"]==replay["selected"]
    large = build_qubo([dict(id=str(i),reward=i+1,resources={"power":1}) for i in range(4)],capacities={"power":2})
    assert large.size==6
    fallback = select_qaoa(large,seed=83)
    assert fallback["method"]=="sa" and not fallback["quantum_algorithm_simulated"]
    assert fallback["feasible"] and "slack included" in fallback["fallback_reason"]
    # A one-shot sampled answer is allowed to be suboptimal; reference must not leak into selection.
    suboptimal_seen = False
    for seed in range(20):
        result = select_qaoa(slack,seed=seed,shots=1,max_evaluations=16)
        if not result["repaired"] and result["reward"]<result["reference"]["reward"]:
            suboptimal_seen = True
            break
    assert suboptimal_seen
    return dict(schema="stage2-qaoa-audit.v1",random_qubos=20,
        ising_basis_energies_checked=examined,qiskit_probability_comparisons=qiskit_checked,
        qubit_cap_includes_slack=True,seeded_counts_reproducible=True,
        core_feasibility_independent_of_energy_zero=True,reference_does_not_choose_actions=True,
        no_physical_quantum_execution=True)


def save_result(result: dict, directory) -> None:
    """Save auditable result/QASM/counts into a new empty directory."""
    directory = Path(directory)
    if directory.exists() and any(directory.iterdir()):
        raise ValueError("Use an empty directory to preserve existing quantum evidence")
    directory.mkdir(parents=True,exist_ok=True)
    (directory/"result.json").write_text(json.dumps(result,indent=2)+"\n")
    if result.get("problem"):
        (directory/"problem.json").write_text(json.dumps(result["problem"],indent=2)+"\n")
    if result.get("sampling"):
        sampling = result["sampling"]
        (directory/"circuit.qasm").write_text(sampling["circuit"]["openqasm2"])
        (directory/"raw-counts.json").write_text(json.dumps(sampling["raw_counts"],indent=2)+"\n")


def main():
    import argparse
    from .qubo import build_qubo
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input",type=Path,help="JSON with candidates, conflicts and capacities (or decision evidence)")
    parser.add_argument("--output",type=Path)
    parser.add_argument("--layers",type=int,choices=(1,2),default=1)
    parser.add_argument("--shots",type=int,default=1024)
    parser.add_argument("--seed",type=int,default=0)
    parser.add_argument("--optimizer",choices=("coordinate","scipy"),default="coordinate")
    parser.add_argument("--evaluations",type=int,default=256)
    args = parser.parse_args()
    data = json.loads(args.input.read_text())
    q = build_qubo(data["candidates"],data.get("conflicts",[]),data.get("capacities",{}))
    result = select_qaoa(q,seed=args.seed,layers=args.layers,shots=args.shots,
                         max_evaluations=args.evaluations,optimizer=args.optimizer)
    if args.output:
        save_result(result,args.output)
    print(json.dumps({k:v for k,v in result.items() if k not in ("sampling",)},indent=2))


if __name__ == "__main__":
    main()
