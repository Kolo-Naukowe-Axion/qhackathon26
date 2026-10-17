"""VeloxQ adapter for frozen catering QUBO bundles (solver contract v1, sections 4-6).

Offline by default: serialization, spin conversion and response parsing need no
token. A remote job is submitted only when the budget sets
allow_external_execution, VELOX_TOKEN is present and the local job ledger is
below max_service_jobs. Remote calls are never retried automatically.

Spin convention used here (NOT the Pauli-Z convention of contract section 5):
    s = 2x - 1,  x = (1 + s)/2,  values in {-1, +1}.
With integer QUBO coefficients (constant c, linear a_i, pair b_ij) the
transformed Ising model is multiplied by SPIN_SCALE = 4 so it stays integral:
    h_i    = 2*a_i + sum_j b_ij          (over pairs touching i)
    J_ij   = b_ij
    offset = 4*c + 2*sum_i a_i + sum_ij b_ij
    E_spin(s) = offset + sum_i h_i*s_i + sum_ij J_ij*s_i*s_j = 4*E_qubo(x).
Returned energies are divided by SPIN_SCALE before comparison or reporting.

Results follow the foundation's catering-method-result.v1 (catering/contracts.py)
so `python -m catering.run evaluate` accepts result.json directly; VeloxQ-specific
fields (bundle identity, budget, representation, failure) are kept alongside.
"""

import argparse
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import time

SCHEMA_VERSION = "catering-method-result.v1"
METHOD_ID = "veloxq"
METHOD_VERSION = "0.3.0"
SPIN_SCALE = 4
# Coefficients are serialized as float64 by the SDK; above this they are inexact.
FLOAT_EXACT_LIMIT = 2**53
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LEDGER = ROOT / "output/catering-methods/veloxq/job_ledger.json"
IDENTITY_FIELDS = ("schema_version", "bundle_id", "bundle_sha256", "case_id", "profile_id", "scenario_id",
                   "instance_sha256", "snapshot_sha256", "representation_id")

# Contract section 5 standalone smoke example; not a catering result.
SMOKE_BUNDLE = {
    "bundle_id": "contract-smoke-v1",
    "case_id": "smoke",
    "representation_id": "contract-section5-example",
    "qubo": {
        "constant": "0",
        "linear": ["-4", "-3"],
        "quadratic": [{"i": 0, "j": 1, "value": "6"}],
        "variable_order": ["A", "B"],
        "registers": [],
    },
}


def canonical_sha256(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def file_sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    tmp.replace(path)


def _parse_int(text, where):
    # Decimal integer strings only: no floats, exponents, NaN or whitespace tricks.
    if not isinstance(text, str):
        raise ValueError(f"{where}: coefficient must be a decimal integer string")
    body = text[1:] if text[:1] == "-" else text
    if not body.isdigit() or not body.isascii() or (len(body) > 1 and body[0] == "0"):
        raise ValueError(f"{where}: not a canonical decimal integer: {text!r}")
    return int(text)


def load_qubo(bundle):
    """Validate and parse contract section 4 coefficients into Python ints.

    Coefficients are read from bundle["qubo"] when present, otherwise from the
    bundle's top level. The foundation fixes the final on-disk layout.
    """
    raw = bundle.get("qubo", bundle)
    order = raw.get("variable_order")
    if not isinstance(order, list) or not order:
        raise ValueError("variable_order must be a non-empty list")
    if len(set(order)) != len(order) or not all(isinstance(v, str) and v for v in order):
        raise ValueError("variable_order must contain unique non-empty strings")
    n = len(order)
    linear = raw.get("linear")
    if not isinstance(linear, list) or len(linear) != n:
        raise ValueError("linear must be a list of length n")
    linear = [_parse_int(v, f"linear[{i}]") for i, v in enumerate(linear)]
    quadratic = {}
    for k, term in enumerate(raw.get("quadratic", [])):
        i, j = term.get("i"), term.get("j")
        if type(i) is not int or type(j) is not int or not 0 <= i < j < n:
            raise ValueError(f"quadratic[{k}]: indices must satisfy 0 <= i < j < n")
        if (i, j) in quadratic:
            raise ValueError(f"quadratic[{k}]: duplicate pair ({i}, {j})")
        value = _parse_int(term.get("value"), f"quadratic[{k}]")
        if value:
            quadratic[(i, j)] = value
    return {"n": n, "constant": _parse_int(raw.get("constant"), "constant"), "linear": linear,
            "quadratic": quadratic, "variable_order": list(order), "registers": raw.get("registers", [])}


def qubo_energy(q, bits):
    if len(bits) != q["n"] or any(b not in (0, 1) for b in bits):
        raise ValueError("bits must be a 0/1 vector of length n")
    total = q["constant"] + sum(a for a, b in zip(q["linear"], bits) if b)
    return total + sum(v for (i, j), v in q["quadratic"].items() if bits[i] and bits[j])


def qubo_to_spin(q):
    """Exact integer Ising model with E_spin = SPIN_SCALE * E_qubo (see module docstring)."""
    h = [2 * a for a in q["linear"]]
    for (i, j), b in q["quadratic"].items():
        h[i] += b
        h[j] += b
    offset = 4 * q["constant"] + 2 * sum(q["linear"]) + sum(q["quadratic"].values())
    J = dict(q["quadratic"])
    return {"h": h, "J": J, "offset": offset, "scale": SPIN_SCALE}


def spin_energy(model, spins):
    total = model["offset"] + sum(h * s for h, s in zip(model["h"], spins))
    return total + sum(v * spins[i] * spins[j] for (i, j), v in model["J"].items())


def spin_l1(model):
    """Sum of |offset|, |h| and |J|: bounds |E_spin| and scales float rounding error."""
    return abs(model["offset"]) + sum(abs(v) for v in model["h"]) + sum(abs(v) for v in model["J"].values())


def coefficient_report(q, model):
    import numpy as np

    values = [abs(v) for v in q["linear"]] + [abs(v) for v in q["quadratic"].values()]
    spin_values = [abs(v) for v in model["h"]] + [abs(v) for v in model["J"].values()] + [abs(model["offset"])]
    spin_terms = [v for v in model["h"] + list(model["J"].values()) if v]
    nonzero = [v for v in values if v]
    # VeloxQ returns float32 energies; a GPU backend may also round coefficients to float32.
    f32_inexact = sum(int(np.float32(v)) != v for v in spin_terms)
    return {"n": q["n"], "couplers": len(q["quadratic"]),
            "qubo_max_abs": max(values, default=0), "qubo_min_nonzero_abs": min(nonzero, default=0),
            "spin_max_abs_including_offset": max(spin_values, default=0),
            "spin_dynamic_range": max(map(abs, spin_terms), default=0) / max(1, min(map(abs, spin_terms), default=1)),
            "spin_l1": spin_l1(model),
            "float64_exact": max(spin_values, default=0) < FLOAT_EXACT_LIMIT,
            "float32_inexact_spin_coefficients": f32_inexact, "spin_coefficients": len(spin_terms)}


def write_packet(model, path, *, initial_bits=None, num_rep=1):
    """Serialize through the installed SDK's own HDF5 writer (no upload)."""
    from veloxq_sdk.api.problems import File

    if max([abs(v) for v in model["h"]] + [abs(v) for v in model["J"].values()] + [abs(model["offset"])]) >= FLOAT_EXACT_LIMIT:
        raise ValueError("Spin coefficients exceed float64 exact-integer range; refuse lossy serialization")
    # Python ints make the SDK store an exact integer dtype. Floats are stored as float32,
    # which rounds coefficients above 2^24 (all v3 scale bundles) before upload.
    initial_state = None
    if initial_bits is not None:
        import dimod
        import numpy as np
        if len(initial_bits) != len(model["h"]) or any(type(b) is not int or b not in (0,1) for b in initial_bits):
            raise ValueError("Initializer must be binary in the submitted variable order")
        if type(num_rep) is not int or num_rep < 1:
            raise ValueError("Initializer repetitions must be positive")
        spins = [2*b-1 for b in initial_bits]
        samples = np.tile(np.asarray(spins, dtype=np.int8), (num_rep,1))
        initial_state = dimod.SampleSet.from_samples((samples,list(range(len(spins)))),
            vartype=dimod.SPIN, energy=[spin_energy(model,spins)]*num_rep)
    h = {i: int(v) for i, v in enumerate(model["h"])}
    J = {key: int(v) for key, v in model["J"].items()}
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w+b") as handle:
        # Private writer, pinned via veloxq-sdk==1.0.0 and covered by round-trip tests.
        File._write_ising_hdf5(handle, h, J, offset=float(model["offset"]), init_state=initial_state)
    return path


def read_packet(path):
    """Read back the Ising packet written by write_packet (for round-trip checks)."""
    import h5py

    with h5py.File(path, "r") as hdf:
        group = hdf["Ising"]
        labels = [int(x) for x in group["labels"].asstr()[()]]
        biases = group["biases"][()]
        h = {label: float(b) for label, b in zip(labels, biases)}
        entries = {}
        couplings = group["couplings"]
        if group.attrs["sparsity"] == "sparse":
            triples = zip(couplings["I"][()], couplings["J"][()], couplings["V"][()])
            for r, c, v in triples:  # stored 1-based
                entries[(int(r) - 1, int(c) - 1)] = float(v)
        else:
            dense = couplings[()]
            for r, c in zip(*dense.nonzero()):
                entries[(int(r), int(c))] = float(dense[r, c])
        # The SDK stores each coupling J_ij in BOTH triangles with its full value.
        J = {}
        for (r, c), v in entries.items():
            if r == c or entries.get((c, r)) != v:
                raise ValueError("Packet couplings are not a zero-diagonal symmetric matrix")
            if r < c:
                a, b = labels[r], labels[c]
                J[(min(a, b), max(a, b))] = v
        return {"h": h, "J": J, "offset": float(group.attrs["offset"]), "var_type": group.attrs["var_type"],
                "dtype": str(biases.dtype)}


def parse_samples(sampleset, q, model):
    """Map returned rows to contract samples and verify the energy convention.

    Labels must be exactly the decimal indices 0..n-1 we submitted. Each reported
    energy must equal the recomputed spin energy either with the offset (full
    model) or without it, consistently across all rows. Anything else rejects.
    """
    import dimod
    import numpy as np

    n = q["n"]
    columns = {}
    for label in sampleset.variables:
        text = str(label)
        if not text.isdecimal() or str(int(text)) != text or int(text) in columns:
            raise ValueError("Unexpected or duplicate solver variable label")
        columns[int(text)] = label
    if set(columns) != set(range(n)):
        raise ValueError("Solver variables do not match the submitted model")
    if sampleset.vartype not in (dimod.SPIN, dimod.BINARY):
        raise ValueError("Unsupported solver vartype")
    # Returned energies only confirm mapping and convention; literal energies are recomputed exactly.
    # Tolerance follows the returned dtype (VeloxQ: float32), scaled by the L1 bound on |E_spin|.
    dtype = np.asarray(sampleset.record.energy).dtype
    eps = float(np.finfo(dtype).eps) if np.issubdtype(dtype, np.floating) else 0.0
    tolerance = max(16 * eps * spin_l1(model), 1e-9 * max(1, n))
    records, deltas = [], []
    for row in sampleset.data(sorted_by=None):
        raw_values = [row.sample[columns[i]] for i in range(n)]
        if any(x != int(x) for x in raw_values):
            raise ValueError("Nonintegral returned state")
        values = [int(x) for x in raw_values]
        if sampleset.vartype == dimod.SPIN:
            if any(x not in (-1, 1) for x in values):
                raise ValueError("Invalid spin value")
            bits = [(x + 1) // 2 for x in values]
        else:
            if any(x not in (0, 1) for x in values):
                raise ValueError("Invalid binary value")
            bits = values
        reported = float(row.energy)
        if not math.isfinite(reported):
            raise ValueError("Nonfinite returned energy")
        recomputed = qubo_energy(q, bits)
        deltas.append(reported - SPIN_SCALE * recomputed)
        records.append({"bits": bits, "count": int(row.num_occurrences),
                        "reported_energy_spin_scaled": reported, "reported_energy": str(recomputed)})
    if not records:
        raise ValueError("Solver returned no samples")
    allowed = {"full model": 0.0, "Ising offset omitted by result": -float(model["offset"])}
    matches = [name for name, expected in allowed.items()
               if all(math.isclose(d, expected, abs_tol=tolerance, rel_tol=0) for d in deltas)]
    if not matches:
        raise ValueError("Returned energies disagree with submitted model and label mapping")
    if len(matches) > 1:
        raise ValueError("Energy convention ambiguous: offset is within the returned-energy tolerance")
    convention = matches[0]
    deviation = max(abs(d - allowed[convention]) for d in deltas)
    # Contract samples are aggregated by bit vector; multiplicities add up.
    merged = {}
    for record in records:
        key = tuple(record["bits"])
        if key in merged:
            merged[key]["count"] += record["count"]
        else:
            merged[key] = record
    samples = sorted(merged.values(), key=lambda r: (int(r["reported_energy"]), r["bits"]))
    return samples, {"returned_vartype": sampleset.vartype.name, "energy_convention": convention,
                     "spin_scale": SPIN_SCALE, "reported_minus_scaled_energy": deltas[0],
                     "returned_energy_dtype": str(dtype),
                     "convention_tolerance": tolerance, "max_convention_deviation": deviation}


def _ledger(path):
    if path.exists():
        return json.loads(path.read_text())
    return {"jobs": []}


def _environment():
    env = {"python": platform.python_version(), "platform": platform.platform()}
    for package in ("veloxq-sdk", "dimod", "h5py", "numpy"):
        try:
            env[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            env[package] = None
    return env


def _bundle_identity(bundle, q):
    identity = {k: bundle[k] for k in IDENTITY_FIELDS if k in bundle}
    identity["qubo_sha256"] = canonical_sha256(bundle.get("qubo", {k: bundle.get(k) for k in
                                                                  ("constant", "linear", "quadratic", "variable_order")}))
    identity["variable_order_sha256"] = canonical_sha256(q["variable_order"])
    return identity


def _wait_for_job(job, timeout, poll_interval=2.0):
    """Bounded polling instead of the SDK's unbounded blocking wait."""
    deadline = time.monotonic() + timeout
    while True:
        job.refresh()
        status = getattr(job.status, "value", job.status)
        if status == "completed":
            return status
        if status in ("failed", "canceled"):
            raise RuntimeError(f"VeloxQ job ended with status {status}")
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("Local wait expired; job may still run. Resume using the saved job id.")
        time.sleep(min(poll_interval, remaining))


def solve_qubo(bundle, budget, method_config, output_dir, *, solver_factory=None):
    """Contract adapter: returns a MethodResult dict and writes it to output_dir/result.json."""
    started = time.perf_counter()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    budget = dict(budget or {})
    method_config = dict(method_config or {})
    timings = {}

    t = time.perf_counter()
    q = load_qubo(bundle)
    model = qubo_to_spin(q)
    timings["build_s"] = time.perf_counter() - t
    report = coefficient_report(q, model)

    parameters = {"num_rep": int(method_config.get("num_rep", 512)),
                  "num_steps": int(method_config.get("num_steps", 2000))}
    if any(v < 1 for v in parameters.values()):
        raise ValueError("Positive solver steps/repetitions required")
    initial_bits = method_config.get("initial_bits")
    if initial_bits is not None and bundle.get("encoding") == "paired-course-anchor-onehot.v1":
        from catering.decode import decode
        if not decode(bundle,initial_bits)["valid"]:
            raise ValueError("Catering warm start must be independently feasible")
    wall_limit = float(budget.get("wall_time_limit_s", 300))
    max_jobs = int(budget.get("max_service_jobs", 0))
    ledger_path = Path(method_config.get("ledger_path", DEFAULT_LEDGER))
    result = {
        "schema_version": SCHEMA_VERSION, "method_id": METHOD_ID, "method_version": METHOD_VERSION,
        "case_id": bundle.get("case_id"), "bundle_sha256": bundle.get("bundle_sha256"),
        "representation_id": bundle.get("representation_id"),
        "bundle": _bundle_identity(bundle, q), "execution_kind": "veloxq_service", "status": "not_run",
        "samples": [], "representation": report,
        "configuration": {"solver": "VeloxQSolver", "parameters": parameters,
                          "backend_id": method_config.get("backend_id"), "spin_convention": "s=2x-1",
                          "spin_scale": SPIN_SCALE, "initializer": "none (cold start)" if initial_bits is None else "explicit checked bits; repeated to num_rep",
                          "initial_bits_sha256": None if initial_bits is None else canonical_sha256(initial_bits),
                          "initial_literal_energy": None if initial_bits is None else str(qubo_energy(q,initial_bits)),
                          "initializer_service_acceptance": "unmeasured" if initial_bits is not None else "not applicable",
                          "seed_support": "not exposed by veloxq-sdk 1.0.0; not controlled",
                          "retries": "disabled", "repair": "disabled"},
        "budget": {**budget, "enforced": {"wall_time_limit_s": "local polling bound only",
                                          "max_service_jobs": f"local ledger {ledger_path.name}",
                                          "repeats": "one job per call", "shots": "num_rep is a backend setting"}},
        "timings": timings, "work": {"service_jobs_submitted": 0}, "environment": _environment(),
        "raw_artifacts": {}, "failure": None, "reference": None,
        "veloxq_calls": 0, "physical_qpu_calls": 0,
    }

    def finish(status, failure=None):
        result["status"] = status
        result["failure"] = failure
        timings["total_s"] = time.perf_counter() - started
        write_json(output_dir / "result.json", result)
        return result

    t = time.perf_counter()
    packet = write_packet(model, output_dir / "ising-input.h5", initial_bits=initial_bits, num_rep=parameters["num_rep"])
    timings["serialize_s"] = time.perf_counter() - t
    packet_hash = file_sha256(packet)
    result["raw_artifacts"]["ising_input"] = {"path": str(packet), "sha256": packet_hash}
    # Never upload a packet that differs from the exact model (e.g. silent float32 rounding).
    stored = read_packet(packet)
    result["configuration"]["packet_coefficient_dtype"] = stored["dtype"]
    if (stored["offset"] != model["offset"] or stored["h"] != {i: v for i, v in enumerate(model["h"])}
            or stored["J"] != model["J"]):
        return finish("failed", {"reason": "serialized packet is not exactly the submitted model",
                                 "packet_dtype": stored["dtype"]})

    if initial_bits is not None:
        import h5py
        import numpy as np
        with h5py.File(packet,"r") as handle:
            states=handle["Spectrum/states"][()]
            expected=np.asarray([2*b-1 for b in initial_bits],dtype=np.int8)
            if states.shape != (parameters["num_rep"],q["n"]) or not np.all(states==expected):
                return finish("failed", {"reason": "Serialized initializer changed bits or variable order"})
        result["configuration"]["initializer_packet_roundtrip"] = True

    if not budget.get("allow_external_execution", False):
        return finish("not_run", {"reason": "external execution not allowed by budget"})
    if not os.environ.get("VELOX_TOKEN"):
        return finish("unavailable", {"reason": "VELOX_TOKEN not set"})
    ledger = _ledger(ledger_path)
    if len(ledger["jobs"]) >= max_jobs:
        return finish("not_run", {"reason": f"service job cap reached ({len(ledger['jobs'])}/{max_jobs})",
                                  "ledger": str(ledger_path)})

    from veloxq_sdk import VeloxQSolver
    from veloxq_sdk.api.backends import BaseBackend
    from veloxq_sdk.api.problems import File
    from veloxq_sdk.api.solvers import VeloxQParameters

    kwargs = {"parameters": VeloxQParameters(**parameters)}
    if method_config.get("backend_id"):
        kwargs["backend"] = BaseBackend(id=method_config["backend_id"])
    solver = (solver_factory or VeloxQSolver)(**kwargs)
    result["configuration"]["solver_id"] = solver.id
    result["configuration"]["backend_id"] = solver.backend.id
    result["configuration"]["backend_name"] = type(solver.backend).__name__

    # Count the attempt before any mutation: an ambiguous failure still uses budget.
    entry = {"case_id": bundle.get("case_id"), "bundle_id": bundle.get("bundle_id"), "packet_sha256": packet_hash,
             "output_dir": str(output_dir), "submitted_unix": time.time(), "job_id": None}
    ledger["jobs"].append(entry)
    write_json(ledger_path, ledger)
    job = None
    try:
        t = time.perf_counter()
        file = File.from_path(packet, name=f"catering-{packet_hash[:16]}.h5")
        timings["upload_s"] = time.perf_counter() - t
        t = time.perf_counter()
        job = solver.submit(file)
        timings["submit_s"] = time.perf_counter() - t
        entry["job_id"] = job.id
        write_json(ledger_path, ledger)
        result["work"]["service_jobs_submitted"] = 1
        result["veloxq_calls"] = 1
        result["raw_artifacts"]["job_id"] = job.id
        result["raw_artifacts"]["file_id"] = file.id
        t = time.perf_counter()
        remaining = wall_limit - (time.perf_counter() - started)
        _wait_for_job(job, max(1.0, remaining))
        timings["backend_wait_s"] = time.perf_counter() - t
        t = time.perf_counter()
        raw_path = output_dir / "raw-result.h5"
        job.save_result(raw_path)
        timings["download_s"] = time.perf_counter() - t
        result["raw_artifacts"]["raw_result"] = {"path": str(raw_path), "sha256": file_sha256(raw_path)}
        t = time.perf_counter()
        import h5py
        from veloxq_sdk.api.jobs import VeloxSampleSet

        with h5py.File(raw_path, "r") as handle:
            sampleset = VeloxSampleSet.from_result(handle)
        samples, convention = parse_samples(sampleset, q, model)
        timings["parse_s"] = time.perf_counter() - t
        result["samples"] = samples
        if initial_bits is not None:
            result["configuration"]["initializer_service_acceptance"] = "job completed; backend use/effect not proven"
        result["configuration"]["returned"] = convention
        result["work"]["returned_rows"] = sum(s["count"] for s in samples)
        result["work"]["distinct_samples"] = len(samples)
        return finish("completed")
    except TimeoutError as exc:
        return finish("timeout", {"error_type": type(exc).__name__, "message": str(exc)})
    except Exception as exc:
        # Exception text can carry URLs or headers; keep only the type and our job id.
        return finish("failed", {"error_type": type(exc).__name__, "job_id": getattr(job, "id", None)})
    finally:
        if job is not None:
            try:
                job.refresh()
                result["backend_statistics"] = job.statistics.model_dump(mode="json")
                result["backend_timeline"] = [v.model_dump(mode="json") for v in job.timeline]
                write_json(output_dir / "result.json", result)
            except Exception as exc:  # statistics are best effort; never mask the main outcome
                result["backend_statistics_error"] = type(exc).__name__


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--smoke", action="store_true", help="Contract section 5 two-variable example")
    source.add_argument("--bundle", type=Path, help="Frozen bundle JSON from the foundation")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--allow-external", action="store_true", help="Permit ONE remote VeloxQ job")
    parser.add_argument("--max-service-jobs", type=int, default=0, help="Cap on total ledger jobs")
    parser.add_argument("--num-rep", type=int, default=512)
    parser.add_argument("--num-steps", type=int, default=2000)
    parser.add_argument("--timeout", type=float, default=300)
    parser.add_argument("--backend-id")
    args = parser.parse_args()
    bundle = SMOKE_BUNDLE if args.smoke else json.loads(args.bundle.read_text())
    label = str(bundle.get("bundle_id") or bundle.get("case_id") or "case").replace("/", "_")
    output = args.output or ROOT / "output/catering-methods/veloxq" / f"{label}-{time.strftime('%Y%m%dT%H%M%S')}"
    if (output / "result.json").exists():
        parser.error("Result already exists; choose a fresh output directory")
    budget = {"wall_time_limit_s": args.timeout, "allow_external_execution": args.allow_external,
              "max_service_jobs": args.max_service_jobs}
    config = {"num_rep": args.num_rep, "num_steps": args.num_steps, "backend_id": args.backend_id}
    result = solve_qubo(bundle, budget, config, output)
    best = result["samples"][0] if result["samples"] else None
    print(json.dumps({"status": result["status"], "output": str(output), "failure": result["failure"],
                      "best": best and {"bits": best["bits"], "energy": best["reported_energy"]},
                      "distinct_samples": len(result["samples"])}, indent=2))


if __name__ == "__main__":
    main()
