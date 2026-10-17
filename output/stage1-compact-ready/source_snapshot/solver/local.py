"""Solve the actual QUBO locally by simulated annealing, keeping real samples."""

import argparse
import json
from pathlib import Path
import time

from dwave.samplers import SimulatedAnnealingSampler

from .artifacts import save_run
from .stage1 import ROOT, build_qubo, to_dimod


def anneal(model, *, reads=512, sweeps=32000, seed=2026, beta_range=None, schedule="linear"):
    if min(reads, sweeps) < 1:
        raise ValueError("Positive annealing budgets required")
    started = time.perf_counter()
    samples = SimulatedAnnealingSampler().sample(to_dimod(model), num_reads=reads, num_sweeps=sweeps, seed=seed,
                                                beta_range=beta_range, beta_schedule_type=schedule)
    records = [dict(bits=[int(row.sample[i]) for i in range(len(model["variables"]))], count=int(row.num_occurrences))
               for row in samples.aggregate().data()]
    return records, dict(algorithm="dwave.samplers.SimulatedAnnealingSampler", reads=reads, sweeps=sweeps, seed=seed,
                         elapsed_wall_seconds=time.perf_counter() - started,
                         beta_range=[float(x) for x in samples.info["beta_range"]], beta_schedule_type=schedule,
                         reference_warm_start=False, timing_scope="local BQM construction, sampling and extraction")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--encoding", choices=("onehot", "domain-wall"), default="onehot")
    parser.add_argument("--horizon", type=int, default=8)
    parser.add_argument("--output", type=Path, default=ROOT / "output/stage1/anneal-3x3")
    parser.add_argument("--reads", type=int, default=512)
    parser.add_argument("--sweeps", type=int, default=32000)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--beta-range", type=float, nargs=2, metavar=("START", "END"))
    parser.add_argument("--schedule", choices=("geometric", "linear"), default="linear")
    args = parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        parser.error("Use an empty output directory to preserve previous evidence")
    instance = json.loads((ROOT / "instances/instance_3x3.json").read_text())
    model = build_qubo(instance, args.horizon, args.encoding)
    records, metadata = anneal(model, reads=args.reads, sweeps=args.sweeps, seed=args.seed,
                              beta_range=args.beta_range, schedule=args.schedule)
    official, report = save_run(args.output, "instance_3x3", instance, model, records,
                                "Classical QUBO simulated annealing (dwave-samplers)", metadata)
    print(json.dumps(dict(makespan=official["makespan"], feasible_rate=report["feasible_rate"], output=str(args.output)), indent=2))


if __name__ == "__main__":
    main()
