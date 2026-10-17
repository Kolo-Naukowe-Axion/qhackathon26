"""Same-QUBO exact enumeration and annealing, without feasibility repair."""
import math
import time
import numpy as np
from ..contracts import method_result
from ..qubo import energy


def energy_chunks(bundle, chunk_size=65536):
    n = bundle["size"]["binary_variables"]
    if n > 22:
        raise ValueError("Dense exact enumeration capped at 22 bits")
    magnitude = abs(int(bundle["constant"])) + sum(abs(int(v)) for v in bundle["linear"])
    magnitude += sum(abs(int(t["value"])) for t in bundle["quadratic"])
    if magnitude >= 2**63:
        raise ValueError("Exact enumeration int64 range exceeded")
    linear = np.array(list(map(int, bundle["linear"])), dtype=np.int64)
    for start in range(0, 1 << n, chunk_size):
        masks = np.arange(start, min(start + chunk_size, 1 << n), dtype=np.uint64)
        bits = ((masks[:, None] >> np.arange(n, dtype=np.uint64)) & 1).astype(np.uint8)
        values = bits @ linear + int(bundle["constant"])
        for term in bundle["quadratic"]:
            # Cast first: uint8 multiplication by a negative/large coefficient must not overflow.
            values += int(term["value"]) * (bits[:, term["i"]].astype(np.int64) * bits[:, term["j"]])
        yield masks, bits, values


def solve_exact(bundle, budget=None, method_config=None, output_dir=None):
    start = time.monotonic()
    best, winners, ground_count = None, [], 0
    for masks, bits, values in energy_chunks(bundle):
        local = int(values.min())
        if best is None or local < best:
            best, winners, ground_count = local, [], 0
        if local == best:
            indices = np.flatnonzero(values == best)
            ground_count += len(indices)
            winners += [dict(bits=[int(v) for v in bits[i]], count=1, reported_energy=str(best)) for i in indices[:64]]
            winners = winners[:64]
    n = bundle["size"]["binary_variables"]
    return method_result(bundle, "qubo_exact_enumeration", winners,
                         timings=dict(total_s=time.monotonic()-start),
                         work=dict(bitstrings=1 << n, ground_states=ground_count, retained_ground_states=len(winners)),
                         reference=dict(status="OPTIMAL", objective=str(best), bound=str(best),
                                        scope="Identical literal QUBO, all bitstrings"))


def solve_qubo(bundle, budget=None, method_config=None, output_dir=None):
    """Seeded Metropolis SA with exact integer local energy deltas."""
    budget, cfg = budget or {}, method_config or {}
    restarts, sweeps = int(cfg.get("restarts", 8)), int(cfg.get("sweeps", 200))
    if restarts < 1 or sweeps < 1:
        raise ValueError("Positive restarts/sweeps required")
    limit = float(budget.get("wall_time_limit_s", 10))
    if not math.isfinite(limit) or limit <= 0:
        raise ValueError("Positive finite time limit required")
    rng = np.random.default_rng(int(cfg.get("seed", 2026)))
    n = bundle["size"]["binary_variables"]
    linear = list(map(int, bundle["linear"]))
    neighbors = [[] for _ in range(n)]
    for t in bundle["quadratic"]:
        i, j, v = t["i"], t["j"], int(t["value"])
        neighbors[i].append((j, v)); neighbors[j].append((i, v))
    start = time.monotonic()
    scale = max([1] + [abs(v) for v in linear] + [abs(int(t["value"])) for t in bundle["quadratic"]])
    samples, flips, completed = [], 0, 0
    for run in range(restarts):
        bits = rng.integers(0, 2, n).tolist()
        current = energy(bundle, bits)
        best, best_bits = current, bits.copy()
        for sweep in range(sweeps):
            temperature = scale * (0.002 ** (sweep / max(1, sweeps - 1)))
            for i in rng.permutation(n):
                i = int(i)
                delta = (1 - 2*bits[i]) * (linear[i] + sum(v*bits[j] for j, v in neighbors[i]))
                flips += 1
                if delta <= 0 or rng.random() < math.exp(-min(745, delta / temperature)):
                    bits[i] = 1-bits[i]
                    current += delta
                    if current < best:
                        best, best_bits = current, bits.copy()
            if time.monotonic()-start > limit:
                break
        if energy(bundle, best_bits) != best:
            raise AssertionError("Incremental SA energy mismatch")
        samples.append(dict(bits=best_bits, count=1, reported_energy=str(best)))
        completed += 1
        if time.monotonic()-start > limit:
            break
    result = method_result(bundle, "qubo_sa", samples,
                           timings=dict(total_s=time.monotonic()-start),
                           work=dict(bit_flip_proposals=flips, completed_restarts=completed,
                                     requested_restarts=restarts, requested_sweeps=sweeps))
    result["configuration"] = dict(seed=cfg.get("seed", 2026), initializer="seeded random bits",
                                   restarts=restarts, sweeps=sweeps, repair=False)
    if completed < restarts:
        result["status"] = "timeout"
    return result
