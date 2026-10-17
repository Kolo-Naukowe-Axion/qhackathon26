"""Independent feasible-selection audit and optional all-bitstring energy audit."""
import itertools
import time
import numpy as np
from .check import check_plan
from .domain import make_plan, residual_demand
from .native import bits_for_selection
from .decode import decode
from .qubo import energy, objective_energy, ising, validate_bundle
from .methods.classical import energy_chunks


def audit_bundle(bundle):
    start = time.monotonic()
    validate_bundle(bundle)
    instance, state, programs = bundle["instance"], bundle["snapshot"], bundle["options"]
    remaining = residual_demand(state)
    # Every generated new batch serves >=1 lot. Demand bounds therefore bound
    # the number of selected programs in ANY physically feasible selection.
    max_selected = sum(remaining.values())
    if max_selected > 4:
        raise ValueError("Independent selection audit limited to at most four residual lots")
    checked, feasible, best, best_bits = 0, 0, None, None
    valid_masks = []
    for count in range(min(max_selected, len(programs)) + 1):
        for selected in itertools.combinations(range(len(programs)), count):
            checked += 1
            plan = make_plan(instance, state["fixed_batches"] + [programs[i] for i in selected])
            physical = check_plan(instance, state, plan)
            if not physical["valid"]:
                continue
            bits = bits_for_selection(bundle, selected)
            decoded = decode(bundle, bits)
            if not decoded["valid"]:
                raise AssertionError("Raw feasible selection disagrees with literal QUBO")
            e = energy(bundle, bits)
            feasible += 1
            if best is None or e < best:
                best, best_bits = e, bits
            # Enumerate every register code, including bounded-register degeneracy.
            domains = []
            for register in bundle["registers"]:
                needed = sum(bits[i]*w for i, w in zip(register["indices"], register["weights"]))
                domains.append([code for code in itertools.product((0, 1), repeat=len(register["indices"]))
                                if sum(a*b for a, b in zip(code, register["weights"])) == needed])
            for codes in itertools.product(*domains):
                encoded = bits.copy()
                for register, code in zip(bundle["registers"], codes):
                    for i, value in zip(register["indices"], code):
                        encoded[i] = value
                valid_masks.append(sum(value << i for i, value in enumerate(encoded)))
    if best is None:
        raise AssertionError("No feasible raw continuation found")
    n = bundle["size"]["binary_variables"]
    raw_enumeration = dict(raw_selections_checked=checked, feasible_selections=feasible,
                           exact_best_energy=str(best), best_bits=best_bits,
                           completeness_reason="Every offered program covers >=1 residual lot; all subsets up to residual lots checked")
    bitstring_count, zero_count = 0, 0
    if n <= 22:
        valid_masks_array = np.array(sorted(set(valid_masks)), dtype=np.uint64)
        linear = np.array(list(map(int, bundle["objective"]["linear"])), dtype=np.int64)
        observed_min = None
        for masks, bits, values in energy_chunks(bundle):
            objective = bits @ linear + int(bundle["objective"]["constant"])
            expected = np.isin(masks, valid_masks_array)
            if not np.array_equal(values == objective, expected):
                raise AssertionError("Zero-penalty set differs from independently feasible selections")
            if np.any(values < objective):
                raise AssertionError("Negative literal penalty")
            bitstring_count += len(masks)
            zero_count += int(expected.sum())
            local = int(values.min())
            observed_min = local if observed_min is None else min(observed_min, local)
        if observed_min != best:
            raise AssertionError("All-bitstring ground energy differs from independent optimum")
    z_model = ising(bundle)
    rng = np.random.default_rng(7)
    probe = [best_bits] + [rng.integers(0, 2, n).tolist() for _ in range(32)]
    for bits in probe:
        z = [1 - 2*x for x in bits]
        ze = (int(z_model["constant"]) + sum(int(c)*s for c, s in zip(z_model["linear"], z))
              + sum(int(t["value"])*z[t["i"]]*z[t["j"]] for t in z_model["quadratic"]))
        if ze != 4*energy(bundle, bits):
            raise AssertionError("Binary/Pauli-Z conversion mismatch")
    return dict(schema_version="catering-audit.v1", bundle_sha256=bundle["bundle_sha256"],
                raw_enumeration=raw_enumeration, all_bitstrings_checked=bitstring_count,
                zero_penalty_bitstrings=zero_count if bitstring_count else None,
                all_bitstrings_status="exhaustive" if bitstring_count else "not_enumerated",
                ising_probes=len(probe), valid=True, total_s=time.monotonic()-start,
                physical_qpu_calls=0, veloxq_calls=0)
