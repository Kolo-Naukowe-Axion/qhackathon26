"""Simulated QAOA adapter for frozen catering QUBO bundles.

Three variants share one optimizer loop, budget accounting and sampler:

- ``standard``: |+>^n start, single-gamma cost layer on the full literal
  (penalized) QUBO, transverse-field X mixer. Full 2^n statevector.
- ``xy``: equal superposition of the declared one-hot sector (a W-state per
  block), single-gamma cost layer on the literal energy, XY ring mixer inside
  every one-hot block. Simulated exactly on the one-hot sector only.
- ``xy_multiangle_warm``: the integrator pilot's ansatz (independent objective
  and conflict angles per layer, warm start biased to an incumbent), but with
  the same optimizer as the other variants.

Conventions follow the methods tutorial (sections 6 and 8): basis index bit i
is x_i in ``variable_order`` (little-endian, Qiskit order), the cost layer is
exp(-i gamma E(x)/scale) and the X mixer is exp(-i beta X) on every qubit.
Training uses exact simulator probabilities (CVaR or expectation); only the
final returned samples are shot-based. No sample is repaired. Simulation only:
this module never contacts a QPU or service.
"""
import argparse
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import time

import numpy as np

from ..contracts import load_bundle, method_result, save_json
from ..qubo import checked_bits, energy

METHOD_VERSION = 2
VARIANTS = ("standard", "xy", "xy_multiangle_warm")
OPTIMIZERS = ("COBYLA", "Nelder-Mead", "L-BFGS-B", "random", "layerwise")
MAX_STANDARD_QUBITS = 26
DEFAULTS = dict(variant="xy", depth=1, optimizer="COBYLA", restarts=4, loss="cvar", alpha=0.1,
                shots=4096, seed=2026, energy_scale=None, gamma_range=[0.0, math.pi],
                beta_range=[-math.pi/2, math.pi/2], incumbent_ids=[], exploration=0.15)


class _BudgetExhausted(Exception):
    pass


# ---------------------------------------------------------------------------
# Diagonal energy tables
# ---------------------------------------------------------------------------

def _magnitude(constant, linear, quadratic):
    return abs(int(constant)) + sum(abs(int(c)) for c in linear) + sum(abs(int(t["value"])) for t in quadratic)


def energy_table(constant, linear, quadratic, n):
    """Exact int64 E(x) for every basis index; bit i of the index is x_i."""
    if _magnitude(constant, linear, quadratic) >= 2**63:
        raise ValueError("Energy table exceeds int64 range")
    index = np.arange(1 << n, dtype=np.int64)
    table = np.full(1 << n, int(constant), dtype=np.int64)
    bits = {}
    def bit(i):
        if i not in bits:
            bits[i] = ((index >> i) & 1).astype(bool)
        return bits[i]
    for i, c in enumerate(linear):
        if int(c):
            table[bit(i)] += int(c)
    for t in quadratic:
        if int(t["value"]):
            table[bit(t["i"]) & bit(t["j"])] += int(t["value"])
    return table


def _full_space(bundle):
    n = len(bundle["linear"])
    if n > MAX_STANDARD_QUBITS:
        raise ValueError(f"Standard variant simulates the full 2^n statevector; {n} qubits exceeds {MAX_STANDARD_QUBITS}")
    literal = energy_table(bundle["constant"], bundle["linear"], bundle["quadratic"], n)
    space = dict(kind="full", n=n, states=1 << n, energy=literal)
    if "objective" in bundle:
        objective = bundle["objective"]
        obj = energy_table(objective["constant"], objective["linear"], objective.get("quadratic", []), n)
        space["valid"] = literal == obj
    else:
        space["valid"] = np.ones(1 << n, dtype=bool)
    return space


def _sector_space(bundle):
    from ..meal_blocks import sector_data
    sector = sector_data(bundle)
    return dict(kind="onehot_sector", n=len(bundle["linear"]), states=sector["states"], energy=sector["energy"],
                objective=sector["objective"], violations=sector["violations"], valid=sector["valid"],
                dims=sector["dims"], sector=sector)


# ---------------------------------------------------------------------------
# Kernels
# ---------------------------------------------------------------------------

def apply_x_mixer(state, n, beta):
    """exp(-i beta sum_q X_q), applied qubit by qubit in place on a copy."""
    output = np.array(state, dtype=np.complex128, copy=True)
    c, s = math.cos(beta), -1j*math.sin(beta)
    for q in range(n):
        view = output.reshape(-1, 2, 1 << q)
        a = view[:, 0, :].copy()
        view[:, 0, :] = c*a + s*view[:, 1, :]
        view[:, 1, :] = s*a + c*view[:, 1, :]
    return output


def initial_state(bundle, space, variant, config):
    if variant == "standard":
        return np.full(space["states"], 1/math.sqrt(space["states"]), dtype=np.complex128)
    if variant == "xy":
        return np.full(space["states"], 1/math.sqrt(space["states"]), dtype=np.complex128)
    from ..meal_search import warm_state
    state = warm_state(bundle, space["sector"], set(config["incumbent_ids"]), config["exploration"])
    return state.astype(np.complex128)


def evolve(bundle, space, variant, initial, params, scale):
    """Apply the p QAOA layers; params is a flat array of 2p (or 3p) angles."""
    state = initial
    if variant == "standard":
        for gamma, beta in np.reshape(params, (-1, 2)):
            state = apply_x_mixer(state*np.exp(-1j*gamma*(space["energy"]/scale)), space["n"], beta)
        return state
    from ..meal_blocks import xy_mix
    if variant == "xy":
        for gamma, beta in np.reshape(params, (-1, 2)):
            state = xy_mix(state*np.exp(-1j*gamma*(space["energy"]/scale)), space["dims"], beta)
        return state
    for gamma_cost, gamma_conflict, beta in np.reshape(params, (-1, 3)):
        phase = gamma_cost*(space["objective"]/scale) + gamma_conflict*space["violations"]
        state = xy_mix(state*np.exp(-1j*phase), space["dims"], beta)
    return state


def cvar(probabilities, energies, order, alpha):
    """Mean energy of the lowest-energy probability mass alpha (Barkoutsos et al.)."""
    mass = probabilities[order]
    before = np.cumsum(mass) - mass
    taken = np.minimum(mass, np.maximum(0, alpha - before))
    return float(taken @ energies[order] / alpha)


def _bits(bundle, space, index):
    if space["kind"] == "full":
        return [(index >> i) & 1 for i in range(space["n"])]
    from ..meal_blocks import sector_bits
    return sector_bits(bundle, space["sector"], index)


def default_scale(bundle):
    """Common phase normalization: U weight for catering bundles, else max |coefficient|."""
    weights = bundle.get("objective", {}).get("weights", {})
    if weights.get("U"):
        return float(max(1, int(weights["U"])))
    return float(max([1] + [abs(int(c)) for c in bundle["linear"]] + [abs(int(t["value"])) for t in bundle["quadratic"]]))


# ---------------------------------------------------------------------------
# Training loop
# ---------------------------------------------------------------------------

def _random_params(rng, variant, depth, config):
    gamma, beta = config["gamma_range"], config["beta_range"]
    per = 3 if variant == "xy_multiangle_warm" else 2
    out = []
    for _ in range(depth):
        if per == 3:
            out += [rng.uniform(*gamma), rng.uniform(*gamma), rng.uniform(*beta)]
        else:
            out += [rng.uniform(*gamma), rng.uniform(*beta)]
    return np.array(out, dtype=float)


def train(bundle, space, variant, config, budget, rng, started):
    from scipy.optimize import minimize
    scale = float(config["energy_scale"] or default_scale(bundle))
    initial = initial_state(bundle, space, variant, config)
    energies = space["energy"].astype(np.float64)
    order = np.argsort(space["energy"], kind="stable")
    limit = int(budget.get("training_objective_evaluations", 200))
    wall = float(budget.get("wall_time_limit_s", 600))
    if limit < 1 or not math.isfinite(wall) or wall <= 0:
        raise ValueError("Positive evaluation and wall-time budgets required")
    trace, best = [], dict(loss=math.inf, params=None)
    counter = dict(evaluations=0, timed_out=False)

    def loss_of(params, start_index):
        if counter["evaluations"] >= min(limit, counter.get("stage_cap", limit)):
            raise _BudgetExhausted
        if time.monotonic() - started > wall:
            counter["timed_out"] = True
            raise _BudgetExhausted
        probabilities = np.abs(evolve(bundle, space, variant, initial, params, scale))**2
        if config["loss"] == "cvar":
            value = cvar(probabilities, energies, order, float(config["alpha"]))
        else:
            value = float(probabilities @ energies)
        counter["evaluations"] += 1
        trace.append(dict(evaluation=counter["evaluations"], start=start_index, loss=value,
                          params=[float(v) for v in params]))
        if value < best["loss"]:
            best.update(loss=value, params=np.array(params, dtype=float), start=start_index)
        return value

    restarts = int(config["restarts"])
    if config["optimizer"] == "random":
        try:
            for j in range(limit):
                loss_of(_random_params(rng, variant, int(config["depth"]), config), j)
        except _BudgetExhausted:
            pass
    elif config["optimizer"] == "layerwise":
        # INTERP-style growth: optimize depth 1, then extend the best angles by one
        # layer (initialized at half the previous layer) and re-optimize, up to p.
        # Depth d receives a share of the budget proportional to d; COBYLA restarts
        # near the stage's best point if it converges before its share is spent.
        depth = int(config["depth"])
        if limit < depth:
            raise ValueError("Layerwise training needs at least one evaluation per depth")
        per = 3 if variant == "xy_multiangle_warm" else 2
        total, x = depth*(depth + 1)//2, None
        for d in range(1, depth + 1):
            cap = limit if d == depth else min(limit*(d*(d + 1)//2)//total, limit - (depth - d))
            counter["stage_cap"] = cap
            x = _random_params(rng, variant, 1, config) if x is None else np.concatenate([x, 0.5*x[-per:]])
            best.update(loss=math.inf, params=None)
            try:
                while counter["evaluations"] < cap:
                    minimize(loss_of, x, args=(d,), method="COBYLA",
                             options=dict(maxiter=max(len(x) + 2, cap - counter["evaluations"]), rhobeg=0.3))
                    if best["params"] is not None:
                        x = best["params"]
                    if counter["evaluations"] < cap:
                        x = x + rng.normal(0, 0.2, len(x))
            except _BudgetExhausted:
                if counter["timed_out"]:
                    break
            if best["params"] is not None:
                x = best["params"]
        counter.pop("stage_cap", None)
        if best["params"] is not None and len(best["params"]) != depth*per:
            raise RuntimeError("Wall-time budget ended before the final depth was trained")
    else:
        per_start = max(1, limit // max(1, restarts))
        for start_index in range(restarts):
            x0 = _random_params(rng, variant, int(config["depth"]), config)
            # COBYLA needs at least len(x0)+2 calls; the global counter still caps the total.
            per_start = max(per_start, len(x0) + 2)
            try:
                options = dict(maxiter=per_start) if config["optimizer"] != "L-BFGS-B" else dict(maxfun=per_start)
                minimize(loss_of, x0, args=(start_index,), method=config["optimizer"], options=options)
            except _BudgetExhausted:
                if counter["timed_out"] or counter["evaluations"] >= limit:
                    break
            if counter["evaluations"] >= limit:
                break
    if best["params"] is None:
        raise RuntimeError("Budget allowed no objective evaluation")
    return best, trace, counter, scale, initial


# ---------------------------------------------------------------------------
# Public adapter
# ---------------------------------------------------------------------------

def solve_qubo(bundle, budget=None, method_config=None, output_dir=None):
    """Contract adapter: returns raw normalized samples; the central evaluator decodes/checks them."""
    started = time.monotonic()
    budget = dict(budget or {})
    config = dict(DEFAULTS, **(method_config or {}))
    variant = config["variant"]
    if variant not in VARIANTS:
        raise ValueError(f"variant must be one of {VARIANTS}")
    if config["optimizer"] not in OPTIMIZERS:
        raise ValueError(f"optimizer must be one of {OPTIMIZERS}")
    if config["loss"] not in ("cvar", "expectation") or not 0 < float(config["alpha"]) <= 1:
        raise ValueError("loss must be cvar (0<alpha<=1) or expectation")
    if budget.get("allowed_external_execution"):
        raise ValueError("This adapter is simulation-only; external execution is not supported")
    if output_dir is not None:
        output_dir = Path(output_dir)
        if output_dir.exists():
            raise ValueError("Choose a fresh output directory; evidence is never overwritten")
    depth = int(config["depth"])
    if depth < 0:
        raise ValueError("Nonnegative depth required")
    rng = np.random.default_rng(int(config["seed"]))
    shots = int(budget.get("shots", config["shots"]))
    if shots < 1:
        raise ValueError("Positive shot count required")

    build_start = time.monotonic()
    space = _full_space(bundle) if variant == "standard" else _sector_space(bundle)
    build_s = time.monotonic() - build_start

    train_start = time.monotonic()
    if depth == 0:
        scale = float(config["energy_scale"] or default_scale(bundle))
        initial = initial_state(bundle, space, variant, config)
        best, trace, counter = dict(loss=None, params=np.zeros(0)), [], dict(evaluations=0, timed_out=False)
    else:
        best, trace, counter, scale, initial = train(bundle, space, variant, config, budget, rng, started)
    train_s = time.monotonic() - train_start

    sample_start = time.monotonic()
    state = evolve(bundle, space, variant, initial, best["params"], scale) if depth else initial
    probabilities = np.abs(state)**2
    norm = float(probabilities.sum())
    if not math.isclose(norm, 1.0, abs_tol=1e-9):
        raise AssertionError(f"Nonunitary evolution: norm {norm}")
    ground = space["energy"] == space["energy"].min()
    distribution = dict(norm=norm, expected_energy=float(probabilities @ space["energy"].astype(np.float64)),
                        valid_probability=float(probabilities[space["valid"]].sum()),
                        ground_probability=float(probabilities[ground].sum()),
                        ground_states=int(ground.sum()), simulated_states=int(space["states"]),
                        simulated_space=space["kind"])
    indices, counts = np.unique(rng.choice(space["states"], size=shots, p=probabilities/norm), return_counts=True)
    samples = []
    for index, count in zip(indices, counts):
        bits = [int(b) for b in _bits(bundle, space, int(index))]
        literal = energy(bundle, checked_bits(bundle, bits))
        if literal != int(space["energy"][index]):
            raise AssertionError("Simulator energy differs from literal QUBO energy")
        samples.append(dict(bits=bits, count=int(count), reported_energy=str(literal)))
    sample_s = time.monotonic() - sample_start

    method_id = f"qaoa_{variant}"
    result = method_result(bundle, method_id, samples,
                           timings=dict(build_s=build_s, training_s=train_s, sampling_s=sample_s,
                                        total_s=time.monotonic()-started),
                           work=dict(training_objective_evaluations=counter["evaluations"],
                                     training_evaluation_kind="exact simulator probabilities",
                                     evaluation_circuits=1, shots_per_circuit=shots, total_shots=shots,
                                     budget=budget))
    result.update(method_version=METHOD_VERSION, execution_kind="quantum_simulation",
                  status="timeout" if counter["timed_out"] else "completed")
    result["configuration"] = dict(
        variant=variant, depth=depth, optimizer=config["optimizer"], restarts=int(config["restarts"]),
        loss=config["loss"], alpha=float(config["alpha"]), seed=int(config["seed"]), energy_scale=scale,
        gamma_range=list(config["gamma_range"]), beta_range=list(config["beta_range"]),
        initial_state={"standard": "uniform |+>^n", "xy": "uniform one-hot sector (W-state per block)",
                       "xy_multiangle_warm": f"incumbent-biased one-hot product, exploration={config['exploration']}"}[variant],
        incumbent_ids=list(config["incumbent_ids"]) if variant == "xy_multiangle_warm" else [],
        mixer={"standard": "X on every qubit", "xy": "XY ring within each one-hot block",
               "xy_multiangle_warm": "XY ring within each one-hot block"}[variant],
        cost_layer=("exp(-i gamma_cost obj/scale - i gamma_conflict violations)" if variant == "xy_multiangle_warm"
                    else "exp(-i gamma E_literal/scale)"),
        best_params=[float(v) for v in best["params"]], best_training_loss=best["loss"],
        distribution=distribution, repair=False,
        seed_support="numpy default_rng seeds restarts and sampling; scipy optimizers deterministic given x0")
    result["environment"].update(numpy=np.__version__, scipy=importlib.metadata.version("scipy"))
    if output_dir is not None:
        output_dir.mkdir(parents=True)
        save_json(output_dir / "training.json", dict(trace=trace, evaluations=counter["evaluations"]))
        result["raw_artifacts"] = [dict(path=str(output_dir / name),
                                        sha256=hashlib.sha256((output_dir / name).read_bytes()).hexdigest())
                                   for name in ("training.json",)]
        save_json(output_dir / "result.json", result)
        save_json(output_dir / "artifacts.json", dict(files={name:
            hashlib.sha256((output_dir / name).read_bytes()).hexdigest()
            for name in ("training.json", "result.json")}))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--variant", choices=VARIANTS, default=DEFAULTS["variant"])
    parser.add_argument("--depth", type=int, default=DEFAULTS["depth"])
    parser.add_argument("--optimizer", choices=OPTIMIZERS, default=DEFAULTS["optimizer"])
    parser.add_argument("--restarts", type=int, default=DEFAULTS["restarts"])
    parser.add_argument("--loss", choices=("cvar", "expectation"), default=DEFAULTS["loss"])
    parser.add_argument("--alpha", type=float, default=DEFAULTS["alpha"])
    parser.add_argument("--evaluations", type=int, default=200)
    parser.add_argument("--wall-seconds", type=float, default=600)
    parser.add_argument("--shots", type=int, default=DEFAULTS["shots"])
    parser.add_argument("--seed", type=int, default=DEFAULTS["seed"])
    args = parser.parse_args()
    result = solve_qubo(load_bundle(args.bundle),
                        dict(training_objective_evaluations=args.evaluations, wall_time_limit_s=args.wall_seconds,
                             shots=args.shots),
                        dict(variant=args.variant, depth=args.depth, optimizer=args.optimizer, restarts=args.restarts,
                             loss=args.loss, alpha=args.alpha, seed=args.seed),
                        args.output)
    d = result["configuration"]["distribution"]
    print(json.dumps(dict(method=result["method_id"], status=result["status"],
                          evaluations=result["work"]["training_objective_evaluations"],
                          valid_probability=d["valid_probability"], ground_probability=d["ground_probability"],
                          ground_states=d["ground_states"], wrote=str(args.output))))


if __name__ == "__main__":
    main()
