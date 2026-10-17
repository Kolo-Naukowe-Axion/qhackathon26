"""Exact fixed-pool action selection QUBOs and transparent classical solvers.

This module does not encode a whole factory. The caller must enumerate actions
whose boundary conditions are valid and list every interaction between actions.
An optimum here is an optimum over that candidate pool, not over all schedules.

Energy uses each upper-triangular coefficient once: offset + linear[i]*x[i]
+ quadratic[i,j]*x[i]*x[j]. There is no hidden factor of two.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import math
import random
import time
from collections import Counter
from typing import Any, Iterable, Mapping, Sequence


@dataclass(frozen=True)
class Candidate:
    id: str
    reward: float
    resources: Mapping[str, int]


@dataclass
class QUBO:
    candidates: tuple[Candidate, ...]
    conflicts: tuple[tuple[int, int], ...]
    capacities: dict[str, int]
    linear: list[float]
    quadratic: dict[tuple[int, int], float]
    offset: float
    penalty: float
    slack: dict[str, tuple[tuple[int, int], ...]]
    capacity_encoding: dict[str, str]
    resource_scales: dict[str, int] = field(default_factory=dict)

    @property
    def size(self) -> int:
        return len(self.linear)

    def energy(self, bits: Sequence[int]) -> float:
        if len(bits) != self.size or any(b not in (0, 1) for b in bits):
            raise ValueError("Expected one binary value per QUBO variable")
        return (self.offset + sum(a*b for a, b in zip(self.linear, bits))
                + sum(a*bits[i]*bits[j] for (i, j), a in self.quadratic.items()))

    def feasible(self, selected: Iterable[int]) -> bool:
        chosen = set(selected)
        if any(i < 0 or i >= len(self.candidates) for i in chosen):
            return False
        if any(i in chosen and j in chosen for i, j in self.conflicts):
            return False
        return all(sum(self.candidates[i].resources.get(r, 0) for i in chosen) <= cap
                   for r, cap in self.capacities.items())

    def encode(self, selected: Iterable[int]) -> list[int]:
        """Represent a feasible core selection with zero constraint penalty."""
        chosen = set(selected)
        if not self.feasible(chosen):
            raise ValueError("Cannot encode an infeasible selection with zero penalty")
        bits = [int(i in chosen) for i in range(len(self.candidates))]
        bits.extend([0] * (self.size - len(bits)))
        for resource, slack_bits in self.slack.items():
            remainder = self.capacities[resource] - sum(
                self.candidates[i].resources.get(resource, 0) for i in chosen)
            # Bounded binary weights are a complete sequence; descending greedy
            # represents every integer in [0, capacity], including duplicate top weights.
            for index, weight in reversed(slack_bits):
                if weight <= remainder:
                    bits[index] = 1
                    remainder -= weight
            if remainder:
                raise AssertionError("Internal bounded-slack representation error")
        return bits

    def summary(self) -> dict[str, Any]:
        nonzero = [abs(c) for c in self.linear if c] + [abs(c) for c in self.quadratic.values() if c]
        return {"core_variables": len(self.candidates),
                "slack_variables": self.size-len(self.candidates),
                "variables": self.size, "couplers": len(self.quadratic),
                "penalty": self.penalty,
                "capacity_encoding": dict(self.capacity_encoding),
                "resource_integer_gcd_scales": dict(self.resource_scales),
                "coefficient_abs_min": min(nonzero, default=0),
                "coefficient_abs_max": max(nonzero, default=0),
                "convention": "upper_triangular_once",
                "domain": "fixed_candidate_pool"}


def _integer(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{label} must be a nonnegative integer")
    return value


def _bounded_weights(capacity: int) -> list[int]:
    weights, represented = [], 0
    while represented < capacity:
        weight = min(1 << len(weights), capacity - represented)
        weights.append(weight)
        represented += weight
    return weights


def build_qubo(candidates: Sequence[Candidate | Mapping[str, Any]],
               conflicts: Iterable[tuple[str, str]] = (),
               capacities: Mapping[str, int] | None = None,
               penalty: float | None = None) -> QUBO:
    """Build -reward + P*conflicts + P*integer-capacity squared residuals.

    Capacity resources absent from ``capacities`` are rejected, never ignored.
    P must be greater than the total positive reward. Since the empty selection
    is feasible and every nonzero integer residual costs at least P, every
    global QUBO minimizer is feasible. This is sufficient, not a tight bound.
    """
    normalized = []
    caps = {str(r): _integer(v, f"Capacity {r}") for r, v in (capacities or {}).items()}
    for item in candidates:
        c = item if isinstance(item, Candidate) else Candidate(
            str(item["id"]), float(item["reward"]), dict(item.get("resources", {})))
        if not c.id or not math.isfinite(c.reward):
            raise ValueError("Candidate IDs must be nonempty and rewards finite")
        resources = {str(r): _integer(v, f"Demand {r}") for r, v in c.resources.items()}
        missing = resources.keys() - caps.keys()
        if missing:
            raise ValueError(f"Missing capacities for resources: {sorted(missing)}")
        normalized.append(Candidate(c.id, float(c.reward), resources))
    ids = {c.id: i for i, c in enumerate(normalized)}
    if len(ids) != len(normalized):
        raise ValueError("Candidate IDs must be unique")
    pairs = set()
    for a, b in conflicts:
        if a not in ids or b not in ids:
            raise ValueError(f"Unknown conflict endpoint {(a, b)}")
        if a == b:
            raise ValueError("Self-conflicts are invalid; remove the candidate instead")
        pairs.add(tuple(sorted((ids[a], ids[b]))))
    bound = sum(max(c.reward, 0.0) for c in normalized)
    p = float(bound + 1.0 if penalty is None else penalty)
    if not math.isfinite(p) or p <= bound:
        raise ValueError("Penalty must be finite and strictly exceed total positive reward")
    # For integer nonnegative demands, sum(a_i*x_i)<=B is exactly equivalent
    # to sum((a_i/g)*x_i)<=floor(B/g), g=gcd(a_i). This removes unit precision
    # from slack counts without relaxing any feasible core selection.
    scales={r:math.gcd(*(c.resources.get(r,0) for c in normalized)) or 1 for r in caps}
    normalized=[Candidate(c.id,c.reward,{r:v//scales[r] for r,v in c.resources.items()}) for c in normalized]
    caps={r:cap//scales[r] for r,cap in caps.items()}
    q = QUBO(tuple(normalized), tuple(sorted(pairs)), caps,
             [-c.reward for c in normalized], {}, 0.0, p, {}, {})
    q.resource_scales=scales
    for pair in q.conflicts:
        q.quadratic[pair] = q.quadratic.get(pair, 0.0) + p
    for resource, capacity in caps.items():
        terms = [(i, c.resources.get(resource, 0)) for i, c in enumerate(q.candidates)
                 if c.resources.get(resource, 0)]
        if sum(value for _, value in terms) <= capacity:
            q.capacity_encoding[resource] = "redundant_upper_bound_removed"
            continue
        if capacity == 0:
            q.capacity_encoding[resource] = "zero_capacity_linear"
            for i, _ in terms:
                q.linear[i] += p
            continue
        if capacity == 1 and all(value == 1 for _, value in terms):
            q.capacity_encoding[resource] = "unit_capacity_pairwise_no_slack"
            for k, (i, _) in enumerate(terms):
                for j, _ in terms[k+1:]:
                    pair = (i, j)
                    q.quadratic[pair] = q.quadratic.get(pair, 0.0) + p
            continue
        q.capacity_encoding[resource] = "bounded_binary_squared_slack"
        slack = []
        for weight in _bounded_weights(capacity):
            slack.append((len(q.linear), weight))
            q.linear.append(0.0)
        q.slack[resource] = tuple(slack)
        terms += slack
        q.offset += p * capacity**2
        for i, ai in terms:
            q.linear[i] += p * (ai*ai - 2*capacity*ai)
        for k, (i, ai) in enumerate(terms):
            for j, aj in terms[k+1:]:
                key = (min(i, j), max(i, j))
                q.quadratic[key] = q.quadratic.get(key, 0.0) + 2*p*ai*aj
    q.quadratic = {key: value for key, value in q.quadratic.items() if value}
    return q


def exact_reference(q: QUBO, max_candidates: int = 24) -> dict[str, Any]:
    """Enumerate core selections independently of QUBO coefficients/slack."""
    n = len(q.candidates)
    if n > max_candidates:
        raise ValueError(f"Exact enumeration capped at {max_candidates} candidates")
    best_reward, best = 0.0, []
    feasible_count = 0
    for mask in range(1 << n):
        chosen = [i for i in range(n) if mask >> i & 1]
        if not q.feasible(chosen):
            continue
        feasible_count += 1
        reward = sum(q.candidates[i].reward for i in chosen)
        if reward > best_reward:
            best_reward, best = reward, chosen
    return {"indices": best, "selected": [q.candidates[i].id for i in best],
            "reward": best_reward, "proven_optimal_within_pool": True,
            "feasible_selections": feasible_count, "selections_examined": 1 << n}


def greedy_reference(q: QUBO, preferred: Iterable[int] = ()) -> list[int]:
    """Deterministic feasible repair/fill. Negative rewards are never inserted."""
    preferred_set = set(preferred)
    order = sorted(range(len(q.candidates)),
                   key=lambda i: (i not in preferred_set, -q.candidates[i].reward, q.candidates[i].id))
    chosen = []
    for i in order:
        if q.candidates[i].reward > 0 and q.feasible(chosen + [i]):
            chosen.append(i)
    return chosen


def anneal(q: QUBO, seed: int = 0, sweeps: int = 200,
           restarts: int = 8) -> dict[str, Any]:
    """Seeded single-flip Metropolis SA; raw sample retained before repair."""
    if sweeps < 1 or restarts < 1:
        raise ValueError("sweeps and restarts must be positive")
    rng = random.Random(seed)
    adjacency: list[list[tuple[int, float]]] = [[] for _ in q.linear]
    for (i, j), value in q.quadratic.items():
        adjacency[i].append((j, value))
        adjacency[j].append((i, value))
    greedy = greedy_reference(q)
    best_bits = q.encode(greedy)
    best_energy = q.energy(best_bits)
    scale = max([abs(a) for a in q.linear] + [1.0])
    high, low = scale, max(scale*0.001, 0.001)
    indices = list(range(q.size))
    for restart in range(restarts):
        bits = q.encode(greedy) if restart == 0 else [rng.randrange(2) for _ in q.linear]
        fields = [q.linear[i] + sum(a*bits[j] for j, a in adjacency[i]) for i in range(q.size)]
        energy = q.energy(bits)
        if energy < best_energy:
            best_energy, best_bits = energy, bits[:]
        for sweep in range(sweeps):
            temperature = high*(low/high)**(sweep/max(1, sweeps-1))
            rng.shuffle(indices)
            for i in indices:
                direction = 1-2*bits[i]
                delta = direction*fields[i]
                if delta <= 0 or rng.random() < math.exp(-delta/temperature):
                    bits[i] ^= 1
                    energy += delta
                    for j, value in adjacency[i]:
                        fields[j] += direction*value
                    if energy < best_energy - 1e-9:
                        best_energy, best_bits = energy, bits[:]
    return {"bits": best_bits, "energy": q.energy(best_bits),
            "seed": seed, "sweeps": sweeps, "restarts": restarts,
            "warm_start": "feasible_reward_greedy_first_restart"}


def select(candidates: Sequence[Candidate | Mapping[str, Any]],
           conflicts: Iterable[tuple[str, str]] = (),
           capacities: Mapping[str, int] | None = None, *, seed: int = 0,
           method: str = "sa", sweeps: int = 200, restarts: int = 8,
           exact_limit: int = 24) -> dict[str, Any]:
    """Select compatible actions, with explicit solver and repair provenance."""
    started = time.perf_counter()
    conflicts=tuple(conflicts)
    q = build_qubo(candidates, conflicts, capacities)
    if method == "qaoa":
        from .quantum import select_qaoa
        return select_qaoa(q,seed=seed)
    if method == "uniform":
        if q.size>5:
            result=select(candidates,conflicts,capacities,seed=seed,method="sa",sweeps=100,restarts=4)
            result.update(requested_method="uniform",fallback_reason="Same five-total-bit cap as QAOA",quantum_executed=False)
            return result
        rng=random.Random(seed ^ 0xB451);shots=1024
        counts=Counter(rng.randrange(1<<q.size) for _ in range(shots));eligible=[]
        for state,count in counts.items():
            bits=[(state>>i)&1 for i in range(q.size)]
            chosen=[i for i in range(len(q.candidates)) if bits[i]]
            if q.feasible(chosen):
                reward=sum(q.candidates[i].reward for i in chosen)
                eligible.append((reward,-q.energy(bits),count,-state,chosen,bits))
        if eligible:
            reward,_,_,_,chosen,bits=max(eligible)
            repaired=False
        else:
            chosen=greedy_reference(q);bits=q.encode(chosen)
            reward=sum(q.candidates[i].reward for i in chosen);repaired=True
        return dict(selected=[q.candidates[i].id for i in chosen],reward=reward,feasible=q.feasible(chosen),
            method="uniform_born_baseline",quantum_executed=False,proven_optimal_within_pool=False,
            qubo=q.summary(),raw=dict(bits=bits,energy=q.energy(bits),feasible=q.feasible(chosen)),
            repaired=repaired,reference=exact_reference(q),shots=shots,
            raw_counts={format(s,f"0{q.size}b"):n for s,n in sorted(counts.items())},
            elapsed_seconds=time.perf_counter()-started)
    reference = None
    if method == "exact":
        reference = exact_reference(q, exact_limit)
        selected = reference["indices"]
        raw = {"bits": q.encode(selected), "energy": -reference["reward"]}
    elif method == "greedy":
        selected = greedy_reference(q)
        raw = {"bits": q.encode(selected), "energy": q.energy(q.encode(selected))}
    elif method == "sa":
        raw = anneal(q, seed, sweeps, restarts)
        selected = [i for i, bit in enumerate(raw["bits"][:len(q.candidates)]) if bit]
    elif method == "exact_random_tie":
        reference=exact_reference(q,exact_limit);rng=random.Random(seed);selected=[];ties=0
        for mask in range(1<<len(q.candidates)):
            chosen=[i for i in range(len(q.candidates)) if mask>>i&1]
            if q.feasible(chosen) and math.isclose(sum(q.candidates[i].reward for i in chosen),reference["reward"],abs_tol=1e-8):
                ties+=1
                if rng.randrange(ties)==0:selected=chosen
        raw=dict(bits=q.encode(selected),energy=-reference["reward"],optimal_ties=ties)
    else:
        raise ValueError(f"Unknown method {method!r}")
    raw_chosen = selected[:]
    raw_feasible = q.feasible(raw_chosen)
    if not raw_feasible:
        selected = greedy_reference(q, raw_chosen)
    reward = sum(q.candidates[i].reward for i in selected)
    return {"selected": [q.candidates[i].id for i in selected], "reward": reward,
            "feasible": q.feasible(selected), "method": method,
            "proven_optimal_within_pool": method in ("exact","exact_random_tie"), "qubo": q.summary(),
            "raw": {**raw, "selected": [q.candidates[i].id for i in raw_chosen],
                    "feasible": raw_feasible},
            "repaired": selected != raw_chosen, "reference": reference,
            "elapsed_seconds": time.perf_counter()-started}


def audit() -> dict[str, Any]:
    """Small reproducible exhaustive proof checks and a held-fixed solver smoke benchmark."""
    from itertools import product
    from statistics import mean, median
    rng = random.Random(713)
    examined = 0
    for trial in range(100):
        n, capacity = rng.randint(0, 6), rng.randint(0, 7)
        candidates = [dict(id=str(i), reward=rng.randint(-2, 9),
            resources={"power": rng.randint(0, 3), "worker": rng.randint(0, 1)}) for i in range(n)]
        conflicts = [(str(i), str(j)) for i in range(n) for j in range(i+1, n) if rng.random() < .2]
        q = build_qubo(candidates, conflicts, {"power": capacity, "worker": 1})
        reference = exact_reference(q)
        ground, valid_ground = math.inf, True
        for bits in product((0, 1), repeat=q.size):
            examined += 1
            energy = q.energy(bits)
            feasible = q.feasible(i for i in range(n) if bits[i])
            if energy < ground:
                ground, valid_ground = energy, feasible
            elif energy == ground:
                valid_ground &= feasible
        if abs(ground + reference["reward"]) > 1e-8 or not valid_ground:
            raise AssertionError(f"QUBO/reference mismatch in random tiny case {trial}")
        for mask in range(1 << n):
            chosen = [i for i in range(n) if mask >> i & 1]
            if q.feasible(chosen):
                reward = sum(q.candidates[i].reward for i in chosen)
                if abs(q.energy(q.encode(chosen)) + reward) > 1e-8:
                    raise AssertionError("Feasible selection lacks zero-penalty encoding")
    rows = []
    for seed in range(30):
        rng = random.Random(seed)
        candidates = [dict(id=str(i), reward=rng.randrange(1, 21),
            resources={"power": rng.randrange(1, 7)}) for i in range(12)]
        conflicts = [(str(i), str(j)) for i in range(12) for j in range(i+1, 12) if rng.random() < .25]
        exact = select(candidates, conflicts, {"power": 15}, method="exact")
        greedy = select(candidates, conflicts, {"power": 15}, method="greedy")
        sa = select(candidates, conflicts, {"power": 15}, method="sa", seed=seed, sweeps=150, restarts=4)
        if sa["reward"] < greedy["reward"]-1e-8 or abs(sa["raw"]["energy"]+sa["reward"]) > 1e-7:
            raise AssertionError("SA warm-start or incremental energy regression")
        rows.append((greedy["reward"]/exact["reward"], sa["reward"]/exact["reward"],
                     sa["repaired"], sa["elapsed_seconds"]))
    return {"schema": "stage2-qubo-audit.v1", "tiny_random_qubos": 100,
            "complete_bitstrings_examined": examined,
            "ground_energy_matches_independent_selection_reference": True,
            "every_ground_state_feasible": True,
            "every_feasible_core_set_has_zero_penalty_extension": True,
            "benchmark": {"instances": 30, "candidates_each": 12,
                "instance_generation_seeds": [0, 29],
                "purpose": "solver_smoke_test_not_factory_evidence",
                "greedy_mean_reward_ratio_to_pool_optimum": mean(r[0] for r in rows),
                "sa_mean_reward_ratio_to_pool_optimum": mean(r[1] for r in rows),
                "greedy_exact_hits": sum(r[0] == 1 for r in rows),
                "sa_exact_hits": sum(r[1] == 1 for r in rows),
                "repairs": sum(r[2] for r in rows),
                "sa_median_seconds": median(r[3] for r in rows)}}


if __name__ == "__main__":
    import argparse
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", action="store_true", help="Run reproducible exhaustive correctness checks")
    args = parser.parse_args()
    if not args.audit:
        parser.error("Use --audit, or import select/build_qubo from Python")
    print(json.dumps(audit(), indent=2))
