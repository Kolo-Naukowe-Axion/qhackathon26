"""Offline VeloxQ packet preparation; remote work requires --submit/--resume.

No token is needed to exercise the actual SDK's local HDF5 writer/parser.
"""

import argparse
import json
import math
import os
import importlib.metadata
from pathlib import Path
import time

import dimod
import h5py
from veloxq_sdk import VeloxQSolver
from veloxq_sdk.api.backends import BaseBackend
from veloxq_sdk.api.jobs import Job, VeloxSampleSet
from veloxq_sdk.api.problems import File
from veloxq_sdk.api.solvers import VeloxQParameters

from .artifacts import digest, save_run, write_json
from .stage1 import ROOT, build_qubo, energy, to_dimod


def write_packet(model, path):
    """Use the installed SDK's real serialization path without uploading."""
    spin = to_dimod(model).spin
    # Private writer is version-pinned and covered by round-trip energy tests.
    File._write_ising_hdf5(path, spin.linear, spin.quadratic, offset=spin.offset)


def extract_samples(samples, model):
    """Respect vartype AND serialized labels, never infer a bit/spin convention."""
    n = len(model["variables"])
    columns = {}
    for label in samples.variables:
        text = str(label)
        if not text.isdecimal() or str(int(text)) != text or int(text) in columns:
            raise ValueError("Unexpected or duplicate solver variable label")
        columns[int(text)] = label
    if set(columns) != set(range(n)):
        raise ValueError("Solver variables do not match the submitted model")
    if samples.vartype not in (dimod.SPIN, dimod.BINARY):
        raise ValueError("Unsupported solver vartype")
    records, deltas = [], []
    for row in samples.data(sorted_by=None):
        raw_values = [row.sample[columns[i]] for i in range(n)]
        if any(x != int(x) for x in raw_values):
            raise ValueError("Nonintegral returned state")
        values = [int(x) for x in raw_values]
        if samples.vartype == dimod.SPIN:
            if any(x not in (-1, 1) for x in values):
                raise ValueError("Invalid spin value")
            bits = [(x + 1) // 2 for x in values]
        else:
            if any(x not in (0, 1) for x in values):
                raise ValueError("Invalid binary value")
            bits = values
        returned_energy = float(row.energy)
        if not math.isfinite(returned_energy):
            raise ValueError("Nonfinite returned energy")
        deltas.append(returned_energy - energy(model, bits))
        records.append(dict(bits=bits, count=int(row.num_occurrences), reported_energy=returned_energy))
    if not records:
        raise ValueError("Solver returned no samples")
    # Some engines omit the Ising constant. Permit only that known convention,
    # consistently across all rows; reject varying discrepancies or sign errors.
    delta = deltas[0]
    allowed = (0.0, -float(to_dimod(model).spin.offset))
    if not any(math.isclose(delta, d, abs_tol=1e-6, rel_tol=0) for d in allowed) or any(
        not math.isclose(d, delta, abs_tol=1e-6, rel_tol=0) for d in deltas
    ):
        raise ValueError("Returned energies disagree with submitted model and label mapping")
    return records, dict(returned_vartype=samples.vartype.name, reported_minus_recomputed_energy=delta,
                         energy_convention="full model" if abs(delta) < 1e-6 else "Ising constant omitted by result")


def wait_for_job(job, timeout, poll_interval=2):
    """Bound our polling loop rather than relying on the SDK's blocking WebSocket."""
    deadline = time.monotonic() + timeout
    while True:
        job.refresh()
        status = getattr(job.status, "value", job.status)
        if status == "completed":
            return
        if status in ("failed", "canceled"):
            raise RuntimeError(f"VeloxQ job ended with status {status}")
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("Local wait expired; job may still run. Resume using the saved job id.")
        time.sleep(min(poll_interval, remaining))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--submit", action="store_true", help="Upload and submit ONE remote job")
    mode.add_argument("--resume", action="store_true", help="Retrieve the saved job without resubmitting")
    parser.add_argument("--output", type=Path, default=ROOT / "output/stage1/velox-3x3")
    parser.add_argument("--encoding", choices=("onehot", "domain-wall"), default="onehot")
    parser.add_argument("--horizon", type=int, default=8)
    parser.add_argument("--num-rep", type=int, default=512)
    parser.add_argument("--num-steps", type=int, default=2000)
    parser.add_argument("--backend-id", help="Override only with an actual organizer-supplied backend id")
    parser.add_argument("--timeout", type=float, default=300)
    args = parser.parse_args()
    if not math.isfinite(args.timeout) or min(args.num_rep, args.num_steps, args.timeout) <= 0:
        parser.error("Positive budgets required")
    if (args.output / "run.json").exists():
        parser.error("Completed evidence already exists; choose another output directory")
    if not args.resume and (args.output / "submission.json").exists():
        parser.error("A job was already submitted here; use --resume")
    if args.submit and (args.output / "submission-intent.json").exists():
        parser.error("Prior submission intent exists. Check the platform for a job before any resubmit")
    instance = json.loads((ROOT / "instances/instance_3x3.json").read_text())
    model = build_qubo(instance, args.horizon, args.encoding)
    parameters = VeloxQParameters(num_rep=args.num_rep, num_steps=args.num_steps)
    kwargs = dict(parameters=parameters)
    if args.backend_id:
        kwargs["backend"] = BaseBackend(id=args.backend_id)
    solver = VeloxQSolver(**kwargs)  # Local pydantic object, no service calls.
    plan = dict(mode="offline packet; no remote job", model_sha256=digest(model), instance_sha256=digest(instance),
                encoding=args.encoding, horizon=args.horizon, variables=len(model["variables"]),
                solver_id=solver.id, backend_id=solver.backend.id,
                parameters=solver.parameters.model_dump(mode="json"),
                sdk_version=importlib.metadata.version("veloxq-sdk"), backend_access_verified=False)
    args.output.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    if args.resume:
        submission = json.loads((args.output / "submission.json").read_text())
        if submission["model_sha256"] != digest(model) or submission["instance_sha256"] != digest(instance):
            parser.error("Resume instance/model differs from the saved submission")
        if not os.environ.get("VELOX_TOKEN"):
            parser.error("VELOX_TOKEN is required for remote access")
        job = Job.from_id(submission["job_id"])
    else:
        write_json(args.output / "model.json", model)
        write_json(args.output / "plan.json", plan)
        write_packet(model, args.output / "ising-input.h5")
        if not args.submit:
            print(json.dumps(plan, indent=2))
            return
        if not os.environ.get("VELOX_TOKEN"):
            parser.error("Packet prepared. Set VELOX_TOKEN before --submit")
        # Persist intent before mutations; ambiguous transport failure is never
        # automatically retried. Check the platform before any manual resubmit.
        write_json(args.output / "submission-intent.json", plan)
        file = File.from_instance(to_dimod(model), name=f"qfactoria-3x3-{args.encoding}-H{args.horizon}")
        job = solver.submit(file)
        submission = dict(plan, mode="remote submission", job_id=job.id, file_id=file.id,
                          upload_and_submit_wall_seconds=time.perf_counter() - started)
        write_json(args.output / "submission.json", submission)
    try:
        wait_for_job(job, args.timeout)
        job.save_result(args.output / "raw-result.h5")
        with h5py.File(args.output / "raw-result.h5", "r") as result_file:
            samples = VeloxSampleSet.from_result(result_file)
        records, convention = extract_samples(samples, model)
        write_json(args.output / "returned-samples.json", records)
        metadata = dict(submission, **convention, job_statistics=job.statistics.model_dump(mode="json"),
                        retrieval_wall_seconds=time.perf_counter() - started,
                        timing_scope="this invocation; resumed runs exclude prior waiting time")
        official, report = save_run(args.output, "instance_3x3", instance, model, records,
                                    "VeloxQ (remote QUBO solver)", metadata)
        print(json.dumps(dict(job_id=job.id, makespan=official["makespan"], feasible_rate=report["feasible_rate"]), indent=2))
    except Exception as exc:
        # Exceptions can contain URLs/headers; retain the job id, not secret text.
        write_json(args.output / "retrieval-error.json", dict(error_type=type(exc).__name__, job_id=job.id,
                                                             hint="Use --resume with the same model options; no resubmit needed"))
        raise RuntimeError(f"{type(exc).__name__}: inspect local evidence; job {job.id} was retained") from None


if __name__ == "__main__":
    main()
