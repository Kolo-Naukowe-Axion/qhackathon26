"""Shared, fail-closed acceptance and evidence for real solver samples."""

from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path

from .stage1 import checked_bits, decode, energy, validate


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def write_json(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def versions():
    return {name: importlib.metadata.version(name) for name in
            ("numpy", "scipy", "qiskit", "qiskit-aer", "dimod", "dwave-samplers", "veloxq-sdk")}


def assess_samples(instance, model, records):
    """Recompute every energy and check every schedule; never repair a sample."""
    assessed = []
    for record in records:
        bits = checked_bits(model, record["bits"])
        count = record.get("count", 1)
        if type(count) is not int or count < 1:
            raise ValueError("Sample counts must be positive integers")
        recomputed = energy(model, bits)
        try:
            schedule = decode(model, bits)
            makespan = max((s["end"] for s in schedule), default=0)
            errors = validate(instance, schedule, makespan)
            if makespan > model["horizon"]:
                errors.append("outside horizon")
        except ValueError as exc:
            schedule, makespan, errors = [], None, [str(exc)]
        if recomputed != 0:
            errors.append("nonzero QUBO energy")
        assessed.append(dict(bits=bits, count=count, energy=recomputed,
                             feasible=not errors, makespan=makespan, errors=errors))
    return assessed


def save_run(directory, instance_name, instance, model, records, method, metadata):
    """Only a genuinely feasible returned sample produces a schedule/replay."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    # Refuse overwrite: a failed rerun must not leave an old accepted schedule.
    if (directory / "run.json").exists():
        raise FileExistsError(f"Run evidence already exists: {directory}")
    assessed = assess_samples(instance, model, records)
    feasible = [r for r in assessed if r["feasible"]]
    total = sum(r["count"] for r in assessed)
    report = dict(schema="stage1-run.v1", method=method, instance=instance_name,
                  timestamp=datetime.now(timezone.utc).isoformat(),
                  instance_sha256=digest(instance), model_sha256=digest(model),
                  encoding=model["encoding"], variables=len(model["variables"]),
                  horizon=model["horizon"], total_samples=total,
                  feasible_samples=sum(r["count"] for r in feasible),
                  feasible_rate=sum(r["count"] for r in feasible) / total if total else 0,
                  accepted=bool(feasible), metadata=metadata, versions=versions())
    write_json(directory / "model.json", model)
    write_json(directory / "samples.json", assessed)
    write_json(directory / "run.json", report)
    if not feasible:
        raise RuntimeError(f"No feasible returned sample; diagnostics retained in {directory}")
    selected = min(feasible, key=lambda r: (r["makespan"], -r["count"], r["bits"]))
    schedule = decode(model, selected["bits"])
    official = dict(instance=instance_name, method=method, makespan=selected["makespan"], schedule=schedule)
    write_json(directory / "schedule.json", official)
    replay = dict(schema="axion-replay.v1", unit="hours", provenance=dict(
        kind="solver", method=method, label=f"Verified {instance_name} solver run",
        description=f"Actual returned sample; evidence model SHA256 {digest(model)}",
        source=str(directory), jobId=metadata.get("job_id"), timestamp=report["timestamp"]),
        machines=[dict(id=op["machine"], name=op["machine"]) for op in instance["jobs"][0]["operations"]],
        jobs=[dict(job, color=["#648da3", "#ba8560", "#95a66b"][i % 3]) for i, job in enumerate(instance["jobs"])],
        schedule=schedule, declaredMakespan=official["makespan"])
    write_json(directory / "replay.json", replay)
    return official, report
